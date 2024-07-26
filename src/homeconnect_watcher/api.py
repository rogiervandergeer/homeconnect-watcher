from contextlib import ExitStack

from dotenv import load_dotenv

from homeconnect_watcher.client.client import HomeConnectClient, HomeConnectSimulationClient
from homeconnect_watcher.exporter.base import BaseExporter
from homeconnect_watcher.utils import Metrics

load_dotenv()


async def loop(client: HomeConnectClient, exporters: list[BaseExporter], metrics: Metrics | None = None):
    if isinstance(client, HomeConnectSimulationClient):
        await client.authenticate("username", "password")

    if len(exporters) == 0:
        raise ValueError("No exporters defined.")
    with ExitStack() as stack:
        for exporter in exporters:
            stack.enter_context(exporter)

        if metrics is not None:
            for appliance in await client.appliances:
                metrics.init_labels(appliance_id=appliance.appliance_id)

        async for event in client.watch():
            for exporter in exporters:
                exporter.export(event)
