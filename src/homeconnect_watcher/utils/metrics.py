from logging import getLogger
from time import monotonic
from typing import Callable


from homeconnect_watcher._version import __version__
from homeconnect_watcher.event import HomeConnectEvent


class Metrics:
    _event_types = (
        "ACTIVE-PROGRAM-REQUEST",
        "CONNECTED",
        "DEPAIRED",
        "DISCONNECTED",
        "EVENT",
        "NOTIFY",
        "PAIRED",
        "SELECTED-PROGRAM-REQUEST",
        "SETTINGS-REQUEST",
        "STATUS",
        "STATUS-REQUEST",
    )

    def __init__(self, port: int):
        self.logger = getLogger(self.__class__.__name__)
        try:
            from prometheus_client import Counter, Gauge, Info, start_http_server
        except ImportError:
            self.logger.error("Unable to expose prometheus metrics; prometheus_client is not installed.")
            self.logger.error(
                "Please run `pip install prometheus_client` or `pip install 'homeconnect-watcher[prometheus]'`."
            )
            return
        self._start_time = monotonic()
        self._disconnects = Counter("disconnects", "The number of time the connection failed.", ["reason"])
        self._disconnects.labels(reason="timeout")
        self._disconnects.labels(reason="closed")
        self._events = Counter("events", "Number of events.", ["appliance_id", "event"])
        self._events.labels(appliance_id=None, event="KEEP-ALIVE")
        self._info = Info("version", "Version info.")
        self._info.info({"version": __version__})
        self._last_event = Gauge("last_event", "Time since last event.")
        self._metric_uptime = Gauge("uptime", "Watcher uptime.")
        self._metric_uptime.set_function(lambda: monotonic() - self._start_time)
        self._n_appliances = Gauge("n_appliances", "The number of known appliances.")
        self._token_refresh = Counter("token_refresh", "The number of times the token was refreshed.")
        self.logger.info(f"Exposing prometheus metrics on port {port}.")
        start_http_server(port)

    def init_labels(self, appliance_id: str) -> None:
        for event_type in self._event_types:
            self._events.labels(appliance_id=appliance_id, event=event_type)

    def increment_disconnects(self, reason: str) -> None:
        self._disconnects.labels(reason=reason).inc()

    def increment_event_counter(self, event: HomeConnectEvent) -> None:
        self._events.labels(appliance_id=event.appliance_id, event=event.event).inc()

    def increment_token_refresh(self) -> None:
        self._token_refresh.inc()

    def set_last_event(self, function: Callable[[], float]) -> None:
        """
        Set the function for the last event metric.

        This should be a function that returns the time since the last event in seconds, e.g.
            lambda: monotonic() - last_event
        """
        self._last_event.set_function(function)

    def set_n_appliances(self, function: Callable[[], int]) -> None:
        """
        Set the function for the n_appliances metric.

        This should be a function that returns the number of appliances., e.g.
            lambda: len(appliances)
        """
        self._n_appliances.set_function(function)
