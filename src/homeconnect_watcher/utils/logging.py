from enum import Enum
from logging import basicConfig, DEBUG, INFO, WARNING


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"


def initialize_logging(level: LogLevel) -> None:
    level = WARNING if level == LogLevel.WARNING else INFO if level == LogLevel.INFO else DEBUG
    basicConfig(level=level, format="%(asctime)s %(name)s - %(levelname)s:%(message)s")
