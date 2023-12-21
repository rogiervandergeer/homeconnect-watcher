from datetime import timedelta
from os import environ
from pathlib import Path

from dotenv import load_dotenv

from homeconnect_watcher.client.client import HomeConnectClient, HomeConnectSimulationClient
from homeconnect_watcher.exporter.file import FileExporter

load_dotenv()


async def loop(client: HomeConnectClient, flush_interval: int):
    if isinstance(client, HomeConnectSimulationClient):
        await client.authenticate("username", "password")
    path = Path(environ["HOMECONNECT_PATH"]) if "HOMECONNECT_PATH" in environ else Path()
    exporter = FileExporter(path, flush_interval=timedelta(seconds=flush_interval))
    with exporter:
        async for event in client.watch():
            exporter.export(event)
