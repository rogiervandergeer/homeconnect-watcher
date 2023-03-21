from asyncio import sleep
from logging import getLogger
from typing import Any, Callable, Type, TypeVar

logger = getLogger(__name__)
F = TypeVar(name="F", bound=Callable[..., Any])


def retry(n_tries: int, delay: float = 1, exceptions: Type[Exception] | tuple[Type[Exception]] = Exception):
    def func_wrapper(f: F) -> F:
        async def wrapper(*args, **kwargs):
            for i_try in range(n_tries):
                try:
                    return await f(*args, **kwargs)
                except exceptions as exc:
                    logger.debug(f"Function {f.__name__} failed with exception {exc} in try {i_try} out of {n_tries}.")
                    if i_try + 1 == n_tries:
                        raise exc
                    else:
                        await sleep(delay)

        return wrapper

    return func_wrapper
