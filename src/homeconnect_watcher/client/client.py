from asyncio import sleep
from json import load, dump
from logging import getLogger
from os import environ
from pathlib import Path
from re import search
from typing import AsyncIterable

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from requests import Session
from httpx import StreamError, RemoteProtocolError


from homeconnect_watcher.client.appliance import HomeConnectAppliance
from homeconnect_watcher.client.trigger import Trigger
from homeconnect_watcher.event import HomeConnectEvent
from homeconnect_watcher.exceptions import HomeConnectRequestError, HomeConnectConnectionClosed, HomeConnectTimeout
from homeconnect_watcher.utils.timeout import timeout


class HomeConnectClient:
    _authorize_endpoint = "https://api.home-connect.com/security/oauth/authorize"
    _appliances_endpoint = "https://api.home-connect.com/api/homeappliances"
    _token_endpoint = "https://api.home-connect.com/security/oauth/token"

    def __init__(
        self,
        token_cache: Path = Path("token"),
    ):
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
        self.last_event: int | None = None

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

    async def events(self, appliance_id: str | None = None) -> AsyncIterable[HomeConnectEvent]:
        """
        Connect to an event stream.

        If appliance_id is provided, will watch only to events of the given appliance.
        Otherwise, will watch to the global event stream.
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
            except (RemoteProtocolError, StreamError) as e:
                self.logger.warning("Stream error:", exc_info=e)
                raise HomeConnectConnectionClosed()
            except StopAsyncIteration:
                self.logger.info("Reached end of events stream.")
                return

    async def watch(
        self, appliance_id: str | None = None, reconnect_delay: int = 120
    ) -> AsyncIterable[HomeConnectEvent]:
        """
        Watch the status of one or all appliances.

        Listen to the event stream and yield all events.
        """
        for appliance in await self.appliances:
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
        while True:
            try:
                async for event in self.events(appliance_id=appliance_id):
                    yield event
                    async for triggered_event in self._handle_trigger(event.trigger):
                        yield triggered_event
            except HomeConnectConnectionClosed:
                self.logger.warning(f"Connection closed. Reconnecting in {reconnect_delay} seconds.")
                await sleep(reconnect_delay)
                continue
            except HomeConnectTimeout:
                self.logger.warning(f"Connection timed out. Reconnecting in {reconnect_delay} seconds.")
                await sleep(reconnect_delay)
                continue

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
        with self.token_cache.open(mode="w") as token_file:
            self.logger.info("Saving token to disk.")
            dump(token, token_file)

    async def _get(self, path: str) -> dict[str, ...]:
        await sleep(delay=1.5)  # Rate limit
        resp = await self.client.get(f"{self._appliances_endpoint}{path}")
        data = resp.json()
        if len(data.keys()) > 1:
            raise KeyError(f"Unexpected keys: {data.keys()}")
        return data

    async def _handle_trigger(self, trigger: Trigger | None) -> AsyncIterable[HomeConnectEvent]:
        if trigger is None:
            return
        appliance = await self.get_appliance(trigger.appliance_id)
        if trigger.interval and appliance.time_since_update < 300:
            return  # If the trigger is an interval trigger, only do requests if last requests were 5 minutes ago.
        if trigger.status:
            yield await appliance.get_status()
        if trigger.settings:
            yield await appliance.get_settings()
        if await appliance.get_available_programs():  # Only if the appliance supports programs.
            if trigger.active_program:
                yield await appliance.get_active_program()
            if trigger.selected_program:
                yield await appliance.get_selected_program()


class HomeConnectSimulationClient(HomeConnectClient):
    _authorize_endpoint = "https://simulator.home-connect.com/security/oauth/authorize"
    _appliances_endpoint = "https://simulator.home-connect.com/api/homeappliances"
    _token_endpoint = "https://simulator.home-connect.com/security/oauth/token"

    def __init__(
        self,
        token_cache: Path = Path("simulation_token"),
    ):
        super().__init__(token_cache=token_cache)

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
