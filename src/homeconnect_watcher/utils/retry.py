from asyncio import sleep
from logging import getLogger
from typing import Awaitable, Callable, ParamSpec, TypeVar

logger = getLogger(__name__)
P = ParamSpec("P")
R = TypeVar("R")


def retry(n_tries: int, delay: float = 1, exceptions: type[Exception] | tuple[type[Exception], ...] = Exception):
    def func_wrapper(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for i_try in range(n_tries):
                try:
                    return await f(*args, **kwargs)
                except exceptions as exc:
                    name = getattr(f, "__name__", repr(f))
                    logger.debug(f"Function {name} failed with exception {exc} in try {i_try} out of {n_tries}.")
                    if i_try + 1 == n_tries:
                        raise exc
                    else:
                        await sleep(delay)
            raise RuntimeError(f"retry requires n_tries >= 1, got {n_tries}.")

        return wrapper

    return func_wrapper
