from abc import ABCMeta, abstractmethod

from homeconnect_watcher.event import HomeConnectEvent


class BaseExporter(metaclass=ABCMeta):
    def __enter__(self) -> "BaseExporter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return

    @abstractmethod
    def export(self, event: HomeConnectEvent) -> None:
        pass
