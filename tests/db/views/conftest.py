from pytest import fixture

from homeconnect_watcher.db import WatcherDBClient
from homeconnect_watcher.event import HomeConnectEvent


@fixture
def db_with_events(db_client: WatcherDBClient, request) -> WatcherDBClient:
    marker = request.node.get_closest_marker("events")
    if marker is not None:
        db_client.write_events(
            [HomeConnectEvent.from_string(line) for line in marker.args[0].split("\n") if len(line) > 0]
        )
        db_client.refresh_views()
    return db_client
