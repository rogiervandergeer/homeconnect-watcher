from json import dumps
from datetime import datetime, timedelta
from psycopg import Connection, Cursor, connect
from psycopg.errors import UndefinedTable

from homeconnect_watcher.event import HomeConnectEvent
from homeconnect_watcher.exporter import BaseExporter


class PGExporter(BaseExporter):
    def __init__(self, connection_string: str, refresh_interval: timedelta = timedelta(hours=24)):
        super().__init__()
        self.connection_string = connection_string
        self.connection: Connection | None = None
        self.cursor: Cursor | None = None
        self.refresh_interval = refresh_interval
        self._next_refresh: datetime = datetime.now() + self.refresh_interval

    def __enter__(self) -> "PGExporter":
        self.logger.info("Opening database connection.")
        self.connection = connect(self.connection_string, autocommit=True)
        self.cursor = self.connection.cursor()
        self._create_table()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cursor.close()
        self.cursor = None
        self.connection.close()
        self.connection = None
        self.logger.info("Database connection closed.")
        return

    def export(self, event: HomeConnectEvent) -> None:
        self.cursor.execute(
            "INSERT INTO events(appliance_id, event, timestamp, data) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (event.appliance_id, event.event, event.datetime, dumps(event.items)),
        )
        if datetime.now() > self._next_refresh:
            self._refresh_view()

    def bulk_export(self, events: list[HomeConnectEvent]) -> None:
        data = [(event.appliance_id, event.event, event.datetime, dumps(event.items)) for event in events]
        self.cursor.executemany(
            "INSERT INTO events(appliance_id, event, timestamp, data) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            data,
        )

    def _create_table(self) -> None:
        self.cursor.execute(
            """
CREATE TABLE IF NOT EXISTS events (
    appliance_id char(31),
    event varchar(31) NOT NULL,
    timestamp timestamp NOT NULL,
    data jsonb NOT NULL,
    PRIMARY KEY (appliance_id, event, timestamp)
);
"""
        )

    def _refresh_view(self) -> None:
        try:
            self.cursor.execute(f"REFRESH MATERIALIZED VIEW sessions;")
            self.logger.info("Successfully refreshed the sessions view.")
        except UndefinedTable:
            self.logger.error("Failed to refresh the sessions view.")
        self._next_refresh: datetime = datetime.now() + self.refresh_interval
