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

    @classmethod
    def from_request(cls, request: str, appliance_id: str, response: dict) -> "HomeConnectEvent":
        if "error" in response:
            raise HomeConnectRequestError(response["error"])
        response["data"]["timestamp"] = int(time())
        return HomeConnectEvent(event=f"{request}-REQUEST", appliance_id=appliance_id, data=response["data"])

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
    def timestamp(self) -> int | None:
        """Look up the timestamp from the event data."""
        if self.data:
            if "timestamp" in self.data:
                return self.data["timestamp"]
            # This assumes that all timestamps of the items are equal.
            return self.data["items"][0]["timestamp"]

    def __str__(self) -> str:
        return dumps(dict(appliance_id=self.appliance_id, data=self.data, event=self.event)) + "\n"

    @property
    def trigger(self) -> Trigger:
        if self.event in ("CONNECTED", "PAIRED"):
            return Trigger(
                appliance_id=self.appliance_id, status=True, settings=True, selected_program=True, active_program=True
            )
        elif self.event in ("NOTIFY", "EVENT"):
            pass
        elif self.event == "STATUS":
            pass
        return Trigger(appliance_id=self.appliance_id)  # Empty trigger
