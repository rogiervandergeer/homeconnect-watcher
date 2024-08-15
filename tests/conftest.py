from asyncio import get_event_loop

from dotenv import load_dotenv
from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from homeconnect_watcher.client import HomeConnectClient, HomeConnectAppliance
from homeconnect_watcher.client.client import HomeConnectSimulationClient
from homeconnect_watcher.db import WatcherDBClient
from homeconnect_watcher.event import HomeConnectEvent


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


STREAM_EVENTS = [
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


JSON_EVENTS = [
    '{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "CONNECTED", "timestamp": 1642062149.0}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "CONNECTED", "timestamp": 1678086769.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "handling": "none", "key": "BSH.Common.Appliance.Connected", "level": "hint", "timestamp": 1678086769.0, "value": true}}',
    '{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "DISCONNECTED", "timestamp": 1642272958.0}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "DISCONNECTED", "timestamp": 1678523735.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "handling": "none", "key": "BSH.Common.Appliance.Disconnected", "level": "hint", "timestamp": 1678523735.0, "value": true}}',
    '{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "EVENT", "timestamp": 1642099217.0, "data": {"items": [{"timestamp": 1642099216.0, "handling": "none", "key": "BSH.Common.Event.ProgramFinished", "value": "BSH.Common.EnumType.EventPresentState.Present", "level": "hint"}], "haId": "SIEMENS-WT8HXM90NL-AB1234567890"}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "EVENT", "timestamp": 1676105965.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "ConsumerProducts.CoffeeMaker.Event.DripTrayFull", "level": "alert", "timestamp": 1676105965.0, "value": "BSH.Common.EnumType.EventPresentState.Off"}]}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "NOTIFY", "timestamp": 1674156563.0, "data": {"haId": "SIEMENS-TI9553X1RW-AB1234567890", "items": [{"handling": "none", "key": "BSH.Common.Option.ProgramProgress", "level": "hint", "timestamp": 1674156563.0, "unit": "%", "uri": "/api/homeappliances/SIEMENS-TI9553X1RW-AB1234567890/programs/active/options/BSH.Common.Option.ProgramProgress", "value": 31}]}}',
    '{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "NOTIFY", "timestamp": 1642002626.0, "data": {"items": [{"timestamp": 1642002626.0, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WT8HXM90NL-AB1234567890/programs/active/options/BSH.Common.Option.RemainingProgramTime", "key": "BSH.Common.Option.RemainingProgramTime", "unit": "seconds", "value": 17460, "level": "hint"}], "haId": "SIEMENS-WT8HXM90NL-AB1234567890"}}',
    '{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "NOTIFY", "timestamp": 1642090703.0, "data": {"items": [{"timestamp": 1642090703.0, "handling": "none", "uri": "/api/homeappliances/SIEMENS-EX877LVV5E-AB1234567890/programs/active/options/BSH.Common.Option.ElapsedProgramTime", "key": "BSH.Common.Option.ElapsedProgramTime", "unit": "seconds", "value": 72, "level": "hint"}], "haId": "SIEMENS-EX877LVV5E-AB1234567890"}}',
    '{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "STATUS", "timestamp": 1642087522.0, "data": {"items": [{"timestamp": 1642087522.0, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WT8HXM90NL-AB1234567890/status/BSH.Common.Status.LocalControlActive", "key": "BSH.Common.Status.LocalControlActive", "value": true, "level": "hint"}, {"timestamp": 1642087522.0, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WT8HXM90NL-AB1234567890/status/BSH.Common.Status.RemoteControlActive", "key": "BSH.Common.Status.RemoteControlActive", "value": false, "level": "hint"}], "haId": "SIEMENS-WT8HXM90NL-AB1234567890"}}',
    '{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "STATUS", "timestamp": 1642001123.0, "data": {"items": [{"timestamp": 1642001123.0, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.OperationState", "key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Finished", "level": "hint"}, {"timestamp": 1642001123.0, "handling": "none", "uri": "/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.DoorState", "key": "BSH.Common.Status.DoorState", "value": "BSH.Common.EnumType.DoorState.Closed", "level": "hint"}], "haId": "SIEMENS-WM14T6H9NL-AB1234567890"}}',
    '{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "ACTIVE-PROGRAM-REQUEST", "timestamp": 1677680171.0, "data": {"key": "LaundryCare.Washer.Program.DelicatesSilk", "options": [{"key": "LaundryCare.Common.Option.LoadRecommendation", "value": 2000, "unit": "gram"}, {"key": "LaundryCare.Common.Option.VarioPerfect", "value": "LaundryCare.Common.EnumType.VarioPerfect.Off"}, {"key": "LaundryCare.Washer.Option.IDos1DosingLevel", "value": "LaundryCare.Washer.EnumType.IDosingLevel.Light"}, {"key": "LaundryCare.Washer.Option.IDos2DosingLevel", "value": "LaundryCare.Washer.EnumType.IDosingLevel.Light"}, {"key": "LaundryCare.Washer.Option.LessIroning", "value": false}, {"key": "LaundryCare.Washer.Option.Prewash", "value": false}, {"key": "LaundryCare.Washer.Option.SpinSpeed", "value": "LaundryCare.Washer.EnumType.SpinSpeed.RPM600"}, {"key": "LaundryCare.Washer.Option.Temperature", "value": "LaundryCare.Washer.EnumType.Temperature.GC30"}, {"key": "LaundryCare.Washer.Option.WaterAndRinsePlus", "value": "LaundryCare.Washer.EnumType.WaterAndRinsePlus.Off"}, {"key": "BSH.Common.Option.ProgramProgress", "value": 0, "unit": "%"}, {"key": "BSH.Common.Option.RemainingProgramTime", "value": 0, "unit": "seconds"}, {"key": "BSH.Common.Option.RemainingProgramTimeIsEstimated", "value": true}, {"key": "LaundryCare.Washer.Option.ProcessPhase", "value": "LaundryCare.Washer.EnumType.ProcessPhase.FinalSpinning"}, {"key": "BSH.Common.Option.EnergyForecast", "value": 60, "unit": "%"}, {"key": "BSH.Common.Option.WaterForecast", "value": 80, "unit": "%"}], "timestamp": 1677680171.0}}',
    '{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "ACTIVE-PROGRAM-REQUEST", "timestamp": 1678036051.0, "error": {"description": "There is no program active", "key": "SDK.Error.NoProgramActive", "timestamp": 1678036051.0}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "ACTIVE-PROGRAM-REQUEST", "timestamp": 1677741033.0, "data": {"key": "ConsumerProducts.CoffeeMaker.Program.CleaningModes.ApplianceOnRinsing", "options": [{"key": "BSH.Common.Option.ProgramProgress", "value": 52, "unit": "%"}], "timestamp": 1677741033.0}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "ACTIVE-PROGRAM-REQUEST", "timestamp": 1677742394.0, "data": {"key": "ConsumerProducts.CoffeeMaker.Program.Beverage.Coffee", "options": [{"key": "ConsumerProducts.CoffeeMaker.Option.CoffeeTemperature", "value": "ConsumerProducts.CoffeeMaker.EnumType.CoffeeTemperature.88C"}, {"key": "ConsumerProducts.CoffeeMaker.Option.BeanAmount", "value": "ConsumerProducts.CoffeeMaker.EnumType.BeanAmount.Strong"}, {"key": "ConsumerProducts.CoffeeMaker.Option.FillQuantity", "value": 120, "unit": "ml"}, {"key": "ConsumerProducts.CoffeeMaker.Option.MultipleBeverages", "value": false}, {"key": "ConsumerProducts.CoffeeMaker.Option.FlowRate", "value": "ConsumerProducts.CoffeeMaker.EnumType.FlowRate.Normal"}, {"key": "BSH.Common.Option.ProgramProgress", "value": 0, "unit": "%"}], "timestamp": 1677742394.0}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "SELECTED-PROGRAM-REQUEST", "timestamp": 1677848265.0, "error": {"description": "There is no program selected", "key": "SDK.Error.NoProgramSelected", "timestamp": 1677848265.0}}',
    '{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "SELECTED-PROGRAM-REQUEST", "timestamp": 1677673218.0, "data": {"key": "LaundryCare.Dryer.Program.ColdRefresh.1Piece", "options": [{"key": "BSH.Common.Option.FinishInRelative", "value": 0, "unit": "seconds"}, {"key": "LaundryCare.Dryer.Option.DryingTarget", "value": "LaundryCare.Dryer.EnumType.DryingTarget.CupboardDry"}, {"key": "LaundryCare.Dryer.Option.WrinkleGuard", "value": "LaundryCare.Dryer.EnumType.WrinkleGuard.Min60"}], "timestamp": 1677673218.0}}',
    '{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "SELECTED-PROGRAM-REQUEST", "timestamp": 1678031334.0, "data": {"key": "LaundryCare.Washer.Program.Auto40", "options": [{"key": "LaundryCare.Common.Option.LoadRecommendation", "value": 6000, "unit": "gram"}, {"key": "LaundryCare.Washer.Option.IDos1DosingLevel", "value": "LaundryCare.Washer.EnumType.IDosingLevel.Normal"}, {"key": "LaundryCare.Washer.Option.IDos2DosingLevel", "value": "LaundryCare.Washer.EnumType.IDosingLevel.Normal"}, {"key": "LaundryCare.Washer.Option.SpinSpeed", "value": "LaundryCare.Washer.EnumType.SpinSpeed.Auto"}, {"key": "LaundryCare.Washer.Option.Temperature", "value": "LaundryCare.Washer.EnumType.Temperature.Auto"}], "timestamp": 1678031334.0}}',
    '{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1641970292.0, "error": {"key": "SDK.Error.HomeAppliance.Connection.Initialization.Failed", "description": "HomeAppliance is offline"}}',
    '{"appliance_id": "SIEMENS-WM14T6H9NL-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1642000630.0, "data": {"settings": [{"key": "BSH.Common.Setting.PowerState", "value": "BSH.Common.EnumType.PowerState.On"}]}}',
    '{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1642089087.0, "data": {"settings": [{"key": "BSH.Common.Setting.PowerState", "value": "BSH.Common.EnumType.PowerState.Off"}, {"key": "BSH.Common.Setting.AlarmClock", "value": 0, "unit": "seconds"}, {"key": "BSH.Common.Setting.ChildLock", "value": false}, {"key": "BSH.Common.Setting.TemperatureUnit", "value": "BSH.Common.EnumType.TemperatureUnit.Celsius"}]}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1674293120.0, "data": {"settings": [{"key": "BSH.Common.Setting.ChildLock", "value": false}, {"key": "BSH.Common.Setting.PowerState", "value": "BSH.Common.EnumType.PowerState.On"}, {"key": "ConsumerProducts.CoffeeMaker.Setting.CupWarmer", "value": false}]}}',
    '{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "STATUS-REQUEST", "timestamp": 1642000633.0, "data": {"status": [{"key": "BSH.Common.Status.LocalControlActive", "value": false}, {"key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Inactive"}, {"key": "BSH.Common.Status.RemoteControlActive", "value": true}]}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "STATUS-REQUEST", "timestamp": 1674291950.0, "data": {"status": [{"key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Ready"}, {"key": "BSH.Common.Status.RemoteControlStartAllowed", "value": false}, {"key": "BSH.Common.Status.LocalControlActive", "value": false}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterRistrettoEspresso", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffee", "value": 1}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffeeAndMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterFrothyMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotWater", "value": 0, "unit": "ml"}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterPowderCoffee", "value": 1}, {"key": "BSH.Common.Status.DoorState", "value": "BSH.Common.EnumType.DoorState.Closed"}]}}',
    '{"appliance_id": "SIEMENS-TI9553X1RW-AB1234567890", "event": "STATUS-REQUEST", "timestamp": 1677667430.0, "data": {"status": [{"key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Inactive"}, {"key": "BSH.Common.Status.RemoteControlStartAllowed", "value": true}, {"key": "BSH.Common.Status.LocalControlActive", "value": false}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterRistrettoEspresso", "value": 16}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffee", "value": 38}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffeeAndMilk", "value": 43}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterFrothyMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotMilk", "value": 0}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotWater", "value": 0, "unit": "ml"}, {"key": "ConsumerProducts.CoffeeMaker.Status.BeverageCounterPowderCoffee", "value": 1}, {"key": "BSH.Common.Status.DoorState", "value": "BSH.Common.EnumType.DoorState.Closed"}], "timestamp": 1677667430.0}}',
    '{"appliance_id": "SIEMENS-EX877LVV5E-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1702944761.0, "data": {"settings": [{"key": "BSH.Common.Setting.PowerState", "value": "BSH.Common.EnumType.PowerState.Off"}, {"key": "BSH.Common.Setting.AlarmClock", "value": 0, "unit": "seconds"}, {"key": "BSH.Common.Setting.ChildLock", "value": false}, {"key": "BSH.Common.Setting.TemperatureUnit", "value": "BSH.Common.EnumType.TemperatureUnit.Celsius"}]}}',
    '{"appliance_id": null, "event": "KEEP-ALIVE", "timestamp": 1674291950.0}',
    '{"appliance_id": "SIEMENS-WT8HXM90NL-AB1234567890", "event": "SETTINGS-REQUEST", "timestamp": 1682306041.0, "error": {"description": "The rate limit \\"10 successive error calls in 10 minutes\\" was reached. Requests are blocked during the remaining period of 564 seconds.", "key": "429"}}',
]


@fixture(scope="function", params=STREAM_EVENTS)
def stream_event(request) -> bytes:
    return request.param


@fixture(scope="function", params=JSON_EVENTS)
def event(request) -> HomeConnectEvent:
    return HomeConnectEvent.from_string(request.param)


@fixture(scope="function")
def db_client(postgresql) -> WatcherDBClient:
    client = WatcherDBClient(
        connection_string=f"postgresql://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    with client:
        yield client
