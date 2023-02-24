from asyncio import sleep

from pytest import mark, raises

from homeconnect_watcher.exceptions import HomeConnectTimeout
from homeconnect_watcher.utils.timeout import timeout


@mark.asyncio
async def test_no_timeout():
    async def iterable():
        for i in range(10):
            yield i

    async for _ in timeout(iterable(), duration=1):
        pass


@mark.asyncio
async def test_timeout():
    async def iterable():
        for i in range(10):
            await sleep(i)
            yield i

    with raises(HomeConnectTimeout):
        async for _ in timeout(iterable(), duration=1):
            pass
