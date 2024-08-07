from asyncio import sleep
from json import load, dump
from logging import getLogger
from os import environ
from pathlib import Path
from re import search
from time import monotonic
from typing import AsyncIterable

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from requests import Session
from httpx import StreamError, ReadTimeout, RemoteProtocolError


from homeconnect_watcher.client.appliance import HomeConnectAppliance
from homeconnect_watcher.trigger import Trigger
from homeconnect_watcher.event import HomeConnectEvent
from homeconnect_watcher.exceptions import HomeConnectRequestError, HomeConnectConnectionClosed, HomeConnectTimeout
from homeconnect_watcher.utils import Metrics, retry, timeout


class HomeConnectClient:
    _authorize_endpoint = "https://api.home-connect.com/security/oauth/authorize"
    _appliances_endpoint = "https://api.home-connect.com/api/homeappliances"
    _token_endpoint = "https://api.home-connect.com/security/oauth/token"

    def __init__(self, token_cache: Path = Path("token"), metrics: Metrics | None = None):
        self.token_cache = (
            Path(environ["HOMECONNECT_PATH"]) / token_cache if "HOMECONNECT_PATH" in environ else token_cache
        )
        self.logger = getLogger(self.__class__.__name__)
        self.client = AsyncOAuth2Client(
            client_id=environ["HOMECONNECT_CLIENT_ID"],
            client_secret=environ["HOMECONNECT_CLIENT_SECRET"],
            redirect_uri=environ["HOMECONNECT_REDIRECT_URI"],
            update_token=self._save_token,
            token_endpoint=self._token_endpoint,
            token=self._load_token(),
        )
        self.client.auth = self.client.token_auth  # Ensure we use token auth for all requests.
        self._appliances: list["HomeConnectAppliance"] | None = None
        self._last_event: int | None = None
        self.metrics = metrics
        if self.metrics:
            self.metrics.set_last_event(lambda: monotonic() - self._last_event if self._last_event else -1)
            self.metrics.set_n_appliances(lambda: len(self._appliances) if self._appliances else 0)

    @property
    async def appliances(self) -> list["HomeConnectAppliance"]:
        if self._appliances is None:
            self._appliances = await self._get_appliances()
        return self._appliances

    async def get_appliance(self, appliance_id: str) -> "HomeConnectAppliance":
        for appliance in await self.appliances:
            if appliance.appliance_id == appliance_id:
                return appliance
        raise KeyError(f"No such appliance: {appliance_id}")

    async def refresh_appliances(self) -> None:
        """Refresh the cached list of appliances. Should only be needed if a new appliance is added."""
        self._appliances = None
        await self.appliances

    async def _get_appliances(self) -> list["HomeConnectAppliance"]:
        data = await self._get("")
        if "error" in data:
            raise HomeConnectRequestError(data["error"])
        return [
            HomeConnectAppliance(
                client=self,
                appliance_id=appliance["haId"],
                appliance_type=appliance["type"],
            )
            for appliance in data["data"]["homeappliances"]
        ]

    @property
    def authorization_url(self) -> str:
        url, state = self.client.create_authorization_url(self._authorize_endpoint)
        return url

    async def authorize(self, url: str) -> None:
        await self.client.fetch_token(self._token_endpoint, authorization_response=url)
        await self._save_token(self.client.token)

    async def watch(
        self, appliance_id: str | None = None, reconnect_delay: int = 120
    ) -> AsyncIterable[HomeConnectEvent]:
        """
        Watch the status of one or all appliances.

        Listens to the event stream and yield all events. In addition, processes triggers of these events
        to make requests for further details.

        Automatically reconnects when disconnected or on timeout.
        """
        async for event in self._initial_triggers(appliance_id=appliance_id):
            yield event
        while True:
            try:
                async for event in self._event_stream(appliance_id=appliance_id):
                    async for resulting_event in self._handle_event_and_triggers(event=event):
                        yield resulting_event
            except HomeConnectConnectionClosed:
                self.logger.warning(f"Connection closed. Reconnecting in {reconnect_delay} seconds.")
                if self.metrics:
                    self.metrics.increment_disconnects(reason="closed")
                await sleep(reconnect_delay)
                continue
            except HomeConnectTimeout:
                self.logger.warning(f"Connection timed out. Reconnecting in {reconnect_delay} seconds.")
                if self.metrics:
                    self.metrics.increment_disconnects(reason="timeout")
                await sleep(reconnect_delay)
                continue

    async def _event_stream(self, appliance_id: str | None = None) -> AsyncIterable[HomeConnectEvent]:
        """
        Connect to an event stream and yield the events.

        If appliance_id is provided, will watch only to events of the given appliance.
        Otherwise, will watch to the global event stream.

        Raises:
            HomeConnectConnectionClosed:
                when the connection can not be established or when there is a stream error.
            HomeConnectTimeout:
                when no events are received in 120 seconds.
        """
        url = (
            f"{self._appliances_endpoint}/events"
            if appliance_id is None
            else f"{self._appliances_endpoint}/{appliance_id}/events"
        )
        self.logger.info("Opening event stream.")
        async with self.client.stream("GET", url, timeout=None) as event_stream:
            if event_stream.status_code != 200:
                self.logger.warning(f"Failed to connect to events endpoint. Status code: {event_stream.status_code}")
                raise HomeConnectConnectionClosed()
            try:
                async for entry in timeout(event_stream.aiter_bytes(), duration=120):
                    if entry:
                        yield HomeConnectEvent.from_stream(entry)
                        self._last_event = monotonic()
            except (RemoteProtocolError, StreamError) as e:
                self.logger.warning("Stream error:", exc_info=e)
                raise HomeConnectConnectionClosed()
            except StopAsyncIteration:
                self.logger.info("Reached end of events stream.")
                return

    async def _handle_event_and_triggers(self, event: HomeConnectEvent) -> AsyncIterable[HomeConnectEvent]:
        """
        Handle triggers for an event and increase all corresponding counters.
        """
        if self.metrics:
            self.metrics.increment_event_counter(event=event)
        yield event
        async for triggered_event in self._handle_trigger(event.trigger):
            if self.metrics:
                self.metrics.increment_event_counter(triggered_event)
            yield triggered_event

    async def _initial_triggers(self, appliance_id: str | None) -> AsyncIterable[HomeConnectEvent]:
        """
        Create and handle initial triggers

        If appliance_id is not None, only create requests for the single appliance. Otherwise do so
        for all known appliances.
        """
        for appliance in await self.appliances:
            if appliance_id == appliance.appliance_id or appliance_id is None:
                async for triggered_event in self._handle_trigger(
                    Trigger(
                        appliance_id=appliance.appliance_id,
                        status=True,
                        settings=True,
                        active_program=True,
                        selected_program=True,
                    )
                ):
                    yield triggered_event
                    if self.metrics:
                        self.metrics.increment_event_counter(triggered_event)

    async def _handle_trigger(self, trigger: Trigger | None) -> AsyncIterable[HomeConnectEvent]:
        """
        Handle a trigger.
        """
        if trigger is None:
            return
        appliance = await self.get_appliance(trigger.appliance_id)
        if trigger.status:
            if not trigger.interval or appliance.time_since_update("status") >= 300:
                yield await appliance.get_status()
        if trigger.settings:
            if not trigger.interval or appliance.time_since_update("settings") >= 300:
                yield await appliance.get_settings()
        if await appliance.get_available_programs():  # Only if the appliance supports programs.
            if trigger.active_program:
                if not trigger.interval or appliance.time_since_update("active_program") >= 300:
                    yield await appliance.get_active_program()
            if trigger.selected_program:
                if not trigger.interval or appliance.time_since_update("selected_program") >= 300:
                    yield await appliance.get_selected_program()

    def _load_token(self) -> OAuth2Token | None:
        """Load the OAuth token from file."""
        if not self.token_cache.is_file():
            self.logger.warning("Token cache not found.")
            return
        with self.token_cache.open() as token_file:
            self.logger.info("Loading token from disk.")
            return OAuth2Token(load(token_file))

    async def _save_token(self, token: OAuth2Token, refresh_token=None) -> None:  # noqa
        """Save the OAuth token to the token cache."""
        if self.metrics:
            self.metrics.increment_token_refresh()
        with self.token_cache.open(mode="w") as token_file:
            self.logger.info("Saving token to disk.")
            dump(token, token_file)

    @retry(n_tries=3, exceptions=(ReadTimeout,))
    async def _get(self, path: str) -> dict[str, ...]:
        await sleep(delay=1.5)  # Rate limit
        resp = await self.client.get(f"{self._appliances_endpoint}{path}")
        data = resp.json()
        if len(data.keys()) > 1:
            raise KeyError(f"Unexpected keys: {data.keys()}")
        return data


