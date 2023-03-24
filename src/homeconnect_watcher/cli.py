from asyncio import run as async_run
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import Response
from typer import Argument, Typer
from uvicorn import run

from homeconnect_watcher.api import loop
from homeconnect_watcher.client.client import HomeConnectSimulationClient, HomeConnectClient
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
):
    initialize_logging(level=log_level)
    metrics = Metrics(port=metrics_port) if metrics_port else None
    client = (HomeConnectSimulationClient if simulation else HomeConnectClient)(metrics=metrics)
    async_run(loop(client, flush_interval=flush_interval))
