from asyncio import Queue, Task, create_task, sleep
from collections.abc import Callable, Coroutine
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
        # Outstanding deferred-fetch tasks, tracked so they are cancelled when watching stops.
        self._deferred_tasks: set[Task] = set()
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

        Listens to the event stream and yields all events. In addition, processes
        triggers of these events to make requests for further details. Throttled
        requests that can't fire immediately are deferred — a single fetch is
        scheduled for when the throttle expires, and any further triggers within
        that window collapse onto the same pending fetch.

        Both stream events and deferred-fetch results land on a shared queue and
        are yielded in arrival order. Automatically reconnects when disconnected
        or on timeout.
        """
        queue: Queue[HomeConnectEvent] = Queue()
        producer = create_task(self._producer(queue=queue, appliance_id=appliance_id, reconnect_delay=reconnect_delay))
        try:
            while True:
                event = await queue.get()
                if self.metrics:
                    self.metrics.increment_event_counter(event=event)
                yield event
        finally:
            producer.cancel()
            for task in list(self._deferred_tasks):
                task.cancel()

    async def _producer(self, queue: "Queue[HomeConnectEvent]", appliance_id: str | None, reconnect_delay: int) -> None:
        """Drive the SSE stream and dispatch triggers onto the shared queue."""
        try:
            await self._initial_triggers(queue=queue, appliance_id=appliance_id)
        except Exception as e:
            # Best-effort enrichment: a failure here must not kill the producer.
            self.logger.warning("Error while handling initial triggers.", exc_info=e)
        while True:
            try:
                async for event in self._event_stream(appliance_id=appliance_id):
                    await queue.put(event)
                    await self._handle_trigger(event.trigger, queue=queue)
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
            except Exception as e:
                # Catch Exception (not BaseException) so CancelledError from watch()'s
                # shutdown still stops the producer instead of being swallowed here.
                self.logger.warning(f"Unexpected error. Reconnecting in {reconnect_delay} seconds.", exc_info=e)
                if self.metrics:
                    self.metrics.increment_disconnects(reason="error")
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

    async def _initial_triggers(self, queue: "Queue[HomeConnectEvent]", appliance_id: str | None) -> None:
        """
        Create and handle initial triggers.

        If appliance_id is not None, only create requests for the single appliance.
        Otherwise do so for all known appliances. Results are pushed onto `queue`.
        """
        for appliance in await self.appliances:
            if appliance_id == appliance.appliance_id or appliance_id is None:
                await self._handle_trigger(
                    Trigger(
                        appliance_id=appliance.appliance_id,
                        status=True,
                        settings=True,
                        active_program=True,
                        selected_program=True,
                    ),
                    queue=queue,
                )

    async def _handle_trigger(self, trigger: Trigger | None, queue: "Queue[HomeConnectEvent]") -> None:
        """
        Handle a trigger by firing or deferring the requested fetches.

        Each fetch either runs immediately (when the throttle has elapsed or
        `trigger.interval` is False) or is scheduled to run when the throttle
        next expires. Repeated triggers landing during the deferral window
        collapse onto the single pending task. Results land on `queue`.
        """
        if trigger is None:
            return
        appliance = await self.get_appliance(trigger.appliance_id)
        fetches: list[tuple[str, bool, Callable[[], Coroutine]]] = [
            ("status", trigger.status, appliance.get_status),
            ("settings", trigger.settings, appliance.get_settings),
        ]
        # active/selected program endpoints only exist for appliances that support programs.
        if (trigger.active_program or trigger.selected_program) and await appliance.get_available_programs():
            fetches += [
                ("active_program", trigger.active_program, appliance.get_active_program),
                ("selected_program", trigger.selected_program, appliance.get_selected_program),
            ]
        for kind, wanted, fetch in fetches:
            if wanted:
                await self._fetch_or_defer(appliance, kind, fetch, throttled=trigger.interval, queue=queue)

    async def _fetch_or_defer(
        self,
        appliance: "HomeConnectAppliance",
        kind: str,
        fetch: Callable[[], Coroutine],
        throttled: bool,
        queue: "Queue[HomeConnectEvent]",
    ) -> None:
        """
        Fetch immediately if the throttle has elapsed; otherwise schedule a
        deferred fetch for when it expires. The pending-task set on the
        appliance deduplicates concurrent triggers for the same request type.
        """
        if not throttled or appliance.time_since_update(kind) >= 300:
            await queue.put(await fetch())
            return
        if kind in appliance._pending:
            return
        appliance._pending.add(kind)

        async def deferred() -> None:
            try:
                wait = 300 - appliance.time_since_update(kind)
                if wait > 0:
                    await sleep(wait)
                await queue.put(await fetch())
            finally:
                appliance._pending.discard(kind)

        task = create_task(deferred())
        self._deferred_tasks.add(task)
        task.add_done_callback(self._deferred_tasks.discard)

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
