from asyncio import run as async_run
from logging import basicConfig, INFO

from fastapi import FastAPI
from fastapi.responses import Response
from typer import Typer
from uvicorn import run

from homeconnect_watcher.api import loop
from homeconnect_watcher.client.client import HomeConnectSimulationClient, HomeConnectClient

app = Typer()
basicConfig(level=INFO)


@app.command()
def authorize():
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
def watch(simulation: bool = False):
    client = (HomeConnectSimulationClient if simulation else HomeConnectClient)()
    async_run(loop(client))
