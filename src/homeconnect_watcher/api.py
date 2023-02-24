from asyncio import create_task, Task
from datetime import timedelta
from logging import getLogger
from os import environ
from pathlib import Path
from time import time
from typing import Optional, Type

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import Response, RedirectResponse

from homeconnect_watcher.client.client import HomeConnectClient, HomeConnectSimulationClient
from homeconnect_watcher.exceptions import HomeConnectRequestError
from homeconnect_watcher.exporter.file import FileExporter

load_dotenv()


def define_endpoints(simulation: bool):
    logger = getLogger(__name__)

    api = FastAPI()
    client: HomeConnectClient | None = None
    task: Task | None = None

    @api.on_event("startup")
    async def startup():
        nonlocal client, task
        if task is not None:
            task.cancel()
        if client is not None:
            await client.client.aclose()
        client = (HomeConnectSimulationClient if simulation else HomeConnectClient)()
        if simulation:
            await client.authenticate("user", "password")
        task = create_task(loop(client))

    @api.on_event("shutdown")
    async def shutdown():
        await client.client.aclose()

    @api.get("/authorize")
    async def authorize():
        return RedirectResponse(client.authorization_url)

    @api.get("/code")
    async def code(code: str):
        url = f"{client.client.redirect_uri}/?code={code}&grant_type=authorization_code"
        await client.authorize(url)
        await startup()
        return Response("OK", 200)

    @api.get("/health")
    async def health():
        if task is None:
            logger.warning("No task running.")
            return Response("No task running.", status_code=404)
        elif task.done():
            exc = task.exception()
            if "invalid_token" in str(exc):
                logger.warning("Unauthorized. Please authorize.")
                return Response("Unauthorized. Please authorize.")
            logger.warning("Task finished.", exc_info=exc)
            return Response(f"Task finished: {exc}", status_code=500)
        else:
            # TODO: last events
            age = 0  # int(time() - client.last_event)
            if age > 240:
                logger.warning(f"No recent events. Last event {age} seconds old.")
                return Response(f"No recent events. Last event {age} seconds old.", status_code=500)
            else:
                return Response(f"OK. Last event {age} seconds old.", status_code=200)

    return api


async def loop(client: HomeConnectClient):
    path = Path(environ["HOMECONNECT_PATH"]) if "HOMECONNECT_PATH" in environ else Path()
    exporter = FileExporter(path, flush_interval=timedelta(seconds=30))
    with exporter:
        async for event in client.watch():
            exporter.export(event)
