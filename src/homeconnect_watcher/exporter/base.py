from abc import ABCMeta, abstractmethod
from logging import getLogger


from homeconnect_watcher.event import HomeConnectEvent


class BaseExporter(metaclass=ABCMeta):
    def __init__(self):
        self.logger = getLogger(self.__class__.__name__)

    def __enter__(self) -> "BaseExporter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return

    @abstractmethod
    def export(self, event: HomeConnectEvent) -> None:
        pass

    def bulk_export(self, events: list[HomeConnectEvent]) -> None:
        for event in events:
            self.export(event)
