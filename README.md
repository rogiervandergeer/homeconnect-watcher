# homeconnect-watcher

Python service that listens to HomeConnect event and logs them.

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/rogiervandergeer/homeconnect-watcher/ci.yaml?branch=main)
![PyPI](https://img.shields.io/pypi/v/homeconnect-watcher)
![PyPI - License](https://img.shields.io/pypi/l/homeconnect-watcher)
![PyPI - Downloads](https://img.shields.io/pypi/dm/homeconnect-watcher)


## Usage

Before you start, create a developer account at https://developer.home-connect.com/ and
register an application with the "Authorization Code Grant Flow" as OAuth Flow
and `http://localhost:8000/code/` as redirect URL.

Next, set the following environment variables with the values of your application:
- `HOMECONNECT_CLIENT_ID`
- `HOMECONNECT_CLIENT_SECRET`
- `HOMECONNECT_REDIRECT_URI`

### Authorization

The watcher requires a token, which will be automatically refreshed once obtained. To obtain the first token run
```
homeconnect-watcher authorize
```
and follow the instructions.

If the watcher is used regularly, this only needs to be done once.

### Watching

Next up, run

```
homeconnect-watcher watch
```

## Exposing Metrics to Prometheus

The watcher can expose its metrics to Prometheus. This requires the `prometheus-client` to be installed;
```shell
pip install "homeconnect-watcher[prometheus]"
```

Then, when starting the watcher, pass the port you want to expose the metrics to. For example:
```shell
homeconnect-watcher watch --metrics-port 8000
```

## Events

Events are received as multi-line byte-strings, and always end with a double newline (`\n\n`). They (may) contain the
following keys:
- event: Event type. One of the types listed below.
- data: Contains a JSON dictionary. For Keep-Alive events, this field is present, but empty.
- id: Contains the appliance id. For Keep-Alive events, this field is missing.

Events come in the following flavours:

#### Keep-Alive

Periodic keep-alive message (interval: every 55 seconds)

```
event:KEEP-ALIVE
data:
```

#### Status

Status changes (e.g. "DoorState")

```
event:STATUS
data:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Status.LocalControlActive","level":"hint","timestamp":1676897835.000,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.LocalControlActive","value":true},{"handling":"none","key":"BSH.Common.Status.RemoteControlActive","level":"hint","timestamp":1676897835.000,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/status/BSH.Common.Status.RemoteControlActive","value":false}]}
id:SIEMENS-WM14T6H9NL-AB1234567890
```

#### Event

Event (e.g. "Preheat finished")

```
event:EVENT
data:{"items":[{"timestamp":1642001123.000,"handling":"none","key":"BSH.Common.Event.ProgramFinished","value":"BSH.Common.EnumType.EventPresentState.Present","level":"hint"}],"haId":"SIEMENS-WM14T6H9NL-AB1234567890"}
id:SIEMENS-WM14T6H9NL-AB1234567890
```

#### Notify

Value changes

```
event:NOTIFY
data:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","items":[{"handling":"none","key":"BSH.Common.Root.SelectedProgram","level":"hint","timestamp":1676897836.000,"uri":"/api/homeappliances/SIEMENS-WM14T6H9NL-AB1234567890/programs/selected","value":"LaundryCare.Washer.Program.DelicatesSilk"}]}
id:SIEMENS-WM14T6H9NL-AB1234567890
```

#### Connected

Connection to home appliance re-established

```
event:CONNECTED
data:{"haId":"SIEMENS-WT8HXM90NL-AB1234567890","handling":"none","key":"BSH.Common.Appliance.Connected","level":"hint","timestamp":1676897865.000,"value":true}
id:SIEMENS-WT8HXM90NL-AB1234567890
```

#### Disconnected

Connection to home appliance lost or not possible

```
event:DISCONNECTED
data:{"haId":"SIEMENS-WM14T6H9NL-AB1234567890","handling":"none","key":"BSH.Common.Appliance.Disconnected","level":"hint","timestamp":1676897981.000,"value":true}
id:SIEMENS-WM14T6H9NL-AB1234567890
```

#### Paired

New home appliance was added to HC account, this appliance can be directly monitored with an open event stream

TODO: add example

#### Depaired

Existing home appliance was removed, monitoring of this appliance is no longer possible

TODO: add example

## Requests

We can make three kinds of requests to an appliance.
These return a payload with one of the following keys:
- "data", containing a dictionary with the result, or
- "error", in case something went wrong.

#### Status

Status information

```json
{
  "data": {
    "status": [
      {
        "key": "BSH.Common.Status.RemoteControlActive",
        "value": true
      },
      {
        "key": "BSH.Common.Status.RemoteControlStartAllowed",
        "value": false
      },
      {
        "key": "BSH.Common.Status.OperationState",
        "value": "BSH.Common.EnumType.OperationState.Run"
      },
      {
        "key": "BSH.Common.Status.DoorState",
        "value": "BSH.Common.EnumType.DoorState.Closed"
      }
    ]
  }
}
```

#### Settings

Settings information

```json
{
  "data": {
    "settings": [
      {
        "key": "BSH.Common.Setting.PowerState",
        "value": "BSH.Common.EnumType.PowerState.On"
      }
    ]
  }
}
```


#### Programs Active

```json
{
  "data": {
    "key": "LaundryCare.Dryer.Program.Cotton",
    "options": [
      {
        "key": "LaundryCare.Dryer.Option.DryingTarget",
        "value": "LaundryCare.Dryer.EnumType.DryingTarget.CupboardDry",
        "unit": "enum"
      },
      {
        "key": "BSH.Common.Option.ProgramProgress",
        "value": 3,
        "unit": "%"
      },
      {
        "key": "BSH.Common.Option.RemainingProgramTime",
        "value": 348,
        "unit": "seconds"
      },
      {
        "key": "BSH.Common.Option.ElapsedProgramTime",
        "value": 12,
        "unit": "seconds"
      },
      {
        "key": "BSH.Common.Option.Duration",
        "value": 360,
        "unit": "seconds"
      }
    ]
  }
}
```
