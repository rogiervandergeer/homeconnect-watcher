from time import time
from typing import TYPE_CHECKING

from homeconnect_watcher.event import HomeConnectEvent
from homeconnect_watcher.exceptions import HomeConnectRequestError

if TYPE_CHECKING:
    from .client import HomeConnectClient


class HomeConnectAppliance:
    def __init__(self, client: "HomeConnectClient", appliance_id: str, appliance_type: str):
        self.client = client
        self.appliance_id = appliance_id
        self.appliance_type = appliance_type
        self._available_programs: list[str] | None = None
        self._last_update: dict[str, float] = dict()

    def __repr__(self) -> str:
        return f"HomeConnect{self.appliance_type}(ha_id={repr(self.appliance_id)})"

    def time_since_update(self, request_type: str) -> float:
        return time() - self._last_update.get(request_type, 0)

    async def get_available_programs(self) -> list[str] | None:
        if self._available_programs is None:
            response = await self.client._get(f"/{self.appliance_id}/programs/available")
            if "error" in response:
                # Some appliances do not support programs.
                if response["error"]["key"] == "SDK.Error.UnsupportedOperation":
                    self._available_programs = []
                elif response["error"]["key"] in (
                    "SDK.Error.HomeAppliance.Connection.Initialization.Failed",
                    "SDK.Error.WrongOperationState",
                ):
                    return None
                else:
                    self.client.logger.error(response["error"])
                    raise HomeConnectRequestError(response["error"]["key"])
            else:
                self._available_programs = [program["key"] for program in response["data"]["programs"]]
        return self._available_programs if len(self._available_programs) else None

    async def get_status(self) -> HomeConnectEvent:
        self._last_update["status"] = time()
        response = await self.client._get(f"/{self.appliance_id}/status")
        return HomeConnectEvent.from_request(request="STATUS", appliance_id=self.appliance_id, response=response)

    async def get_settings(self) -> HomeConnectEvent:
        self._last_update["settings"] = time()
        response = await self.client._get(f"/{self.appliance_id}/settings")
        return HomeConnectEvent.from_request(request="SETTINGS", appliance_id=self.appliance_id, response=response)

    async def get_active_program(self) -> HomeConnectEvent:
        self._last_update["active_program"] = time()
        response = await self.client._get(f"/{self.appliance_id}/programs/active")
        return HomeConnectEvent.from_request(
            request="ACTIVE-PROGRAM", appliance_id=self.appliance_id, response=response
        )

    async def get_selected_program(self) -> HomeConnectEvent:
        self._last_update["selected_program"] = time()
        response = await self.client._get(f"/{self.appliance_id}/programs/selected")
        return HomeConnectEvent.from_request(
            request="SELECTED-PROGRAM", appliance_id=self.appliance_id, response=response
        )
