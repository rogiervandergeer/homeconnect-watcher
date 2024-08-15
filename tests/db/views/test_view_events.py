from datetime import datetime
from pytest import mark
from zoneinfo import ZoneInfo

from homeconnect_watcher.db import WatcherDBClient


@mark.events(
    """{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1703406303.1, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703406303.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}"""
)
def test_single_event(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 1
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2023, 12, 24, 9, 25, 3, 100000, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        None,
    )


@mark.events(
    """
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1703406303.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703406303.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "EVENT", "timestamp": 1703412414.0, "data": {"haId": "SIEMENS-EX877LVV5E-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703412414.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "EVENT", "timestamp": 1703412423.0, "data": {"haId": "SIEMENS-EX877LVV5E-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703412423.0, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
"""
)
def test_multiple_appliances(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 2
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2023, 12, 24, 9, 25, 3, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        None,
    )
    assert result[1] == (
        "SIEMENS-EX877LVV5E-AB1234567890",
        "ProgramFinished",
        datetime(2023, 12, 24, 11, 6, 54, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        datetime(2023, 12, 24, 11, 7, 3, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
    )


@mark.events(
    """
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707376385.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707376385.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707376691.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707376691.0, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "EVENT", "timestamp": 1707377425.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Event.DripTrayFull", "level": "alert", "timestamp": 1707377425.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "EVENT", "timestamp": 1707377768.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Event.DripTrayFull", "level": "alert", "timestamp": 1707377768.0, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707379832.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707379832.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707379944.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707379944.0, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707382275.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707382275.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
"""
)
def test_successive(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 4
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 8, 8, 13, 5, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        datetime(2024, 2, 8, 8, 18, 11, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
    )
    assert result[1] == (
        "SIEMENS-TI9553X1RW-AB1234567890",
        "DripTrayFull",
        datetime(2024, 2, 8, 8, 30, 25, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        datetime(2024, 2, 8, 8, 36, 8, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
    )
    assert result[2] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 8, 9, 10, 32, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        datetime(2024, 2, 8, 9, 12, 24, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
    )
    assert result[3] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 8, 9, 51, 15, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        None,
    )


@mark.events(
    """
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707466277.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707466277.0, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "DISCONNECTED", "timestamp": 1707490575.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "handling": "none", "key": "BSH.Common.Appliance.Disconnected", "level": "hint", "timestamp": 1707490575.0, "value": true}}
"""
)
def test_end_by_disconnect(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 1
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 9, 9, 11, 17, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
        datetime(2024, 2, 9, 15, 56, 15, tzinfo=ZoneInfo("Europe/Amsterdam")).astimezone(
            db_with_events.connection.info.timezone
        ),
    )
