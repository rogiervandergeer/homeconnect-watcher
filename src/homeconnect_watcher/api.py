from contextlib import ExitStack

from dotenv import load_dotenv

from homeconnect_watcher.client.client import HomeConnectClient, HomeConnectSimulationClient
from homeconnect_watcher.exporter.base import BaseExporter

load_dotenv()


async def loop(
    client: HomeConnectClient,
    exporters: list[BaseExporter],
):
    if isinstance(client, HomeConnectSimulationClient):
        await client.authenticate("username", "password")

    if len(exporters) == 0:
        raise ValueError("No exporters defined.")
    with ExitStack() as stack:
        for exporter in exporters:
            stack.enter_context(exporter)

        async for event in client.watch():
            for exporter in exporters:
                exporter.export(event)
