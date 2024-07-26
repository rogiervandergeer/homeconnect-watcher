from datetime import datetime
from pytest import mark

from homeconnect_watcher.db import WatcherDBClient


@mark.events(
    """{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1703406303, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703406303, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}"""
)
def test_single_event(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 1
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2023, 12, 24, 9, 25, 3).astimezone().astimezone(db_with_events.connection.info.timezone),
        None,
    )


@mark.events(
    """
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1703406303, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703406303, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "EVENT", "timestamp": 1703412414, "data": {"haId": "SIEMENS-EX877LVV5E-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703412414, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "EVENT", "timestamp": 1703412423, "data": {"haId": "SIEMENS-EX877LVV5E-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1703412423, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
"""
)
def test_multiple_appliances(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 2
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2023, 12, 24, 9, 25, 3).astimezone().astimezone(db_with_events.connection.info.timezone),
        None,
    )
    assert result[1] == (
        "SIEMENS-EX877LVV5E-AB1234567890",
        "ProgramFinished",
        datetime(2023, 12, 24, 11, 6, 54).astimezone().astimezone(db_with_events.connection.info.timezone),
        datetime(2023, 12, 24, 11, 7, 3).astimezone().astimezone(db_with_events.connection.info.timezone),
    )


@mark.events(
    """
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707376385, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707376385, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707376691, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707376691, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "EVENT", "timestamp": 1707377425, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Event.DripTrayFull", "level": "alert", "timestamp": 1707377425, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "EVENT", "timestamp": 1707377768, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Event.DripTrayFull", "level": "alert", "timestamp": 1707377768, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707379832, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707379832, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707379944, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707379944, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707382275, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707382275, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
"""
)
def test_successive(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 4
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 8, 8, 13, 5).astimezone().astimezone(db_with_events.connection.info.timezone),
        datetime(2024, 2, 8, 8, 18, 11).astimezone().astimezone(db_with_events.connection.info.timezone),
    )
    assert result[1] == (
        "SIEMENS-TI9553X1RW-AB1234567890",
        "DripTrayFull",
        datetime(2024, 2, 8, 8, 30, 25).astimezone().astimezone(db_with_events.connection.info.timezone),
        datetime(2024, 2, 8, 8, 36, 8).astimezone().astimezone(db_with_events.connection.info.timezone),
    )
    assert result[2] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 8, 9, 10, 32).astimezone().astimezone(db_with_events.connection.info.timezone),
        datetime(2024, 2, 8, 9, 12, 24).astimezone().astimezone(db_with_events.connection.info.timezone),
    )
    assert result[3] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 8, 9, 51, 15).astimezone().astimezone(db_with_events.connection.info.timezone),
        None,
    )


@mark.events(
    """
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "EVENT", "timestamp": 1707466277, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "acknowledge", "key": "BSH.Common.Event.ProgramFinished", "level": "hint", "timestamp": 1707466277, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "DISCONNECTED", "timestamp": 1707490575, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "handling": "none", "key": "BSH.Common.Appliance.Disconnected", "level": "hint", "timestamp": 1707490575, "value": true}}
"""
)
def test_end_by_disconnect(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_events")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 1
    assert result[0] == (
        "SIEMENS-WM14T6H9NL-AB1234567890",
        "ProgramFinished",
        datetime(2024, 2, 9, 9, 11, 17).astimezone().astimezone(db_with_events.connection.info.timezone),
        datetime(2024, 2, 9, 15, 56, 15).astimezone().astimezone(db_with_events.connection.info.timezone),
    )
