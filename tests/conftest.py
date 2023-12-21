from asyncio import get_event_loop
from pathlib import Path

from dotenv import load_dotenv

from pytest import fixture
from pytest_asyncio import fixture as async_fixture

from homeconnect_watcher.client import HomeConnectClient, HomeConnectAppliance
from homeconnect_watcher.client.client import HomeConnectSimulationClient


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
