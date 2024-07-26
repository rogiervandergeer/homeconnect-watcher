from datetime import datetime, timedelta

from homeconnect_watcher.event import HomeConnectEvent
from homeconnect_watcher.exporter import BaseExporter
from homeconnect_watcher.db import WatcherDBClient


class PGExporter(BaseExporter, WatcherDBClient):
    def __init__(self, connection_string: str, refresh_interval: timedelta = timedelta(hours=6)):
        WatcherDBClient.__init__(self, connection_string=connection_string)
        BaseExporter.__init__(self)
        self.refresh_interval = refresh_interval
        self._next_refresh: datetime = datetime.now() + self.refresh_interval

    def __enter__(self) -> "PGExporter":
        WatcherDBClient.__enter__(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        WatcherDBClient.__exit__(self, exc_type, exc_val, exc_tb)

    def export(self, event: HomeConnectEvent) -> None:
        self.write_events([event])
        if datetime.now() > self._next_refresh:
            self.refresh_views()
            self._next_refresh: datetime = datetime.now() + self.refresh_interval

    def bulk_export(self, events: list[HomeConnectEvent]) -> None:
        self.write_events(events)
        if datetime.now() > self._next_refresh:
            self.refresh_views()
            self._next_refresh: datetime = datetime.now() + self.refresh_interval
