from dataclasses import dataclass
from datetime import datetime
from json import dumps, loads
from time import time

from homeconnect_watcher.trigger import Trigger


@dataclass
class HomeConnectEvent:
    event: str
    timestamp: float
    appliance_id: str | None = None
    data: dict[str, ...] | None = None
    error: dict[str, ...] | None = None

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp).astimezone()

    @classmethod
    def from_request(cls, request: str, appliance_id: str, response: dict[str, ...]) -> "HomeConnectEvent":
        if "error" in response:
            error = response["error"]
            data = None
        else:
            data = response["data"]
            error = None
        return HomeConnectEvent(
            event=f"{request}-REQUEST",
            timestamp=time(),
            appliance_id=appliance_id,
            data=data,
            error=error,
        )

    @classmethod
    def from_stream(cls, stream: bytes) -> "HomeConnectEvent":
        data = {"timestamp": time()}
        for line in stream.decode("utf-8").split("\n"):
            if line.startswith("data:") and len(line) > 5:
                data["data"] = loads(line[5:])
            elif line.startswith("event:"):
                data["event"] = line[6:].strip()
            elif line.startswith("id:"):
                data["appliance_id"] = line[3:].strip()
        return cls(**data)

    @classmethod
    def from_string(cls, string: str) -> "HomeConnectEvent":
        result = cls(**loads(string))
        return result

    @property
    def is_request(self) -> bool:
        return self.event.endswith("-REQUEST")

    @property
    def items(self) -> dict[str, str | None]:
        """Extract the payload into key/value pairs."""
        if self.event == "KEEP-ALIVE":
            return {}
        elif self.error_key is not None and len(self.error_key) == 3:  # Error code like 429, 500
            return {}
        elif self.event == "ACTIVE-PROGRAM-REQUEST":
            if self.error_key in (
                "SDK.Error.NoProgramActive",
                "SDK.Error.HomeAppliance.Connection.Initialization.Failed",
            ):
                return {"BSH.Common.Root.ActiveProgram": None}
            else:
                result = {item["key"]: item["value"] for item in self.data["options"]}
                result["BSH.Common.Root.ActiveProgram"] = self.data["key"]
                return result
        elif self.event == "SELECTED-PROGRAM-REQUEST":
            if self.error_key in (
                "SDK.Error.NoProgramSelected",
                "SDK.Error.HomeAppliance.Connection.Initialization.Failed",
            ):
                return {"BSH.Common.Root.SelectedProgram": None}
            else:
                result = {item["key"]: item["value"] for item in self.data["options"]}
                result["BSH.Common.Root.SelectedProgram"] = self.data["key"]
                return result
        elif self.error is not None:
            return {}
        elif self.event == "STATUS-REQUEST":
            return {entry["key"]: entry["value"] for entry in self.data["status"]}
        elif self.event == "SETTINGS-REQUEST":
            return {entry["key"]: entry["value"] for entry in self.data["settings"]}
        elif self.event in ("CONNECTED", "DISCONNECTED"):
            if self.data is not None and "key" in self.data:
                return {self.data["key"]: self.data["value"]}
            else:
                return {}
        elif self.data is not None:
            if "items" in self.data:  # For STATUS/EVENT/NOTIFY
                return {item["key"]: item["value"] for item in self.data["items"]}
        raise ValueError("Malformed Event")

    @property
    def error_key(self) -> str | None:
        if self.error:
            return self.error["key"]
        return None

    def __str__(self) -> str:
        data = dict(appliance_id=self.appliance_id, event=self.event, timestamp=self.timestamp)
        if self.data:
            data["data"] = self.data
        if self.error:
            data["error"] = self.error
        return dumps(data) + "\n"

    @property
    def trigger(self) -> Trigger | None:
        if self.event in ("CONNECTED", "PAIRED"):
            # For any new(ly connected) appliance, we perform all requests.
            return Trigger(
                appliance_id=self.appliance_id, status=True, settings=True, selected_program=True, active_program=True
            )
        elif self.event in ("NOTIFY", "EVENT"):
            # For any appliance that is active, request the status once in a while.
            return Trigger(appliance_id=self.appliance_id, status=True, interval=True)
        elif self.event == "STATUS":
            # For an appliance that just switched to running, get the program.
            if self.items.get("BSH.Common.Status.OperationState", "") == "BSH.Common.EnumType.OperationState.Run":
                return Trigger(appliance_id=self.appliance_id, active_program=True, settings=True)
            # For an appliance that was controlled locally, but is no more: get the programs once in a while.
            if self.items.get("BSH.Common.Status.LocalControlActive") is False:
                return Trigger(
                    appliance_id=self.appliance_id, active_program=True, selected_program=True, interval=True
                )
        return None
