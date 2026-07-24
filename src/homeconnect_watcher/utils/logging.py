from enum import Enum
from logging import DEBUG, INFO, WARNING, basicConfig


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"


def initialize_logging(level: LogLevel) -> None:
    numeric_level = WARNING if level == LogLevel.WARNING else INFO if level == LogLevel.INFO else DEBUG
    basicConfig(level=numeric_level, format="%(asctime)s %(name)s - %(levelname)s:%(message)s")
