from json import dumps
from logging import getLogger

from psycopg import Connection, Cursor, connect, sql

from ..event import HomeConnectEvent
from .view import load_views

logger = getLogger(__name__)


class WatcherDBClient:
    # Set in __enter__; only valid inside the context.
    connection: Connection
    cursor: Cursor

    def __init__(self, connection_string: str, init: bool = True):
        self.connection_string = connection_string
        self.init = init

    def __enter__(self) -> "WatcherDBClient":
        logger.info("Opening database connection.")
        self.connection = connect(self.connection_string, autocommit=True)
        self.cursor = self.connection.cursor()
        if self.init:
            self.create_table()
            self.create_views()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cursor.close()
        del self.cursor
        self.connection.close()
        del self.connection
        logger.info("Database connection closed.")
        return

    @property
    def event_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) AS cnt FROM events")
        result = self.cursor.fetchone()
        assert result is not None  # COUNT(*) always returns a row.
        return result[0]

    def create_table(self) -> None:
        """Create the event table."""
        self.cursor.execute(
            """
CREATE TABLE IF NOT EXISTS events (
    appliance_id char(31),
    event varchar(31) NOT NULL,
    timestamp timestamp with time zone NOT NULL,
    data jsonb NOT NULL,
    PRIMARY KEY (appliance_id, event, timestamp)
);
"""
        )

    def create_views(self) -> None:
        logger.info("Creating events table.")
        with self.connection.transaction():
            for view in load_views():
                self.connection.execute(view.query)  # ty: ignore[no-matching-overload]  # trusted packaged SQL

    def drop_views(self) -> None:
        logger.info("Dropping views.")
        with self.connection.transaction():
            for view in reversed(load_views()):
                self.connection.execute(view.drop_query)  # ty: ignore[no-matching-overload]  # trusted packaged SQL

    def refresh_views(self) -> None:
        logger.info("Creating views.")
        with self.connection.transaction():
            for view in load_views():
                if view.materialized:
                    self.connection.execute(sql.SQL("REFRESH MATERIALIZED VIEW {};").format(sql.Identifier(view.name)))

    def write_events(self, events: list[HomeConnectEvent]) -> None:
        data = [(event.appliance_id or "", event.event, event.datetime, dumps(event.items)) for event in events]
        self.cursor.executemany(
            "INSERT INTO events(appliance_id, event, timestamp, data) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            data,
        )