class HomeConnectSimulationClient(HomeConnectClient):
    _authorize_endpoint = "https://simulator.home-connect.com/security/oauth/authorize"
    _appliances_endpoint = "https://simulator.home-connect.com/api/homeappliances"
    _token_endpoint = "https://simulator.home-connect.com/security/oauth/token"

    def __init__(self, token_cache: Path = Path("simulation_token"), metrics: Metrics | None = None):
        super().__init__(token_cache=token_cache, metrics=metrics)

    async def authenticate(self, username: str, password: str):
        """Automatic simulation login. Any username/password goes, except 'wrongPassword'."""
        session = Session()
        response = session.post(
            self.authorization_url.replace("authorize", "login"),
            data=dict(email=username, password=password),
        )
        grant_url = search('(/security/oauth/grant.*)" +method="post"', str(response.content))
        if grant_url is None:
            raise ValueError(response.content)
        response = session.post(
            "https://simulator.home-connect.com" + grant_url.group(1),
            data={
                "submit": "approve",
                "user": "email",
                "client_id": environ["HOMECONNECT_CLIENT_ID"],
                "scope": "CleaningRobot CleaningRobot-Control CleaningRobot-Monitor CleaningRobot-Settings CoffeeMaker "
                "CoffeeMaker-Control CoffeeMaker-Monitor CoffeeMaker-Settings Control CookProcessor "
                "CookProcessor-Control CookProcessor-Monitor CookProcessor-Settings Dishwasher "
                "Dishwasher-Control Dishwasher-Monitor Dishwasher-Settings Dryer Dryer-Control Dryer-Monitor "
                "Dryer-Settings Freezer Freezer-Control Freezer-Monitor Freezer-Settings "
                "FridgeFreezer-Control FridgeFreezer-Monitor FridgeFreezer-Settings Hob Hob-Control "
                "Hob-Monitor Hob-Settings Hood Hood-Control Hood-Monitor Hood-Settings IdentifyAppliance "
                "Monitor Oven Oven-Control Oven-Monitor Oven-Settings Refrigerator Refrigerator-Control "
                "Refrigerator-Monitor Refrigerator-Settings Settings Washer Washer-Control Washer-Monitor "
                "Washer-Settings WasherDryer WasherDryer-Control WasherDryer-Monitor WasherDryer-Settings "
                "WineCooler WineCooler-Control WineCooler-Monitor WineCooler-Settings",
                "redirect_uri": environ["HOMECONNECT_REDIRECT_URI"],
            },
            allow_redirects=False,
        )
        response = session.get(response.headers["Location"], allow_redirects=False)
        await self.authorize(url=response.headers["Location"])
