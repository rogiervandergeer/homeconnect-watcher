from pytest import mark, skip

from homeconnect_watcher.client import HomeConnectAppliance
from homeconnect_watcher.trigger import Trigger
from homeconnect_watcher.event import HomeConnectEvent


class TestFromStream:
    def test_keep_alive(self, stream_event: bytes):
        if b"KEEP-ALIVE" not in stream_event:
            skip()
        event = HomeConnectEvent.from_stream(stream_event)
        assert event.event == "KEEP-ALIVE"
        assert event.data is None
        assert event.appliance_id is None
        assert event.timestamp is not None

    def test_status(self, stream_event: bytes):
        if b"STATUS" not in stream_event:
            skip()
        event = HomeConnectEvent.from_stream(stream_event)
        assert event.event == "STATUS"
        assert event.data is not None
        assert event.appliance_id == event.data["haId"]
        assert event.timestamp is not None

    def test_event(self, stream_event: bytes):
        if b"EVENT" not in stream_event:
            skip()
        event = HomeConnectEvent.from_stream(stream_event)
        assert event.event == "EVENT"
        assert event.data is not None
        assert event.appliance_id == event.data["haId"]
        assert event.timestamp is not None

    def test_notify(self, stream_event: bytes):
        if b"NOTIFY" not in stream_event:
            skip()
        event = HomeConnectEvent.from_stream(stream_event)
        assert event.event == "NOTIFY"
        assert event.data is not None
        assert event.appliance_id == event.data["haId"]
        assert event.timestamp is not None

    def test_connected(self, stream_event: bytes):
        if b"event:CONNECTED" not in stream_event:
            skip()
        event = HomeConnectEvent.from_stream(stream_event)
        assert event.event == "CONNECTED"
        assert event.data is not None
        assert event.appliance_id == event.data["haId"]
        assert event.timestamp is not None

    def test_disconnected(self, stream_event: bytes):
        if b"DISCONNECTED" not in stream_event:
            skip()
        event = HomeConnectEvent.from_stream(stream_event)
        assert event.event == "DISCONNECTED"
        assert event.data is not None
        assert event.appliance_id == event.data["haId"]
        assert event.timestamp is not None


class TestRequest:
    @mark.asyncio
    async def test_status(self, appliance: HomeConnectAppliance):
        event = await appliance.get_status()
        assert event.event == "STATUS-REQUEST"
        assert event.is_request
        assert event.timestamp is not None
        assert "status" in event.data

    @mark.asyncio
    async def test_settings(self, appliance: HomeConnectAppliance):
        event = await appliance.get_settings()
        assert event.event == "SETTINGS-REQUEST"
        assert event.is_request
        assert event.timestamp is not None
        assert "settings" in event.data

    @mark.asyncio
    async def test_active_program(self, appliance: HomeConnectAppliance):
        # By default, the simulator appliances are inactive.
        event = await appliance.get_active_program()
        assert event.error["key"] == "SDK.Error.NoProgramActive"
        assert event.items["BSH.Common.Root.ActiveProgram"] is None

    @mark.asyncio
    async def test_selected_program(self, appliance: HomeConnectAppliance):
        event = await appliance.get_selected_program()
        assert event.event == "SELECTED-PROGRAM-REQUEST"
        assert event.is_request
        assert event.timestamp is not None
        assert "key" in event.data


class TestEvent:
    def test_items(self, event: HomeConnectEvent) -> None:
        items = event.items
        assert isinstance(items, dict)

    def test_trigger(self, event: HomeConnectEvent) -> None:
        trigger = event.trigger
        if trigger is None:
            assert event.event in ("DISCONNECTED", "STATUS", "KEEP-ALIVE") or event.is_request
        else:
            assert isinstance(trigger, Trigger)
