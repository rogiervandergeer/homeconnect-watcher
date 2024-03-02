from homeconnect_watcher.db import WatcherDBClient
from homeconnect_watcher.event import HomeConnectEvent


class TestDBClient:
    def test_event_count(self, db_client: WatcherDBClient) -> None:
        assert db_client.event_count == 0
        db_client.write_events([HomeConnectEvent(timestamp=1674291950, event="KEEP-ALIVE")])
        assert db_client.event_count == 1

    def test_create_views_when_exist(self, db_client: WatcherDBClient):
        db_client.create_views()  # This should not cause any problems

    def test_drop_views(self, db_client: WatcherDBClient):
        db_client.drop_views()

    def test_refresh_views(self, db_client: WatcherDBClient):
        db_client.refresh_views()
