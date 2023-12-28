from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from homeconnect_watcher.event import HomeConnectEvent


def read_events(path: Path) -> Iterable[list[HomeConnectEvent]]:
    for f in tqdm(list(path.glob("*.jsonl"))):
        contents = f.read_text()
        data = []
        for line in contents.split("\n"):
            if len(line) == 0:
                # Skip empty lines
                continue
            event = HomeConnectEvent.from_string(line)
            if event.timestamp is None:
                # Skip events that have no timestamp
                continue
            data.append(event)
        yield data
