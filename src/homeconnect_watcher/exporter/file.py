from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, TextIO

from homeconnect_watcher.event import HomeConnectEvent

from .base import BaseExporter


class FileExporter(BaseExporter):
    def __init__(self, path: Path, flush_interval: timedelta = timedelta(minutes=30)):
        super().__init__()
        self.path = path
        self.flush_interval = flush_interval
        self._fp: Optional[TextIO] = None
        self._last_flush: datetime = datetime.now()

    def __enter__(self) -> "FileExporter":
        self._fp = self._open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._fp.close()
        self._fp = None
        return

    def export(self, event: HomeConnectEvent) -> None:
        self._fp.write(str(event))
        self._flush()

    def _flush(self) -> None:
        now = datetime.now()
        if now.date() != self._last_flush.date():
            self._fp.close()
            self._fp = self._open()
        elif now - self._last_flush > self.flush_interval:
            self.logger.info("Flushing output file.")
            self._last_flush = datetime.now()
            self._fp.flush()

    def _open(self) -> TextIO:
        self._last_flush = datetime.now()
        path = self.path / f"hcw_{self._last_flush.date().strftime('%Y-%m-%d')}.jsonl"
        self.logger.info(f"Opening output file {str(path)}.")
        return path.open("a")
