from homeconnect_watcher.db import load_views


def test_load_views():
    views = load_views()
    assert len(views) > 0
    assert list(views.keys())[0] == "active_events"
