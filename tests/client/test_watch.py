from asyncio import CancelledError, Event, sleep
from time import time
from unittest.mock import Mock

from pytest import fixture, mark, raises

from homeconnect_watcher.client import HomeConnectClient
from homeconnect_watcher.client.appliance import HomeConnectAppliance
from homeconnect_watcher.event import HomeConnectEvent


@fixture
def client(tmp_path, monkeypatch) -> HomeConnectClient:
    """A bare client for exercising watch(); every network path is patched in the tests.

    Overrides the session-scoped `client` fixture from conftest so these tests need no
    credentials or simulator connection.
    """
    monkeypatch.setenv("HOMECONNECT_CLIENT_ID", "id")
    monkeypatch.setenv("HOMECONNECT_CLIENT_SECRET", "secret")
    monkeypatch.setenv("HOMECONNECT_REDIRECT_URI", "http://localhost:8000/code/")
    return HomeConnectClient(token_cache=tmp_path / "token")


class TestWatchResilience:
    @mark.asyncio
    async def test_unexpected_error_reconnects(self, client: HomeConnectClient, monkeypatch):
        """An unexpected error in the producer is logged, counted, and recovered from."""
        keep_alive = HomeConnectEvent(event="KEEP-ALIVE", timestamp=0.0)
        state = {"raised": False}

        async def fake_event_stream(appliance_id=None):
            if not state["raised"]:
                state["raised"] = True
                raise ValueError("boom")
            yield keep_alive
            await Event().wait()  # suspend so the loop can run the consumer; keep the stream "open"

        async def noop_initial(queue, appliance_id):
            return

        async def noop_handle(trigger, queue):
            return

        metrics = Mock()
        monkeypatch.setattr(client, "metrics", metrics)
        monkeypatch.setattr(client, "_initial_triggers", noop_initial)
        monkeypatch.setattr(client, "_event_stream", fake_event_stream)
        monkeypatch.setattr(client, "_handle_trigger", noop_handle)

        gen = client.watch(reconnect_delay=0)
        try:
            received = await gen.__anext__()
        finally:
            await gen.aclose()

        # The producer survived the ValueError, reconnected, and delivered the next event.
        assert received == keep_alive
        assert state["raised"] is True
        metrics.increment_disconnects.assert_any_call(reason="error")


class TestWatchTaskCleanup:
    @mark.asyncio
    async def test_deferred_tasks_cancelled_on_close(self, client: HomeConnectClient, monkeypatch):
        """Pending deferred fetches are cancelled (and untracked) when watching stops."""
        appliance = HomeConnectAppliance(client, "SIEMENS-TEST-AB1234567890", "Washer")
        appliance._last_update["status"] = time()  # throttle active -> the fetch is deferred, not run
        scheduled = Event()

        async def never_fetch():  # pragma: no cover - deferred task is cancelled before this runs
            return HomeConnectEvent(event="STATUS-REQUEST", timestamp=0.0)

        async def fake_handle_trigger(trigger, queue):
            await client._fetch_or_defer(appliance, "status", never_fetch, throttled=True, queue=queue)
            scheduled.set()

        async def fake_event_stream(appliance_id=None):
            yield HomeConnectEvent(event="KEEP-ALIVE", timestamp=0.0)
            await Event().wait()  # keep the stream open so the deferred task stays pending

        async def noop_initial(queue, appliance_id):
            return

        monkeypatch.setattr(client, "_initial_triggers", noop_initial)
        monkeypatch.setattr(client, "_event_stream", fake_event_stream)
        monkeypatch.setattr(client, "_handle_trigger", fake_handle_trigger)

        before = set(client._deferred_tasks)
        gen = client.watch(reconnect_delay=0)
        await gen.__anext__()  # receive the KEEP-ALIVE event
        await scheduled.wait()  # ensure the deferred fetch has been scheduled

        new_tasks = client._deferred_tasks - before
        assert len(new_tasks) == 1
        task = new_tasks.pop()
        assert not task.done()

        await gen.aclose()  # runs watch()'s finally: cancels the producer and deferred tasks

        with raises(CancelledError):
            await task
        await sleep(0)  # let the done-callback drain the task from the set
        assert task.cancelled()
        assert task not in client._deferred_tasks
