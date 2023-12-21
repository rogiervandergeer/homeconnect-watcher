from dataclasses import dataclass


@dataclass
class Trigger:
    appliance_id: str
    status: bool = False
    settings: bool = False
    active_program: bool = False
    selected_program: bool = False
    interval: bool = False
