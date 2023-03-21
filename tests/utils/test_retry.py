from pytest import mark, raises

from homeconnect_watcher.utils.retry import retry


@mark.asyncio
async def test_retry():
    n_tries = 0

    @retry(3, exceptions=ValueError)
    async def fct():
        nonlocal n_tries
        n_tries += 1
        if n_tries == 1:
            raise ValueError

    await fct()
    assert n_tries == 2


@mark.asyncio
async def test_retry_fails():
    n_tries = 0

    @retry(3, exceptions=ValueError)
    async def fct():
        nonlocal n_tries
        n_tries += 1
        raise ValueError

    with raises(ValueError):
        await fct()
    assert n_tries == 3
