from asyncio import run as async_run
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI
from fastapi.responses import Response
from typer import Argument, Typer
from uvicorn import run

from homeconnect_watcher.api import loop
from homeconnect_watcher.client.client import HomeConnectSimulationClient, HomeConnectClient
from homeconnect_watcher.db import clean_schema, create_views, load_views
from homeconnect_watcher.exporter.file import FileExporter
from homeconnect_watcher.exporter.postgres import PGExporter
from homeconnect_watcher.read import read_events
from homeconnect_watcher.utils import LogLevel, Metrics, initialize_logging

app = Typer()


@app.command()
def authorize(
    log_level: LogLevel = Argument(LogLevel.INFO, envvar="HCW_LOGLEVEL"),
):
    initialize_logging(level=log_level)
    client = HomeConnectClient()

    api = FastAPI()

    @api.get("/code")
    async def code(code: str):
        url = f"{client.client.redirect_uri}/?code={code}&grant_type=authorization_code"
        await client.authorize(url)
        print("Authorized.")
        return Response("OK", 200)

    print("Visit the following URL:")
    print(client.authorization_url)
    run(api, host="0.0.0.0", port=8000)


@app.command()
def watch(
    simulation: bool = False,
    flush_interval: int = Argument(300, envvar="HCW_FLUSH_INTERVAL"),
    log_level: LogLevel = Argument(LogLevel.INFO, envvar="HCW_LOGLEVEL"),
    metrics_port: Optional[int] = Argument(None, envvar="HCW_METRICS_PORT"),
    log_path: Annotated[Optional[str], Argument(envvar="HOMECONNECT_PATH")] = None,
    db_uri: Annotated[Optional[str], Argument(envvar="HCW_DB_URI")] = None,
):
    initialize_logging(level=log_level)
    metrics = Metrics(port=metrics_port) if metrics_port else None
    client = (HomeConnectSimulationClient if simulation else HomeConnectClient)(metrics=metrics)
    exporters = []
    if log_path is not None:
        exporters.append(FileExporter(path=Path(log_path), flush_interval=timedelta(seconds=flush_interval)))
    if db_uri is not None:
        exporters.append(PGExporter(connection_string=db_uri))
    async_run(loop(client, exporters))


@app.command()
def load(
    db_uri: Annotated[Optional[str], Argument(envvar="HCW_DB_URI")] = None,
    log_path: Annotated[Optional[str], Argument(envvar="HOMECONNECT_PATH")] = None,
    clean: bool = False,
):
    with PGExporter(connection_string=db_uri) as exporter:
        if clean:
            clean_schema(connection=exporter.connection)
        for events in read_events(Path(log_path)):
            exporter.bulk_export(events)


@app.command()
def views(
    db_uri: Annotated[Optional[str], Argument(envvar="HCW_DB_URI")] = None,
):
    with PGExporter(connection_string=db_uri) as exporter:
        create_views(exporter.connection, drop=True, views=load_views())
