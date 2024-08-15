from pytest import fixture

from homeconnect_watcher.event import HomeConnectEvent
from homeconnect_watcher.exporter.postgres import PGExporter


class TestPGExporter:
    @fixture(scope="function")
    def exporter(self, postgresql):
        return PGExporter(
            connection_string=f"postgresql://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
        )

    @fixture(scope="class")
    def event(self) -> HomeConnectEvent:
        return HomeConnectEvent(
            appliance_id="SIEMENS-EX877LVV5E-AB1234567890",
            event="STATUS-REQUEST",
            timestamp=1641970292.0,
            data={
                "status": [
                    {"key": "BSH.Common.Status.LocalControlActive", "value": False},
                    {"key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Inactive"},
                    {"key": "BSH.Common.Status.RemoteControlActive", "value": True},
                ]
            },
        )

    def test_event_written(self, exporter: PGExporter, event: HomeConnectEvent):
        with exporter:
            exporter.export(event)
        with exporter:
            exporter.cursor.execute("SELECT COUNT(*) FROM events")
            assert exporter.cursor.fetchone() == (1,)

    def test_no_duplicates(self, exporter: PGExporter, event: HomeConnectEvent):
        with exporter:
            exporter.export(event)
        with exporter:
            exporter.export(event)
        with exporter:
            exporter.cursor.execute("SELECT COUNT(*) FROM events")
            assert exporter.cursor.fetchone() == (1,)
