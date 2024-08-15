from pytest import mark

from homeconnect_watcher.db import WatcherDBClient


@mark.events(
    """{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "NOTIFY", "timestamp": 1703264021.0, "data": {"haId": "SIEMENS-EX877LVV5E-AB1234567890", "items": [{"handling": "none", "key": "BSH.Common.Root.SelectedProgram", "level": "hint", "timestamp": 1703264019.0, "uri": "/api/homeappliances/SIEMENS-EX877LVV5E-AB1234567890/programs/selected", "value": "Cooking.Hob.Program.PowerLevelMode"}]}}"""
)
def test_hob(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_appliances")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 1
    assert result[0] == ("SIEMENS-EX877LVV5E-AB1234567890", "Hob")


@mark.events(
    """{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "NOTIFY", "timestamp": 1704095918.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "BSH.Common.Root.SelectedProgram", "level": "hint", "timestamp": 1704095918.0, "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/programs/selected", "value": null}]}}"""
)
def test_missing_program(db_with_events: WatcherDBClient):
    """Verify that notifications where no program is selected do not show up."""
    db_with_events.cursor.execute("SELECT * FROM v_appliances")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 0


@mark.events(
    """
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "NOTIFY", "timestamp": 1704095918.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "BSH.Common.Root.SelectedProgram", "level": "hint", "timestamp": 1704095918.0, "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/programs/selected", "value": null}]}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "NOTIFY", "timestamp": 1708587519.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "BSH.Common.Root.SelectedProgram", "level": "hint", "timestamp": 1708587519.0, "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/programs/selected", "value": "ConsumerProducts.CoffeeMaker.Program.Beverage.Coffee"}, {"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Option.BeanAmount", "level": "hint", "timestamp": 1708587519.0, "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/programs/selected/options/ConsumerProducts.CoffeeMaker.Option.BeanAmount", "value": "ConsumerProducts.CoffeeMaker.EnumType.BeanAmount.Strong"}, {"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Option.FillQuantity", "level": "hint", "timestamp": 1708587519.0, "unit": "ml", "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/programs/selected/options/ConsumerProducts.CoffeeMaker.Option.FillQuantity", "value": 140}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "NOTIFY", "timestamp": 1707925134.0, "data": {"haId": "SIEMENS-WM14T6H9NL-AB1234567890", "items": [{"handling": "none", "key": "LaundryCare.Common.Option.VarioPerfect", "level": "hint", "timestamp": 1707925131.0, "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/LaundryCare.Common.Option.VarioPerfect", "value": "LaundryCare.Common.EnumType.VarioPerfect.Off"}, {"handling": "none", "key": "LaundryCare.Washer.Option.SpinSpeed", "level": "hint", "timestamp": 1707925131.0, "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/LaundryCare.Washer.Option.SpinSpeed", "value": "LaundryCare.Washer.EnumType.SpinSpeed.RPM1200"}, {"handling": "none", "key": "LaundryCare.Washer.Option.Temperature", "level": "hint", "timestamp": 1707925131.0, "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/LaundryCare.Washer.Option.Temperature", "value": "LaundryCare.Washer.EnumType.Temperature.GC40"}, {"handling": "none", "key": "BSH.Common.Root.SelectedProgram", "level": "hint", "timestamp": 1707925131.0, "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected", "value": "LaundryCare.Washer.Program.DelicatesSilk"}]}}
"""
)
def test_multiple(db_with_events: WatcherDBClient):
    db_with_events.cursor.execute("SELECT * FROM v_appliances")
    result = db_with_events.cursor.fetchall()
    assert len(result) == 2
