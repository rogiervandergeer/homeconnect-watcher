from dataclasses import dataclass
from json import dumps, loads
from time import time

from homeconnect_watcher.client.trigger import Trigger
from homeconnect_watcher.exceptions import HomeConnectRequestError


@dataclass
class HomeConnectEvent:
    event: str
    appliance_id: str | None = None
    data: dict[str, ...] | None = None
    error: dict[str, ...] | None = None

    @classmethod
    def from_request(cls, request: str, appliance_id: str, response: dict[str, ...]) -> "HomeConnectEvent":
        data = None
        error = None
        if "error" in response:
            error = response["error"]
            error["timestamp"] = int(time())
        else:
            data = response["data"]
            data["timestamp"] = int(time())
        return HomeConnectEvent(event=f"{request}-REQUEST", appliance_id=appliance_id, data=data, error=error)

    @classmethod
    def from_stream(cls, stream: bytes) -> "HomeConnectEvent":
        data = {}
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
        return cls(**loads(string))

    @property
    def is_request(self) -> bool:
        return self.event.endswith("-REQUEST")

    @property
    def items(self) -> dict[str, str | None]:
        """Extract the payload into key/value pairs."""
        if self.data is not None:
            if "items" in self.data:  # For STATUS/EVENT/NOTIFY
                return {item["key"]: item["value"] for item in self.data["items"]}
            elif "key" in self.data:  # For CONNECTED/DISCONNECTED
                return {self.data["key"]: self.data["value"]}
            elif "status" in self.data:  # For STATUS-REQUEST
                return self.data["status"]
            elif "settings" in self.data:  # For SETTINGS-REQUEST
                return self.data["settings"]
        elif self.event == "ACTIVE-PROGRAM-REQUEST":
            if self.error_key == "SDK.Error.NoProgramActive":
                return {"BSH.Common.Root.ActiveProgram": None}
            else:
                result = {item["key"]: item["value"] for item in self.data["options"]}
                result["BSH.Common.Root.ActiveProgram"] = self.data["key"]
                return result
        elif self.event == "SELECTED-PROGRAM-REQUEST":
            if self.error_key == "SDK.Error.NoProgramSelected":
                return {"BSH.Common.Root.SelectedProgram": None}
            else:
                result = {item["key"]: item["value"] for item in self.data["options"]}
                result["BSH.Common.Root.SelectedProgram"] = self.data["key"]
                return result
        return {}

    @property
    def error_key(self) -> str | None:
        if self.error:
            return self.error["key"]
        return None

    @property
    def timestamp(self) -> int | None:
        """Look up the timestamp from the event data."""
        if self.data:
            if "timestamp" in self.data:
                return self.data["timestamp"]
            # This assumes that all timestamps of the items are equal.
            return self.data["items"][0]["timestamp"]

    def __str__(self) -> str:
        data = dict(appliance_id=self.appliance_id, event=self.event)
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
