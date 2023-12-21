from asyncio import get_event_loop
from pathlib import Path
from typing import Any
from random import choices
from os import environ

from dotenv import load_dotenv

from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from homeconnect_watcher.client import HomeConnectClient, HomeConnectAppliance
from homeconnect_watcher.client.client import HomeConnectSimulationClient
from homeconnect_watcher.event import HomeConnectEvent, load_events


JSON_EVENTS = """
{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "CONNECTED", "timestamp": 1642002327}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "CONNECTED", "timestamp": 1678262667, "data": {"haId": "SIEMENS-EX877LVV5E-AB1234567890", "handling": "none", "key": "BSH.Common.Appliance.Connected", "level": "hint", "timestamp": 1678262667, "value": true}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "DISCONNECTED", "timestamp": 1642624669}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "DISCONNECTED", "timestamp": 1678102231, "data": {"haId": "SIEMENS-EX877LVV5E-AB1234567890", "handling": "none", "key": "BSH.Common.Appliance.Disconnected", "level": "hint", "timestamp": 1678102231, "value": true}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "EVENT", "timestamp": 1674894932, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Event.DripTrayFull", "level": "alert", "timestamp": 1674894932, "value": "BSH.Common.EnumType.EventPresentState.Present"}]}}
{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "EVENT", "timestamp": 1642859104, "data": {"items": [{"timestamp": 1642859104, "handling": "acknowledge", "key": "LaundryCare.Dryer.Event.DryingProcessFinished", "value": "BSH.Common.EnumType.EventPresentState.Present", "level": "hint"}], "haId": "SIEMENS-WT8HXM90NL-AB1234567890"}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "NOTIFY", "timestamp": 1642000702, "data": {"items": [{"timestamp": 1642000702, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/active/options/BSH.Common.Option.RemainingProgramTime", "key": "BSH.Common.Option.RemainingProgramTime", "unit": "seconds", "value": 540, "level": "hint"}], "haId": "SIEMENS-WM14T6H9NL-AB1234567890"}}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "NOTIFY", "timestamp": 1642090628, "data": {"items": [{"timestamp": 1642090627, "handling": "none", "uri": "/api/homeappliances/SIEMENS-EX877LVV5E-AB1234567890/programs/active", "key": "BSH.Common.Root.ActiveProgram", "value": "Cooking.Hob.Program.PowerLevelMode", "level": "hint"}], "haId": "SIEMENS-EX877LVV5E-AB1234567890"}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "NOTIFY", "timestamp": 1674156563, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "BSH.Common.Option.ProgramProgress", "level": "hint", "timestamp": 1674156560, "unit": "%", "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/programs/active/options/BSH.Common.Option.ProgramProgress", "value": 24}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "STATUS", "timestamp": 1642002216, "data": {"items": [{"timestamp": 1642002216, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.OperationState", "key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Ready", "level": "hint"}, {"timestamp": 1642002216, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.DoorState", "key": "BSH.Common.Status.DoorState", "value": "BSH.Common.EnumType.DoorState.Open", "level": "hint"}, {"timestamp": 1642002216, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.LocalControlActive", "key": "BSH.Common.Status.LocalControlActive", "value": true, "level": "hint"}, {"timestamp": 1642002216, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.RemoteControlActive", "key": "BSH.Common.Status.RemoteControlActive", "value": false, "level": "hint"}], "haId": "SIEMENS-WM14T6H9NL-AB1234567890"}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "STATUS", "timestamp": 1674156953, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "BSH.Common.Status.OperationState", "level": "hint", "timestamp": 1674156953, "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/status/BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Inactive"}]}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "ACTIVE-PROGRAM-REQUEST", "timestamp": 1677677195, "data": {"key": "LaundryCare.Washer.Program.DelicatesSilk", "options": [{"key": "LaundryCare.Common.Option.LoadRecommendation", "value": 2000, "unit": "gram"}, {"key": "LaundryCare.Common.Option.VarioPerfect", "value": "LaundryCare.Common.EnumType.VarioPerfect.Off"}, {"key": "LaundryCare.Washer.Option.IDos1DosingLevel", "value": "LaundryCare.Washer.EnumType.IDosingLevel.Light"}, {"key": "LaundryCare.Washer.Option.IDos2DosingLevel", "value": "LaundryCare.Washer.EnumType.IDosingLevel.Light"}, {"key": "LaundryCare.Washer.Option.LessIroning", "value": false}, {"key": "LaundryCare.Washer.Option.Prewash", "value": false}, {"key": "LaundryCare.Washer.Option.SpinSpeed", "value": "LaundryCare.Washer.EnumType.SpinSpeed.RPM600"}, {"key": "LaundryCare.Washer.Option.Temperature", "value": "LaundryCare.Washer.EnumType.Temperature.GC30"}, {"key": "LaundryCare.Washer.Option.WaterAndRinsePlus", "value": "LaundryCare.Washer.EnumType.WaterAndRinsePlus.Off"}, {"key": "BSH.Common.Option.ProgramProgress", "value": 0, "unit": "%"}, {"key": "BSH.Common.Option.RemainingProgramTime", "value": 2530, "unit": "seconds"}, {"key": "BSH.Common.Option.RemainingProgramTimeIsEstimated", "value": true}, {"key": "LaundryCare.Washer.Option.ProcessPhase", "value": "LaundryCare.Washer.EnumType.ProcessPhase.Washing"}, {"key": "BSH.Common.Option.EnergyForecast", "value": 60, "unit": "%"}, {"key": "BSH.Common.Option.WaterForecast", "value": 80, "unit": "%"}], "timestamp": 1677677195}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "ACTIVE-PROGRAM-REQUEST", "timestamp": 1677677215, "error": {"description": "There is no program active", "key": "SDK.Error.NoProgramActive", "timestamp": 1677677215}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "ACTIVE-PROGRAM-REQUEST", "timestamp": 1677753236, "data": {"key": "ConsumerProducts.CoffeeMaker.Program.CleaningModes.ApplianceOffRinsing", "options": [{"key": "BSH.Common.Option.ProgramProgress", "value": 0, "unit": "%"}], "timestamp": 1677753236}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "SELECTED-PROGRAM-REQUEST", "timestamp": 1677915115, "error": {"description": "There is no program selected", "key": "SDK.Error.NoProgramSelected", "timestamp": 1677915115}}
{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "SELECTED-PROGRAM-REQUEST", "timestamp": 1677681250, "data": {"key": "LaundryCare.Dryer.Program.Cotton", "options": [{"key": "BSH.Common.Option.FinishInRelative", "value": 0, "unit": "seconds"}, {"key": "LaundryCare.Dryer.Option.DryingTarget", "value": "LaundryCare.Dryer.EnumType.DryingTarget.CupboardDry"}, {"key": "LaundryCare.Dryer.Option.DryingTargetAdjustment", "value": "LaundryCare.Dryer.EnumType.DryingTargetAdjustment.Plus1"}, {"key": "LaundryCare.Dryer.Option.Gentle", "value": false}, {"key": "LaundryCare.Dryer.Option.WrinkleGuard", "value": "LaundryCare.Dryer.EnumType.WrinkleGuard.Min60"}], "timestamp": 1677681250}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "STATUS-REQUEST", "timestamp": 1641970292, "data": {"error": {"key": "SDK.Error.HomeAppliance.Connection.Initialization.Failed", "description": "HomeAppliance is offline"}}}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "STATUS-REQUEST", "timestamp": 1641912283, "data": {"data": {"status": [{"key": "BSH.Common.Status.LocalControlActive", "value": false}, {"key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Inactive"}, {"key": "BSH.Common.Status.RemoteControlActive", "value": true}]}}}
{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "STATUS-REQUEST", "timestamp": 1674156453, "data": {"data": {"status": [{"key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Run"}, {"key": "BSH.Common.Status.RemoteControlStartAllowed", "value": false}, {"key": "BSH.Common.Status.LocalControlActive", "value": true}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterRistrettoEspresso", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffee", "value": 1}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffeeAndMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterFrothyMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotWater", "value": 0, "unit": "ml"}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterPowderCoffee", "value": 1}, {"key": "BSH.Common.Status.DoorState", "value": "BSH.Common.EnumType.DoorState.Closed"}]}}}
{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1641970292, "data": {"error": {"key": "SDK.Error.HomeAppliance.Connection.Initialization.Failed", "description": "HomeAppliance is offline"}}}
{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1642089087, "data": {"data": {"settings": [{"key": "BSH.Common.Setting.PowerState", "value": "BSH.Common.EnumType.PowerState.Off"}, {"key": "BSH.Common.Setting.AlarmClock", "value": 0, "unit": "seconds"}, {"key": "BSH.Common.Setting.ChildLock", "value": false}, {"key": "BSH.Common.Setting.TemperatureUnit", "value": "BSH.Common.EnumType.TemperatureUnit.Celsius"}]}}}
"""


