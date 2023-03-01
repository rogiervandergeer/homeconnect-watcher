from asyncio import TimeoutError, wait_for
from logging import getLogger
from typing import AsyncIterable

from homeconnect_watcher.exceptions import HomeConnectTimeout


logger = getLogger(__name__)


async def timeout(iterable: AsyncIterable, duration: int) -> AsyncIterable:
    try:
        iterator = iterable.__aiter__()
        while True:
            yield await wait_for(iterator.__anext__(), timeout=duration)
    except TimeoutError:
        logger.error("Timeout on stream.")
        raise HomeConnectTimeout()
    except StopAsyncIteration:
        return
