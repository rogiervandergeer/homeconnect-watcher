from homeconnect_watcher.db.view import load_view, load_views


def test_view_names():
    views = load_views()
    for view in views:
        assert len(view.name) > 0


def test_materialized():
    assert not load_view("v_appliances").materialized
    assert load_view("v_sessions").materialized