@fixture(scope="session", autouse=True)
def dotenv():
    load_dotenv()


@fixture(scope="session")
def event_loop():
    loop = get_event_loop()
    yield loop
    loop.close()


@async_fixture(scope="session")
async def client(tmp_path_factory) -> HomeConnectClient:
    result = HomeConnectSimulationClient(token_cache=tmp_path_factory.mktemp("cache") / "token")
    await result.authenticate(username="user", password="password")
    return result


@async_fixture(scope="session")
async def appliance(client: HomeConnectClient) -> HomeConnectAppliance:
    appliances = await client.appliances
    for app in appliances:
        if app.appliance_type == "Washer":
            return app
    raise RuntimeError("No washers available.")


@fixture(scope="function")
def stream_data() -> list[bytes]:
    return [
        b'event:EVENT\ndata:{"items":[{"timestamp":1642001123,"handling":"none","key":"BSH.Common.Event.ProgramFinished","value":"BSH.Common.EnumType.EventPresentState.Present","level":"hint"}],"haId":"SIEMENS-WM14T6H9NL-AB1234567890"}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b"event:KEEP-ALIVE\ndata:\n\n",
        b"event:KEEP-ALIVE\ndata:\n\n",
        b"event:KEEP-ALIVE\ndata:\n\n",
        b"event: KEEP-ALIVE\ndata:\n\n",  # Simulator events have spaces.
        b'event: STATUS\ndata: {"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Status.LocalControlActive","level":"hint","timestamp":1676897835,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.LocalControlActive","value":true},{"handling":"none","key":"BSH.Common.Status.RemoteControlActive","level":"hint","timestamp":1676897835,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.RemoteControlActive","value":false}]}\nid: SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:NOTIFY\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Root.SelectedProgram","level":"hint","timestamp":1676897836,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected","value":"LaundryCare.Washer.Program.DelicatesSilk"}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:NOTIFY\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"LaundryCare.Washer.Option.SpinSpeed","level":"hint","timestamp":1676897836,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/LaundryCare.Washer.Option.SpinSpeed","value":"LaundryCare.Washer.EnumType.SpinSpeed.RPM600"},{"handling":"none","key":"LaundryCare.Washer.Option.Temperature","level":"hint","timestamp":1676897836,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/LaundryCare.Washer.Option.Temperature","value":"LaundryCare.Washer.EnumType.Temperature.GC30"}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:NOTIFY\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Option.FinishInRelative","level":"hint","timestamp":1676897837,"unit":"seconds","uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/BSH.Common.Option.FinishInRelative","value":2580}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:NOTIFY\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Root.SelectedProgram","level":"hint","timestamp":1676897837,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected","value":"LaundryCare.Washer.Program.Wool"}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:NOTIFY\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"LaundryCare.Washer.Option.SpinSpeed","level":"hint","timestamp":1676897837,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/LaundryCare.Washer.Option.SpinSpeed","value":"LaundryCare.Washer.EnumType.SpinSpeed.RPM800"}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:NOTIFY\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Option.FinishInRelative","level":"hint","timestamp":1676897838,"unit":"seconds","uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected/options/BSH.Common.Option.FinishInRelative","value":2400}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:STATUS\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Status.DoorState","level":"hint","timestamp":1676897842,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.DoorState","value":"BSH.Common.EnumType.DoorState.Closed"}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:STATUS\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Status.DoorState","level":"hint","timestamp":1676897845,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.DoorState","value":"BSH.Common.EnumType.DoorState.Open"}]}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b'event:CONNECTED\ndata:{"haId":"SIEMENS-WT8HXM90NL-AB1234567890","handling":"none","key":"BSH.Common.Appliance.Connected","level":"hint","timestamp":1676897865,"value":true}\nid:SIEMENS-WT8HXM90NL-AB1234567890\n\n',
        b"event:KEEP-ALIVE\ndata:\n\n",
        b'event:STATUS\ndata:{"haId":"SIEMENS-WT8HXM90NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Status.RemoteControlStartAllowed","level":"hint","timestamp":1676897868,"uri":"/api/homeappliances/SIEMENS-WT8HXM90NL-AB1234567890/status/BSH.Common.Status.RemoteControlStartAllowed","value":false}]}\nid:SIEMENS-WT8HXM90NL-AB1234567890\n\n',
        b'event:NOTIFY\ndata:{"haId":"SIEMENS-WT8HXM90NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Root.ActiveProgram","level":"hint","timestamp":1676897868,"uri":"/api/homeappliances/SIEMENS-WT8HXM90NL-AB1234567890/programs/active","value":null},{"handling":"none","key":"BSH.Common.Root.SelectedProgram","level":"hint","timestamp":1676897868,"uri":"/api/homeappliances/SIEMENS-WT8HXM90NL-AB1234567890/programs/selected","value":"LaundryCare.Dryer.Program.Cotton"}]}\nid:SIEMENS-WT8HXM90NL-AB1234567890\n\n',
        b"event:KEEP-ALIVE\ndata:\n\n",
        b"event:KEEP-ALIVE\ndata:\n\n",
        b'event:DISCONNECTED\ndata:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","handling":"none","key":"BSH.Common.Appliance.Disconnected","level":"hint","timestamp":1676897981,"value":true}\nid:SIEMENS-WM14T6H9NL-AB1234567890\n\n',
        b"event:KEEP-ALIVE\ndata:\n\n",
    ]


@fixture(scope="function", params=JSON_EVENTS.strip().split("\n"))
def event(request) -> HomeConnectEvent:
    return HomeConnectEvent.from_string(request.param)
