import asyncio
from functools import wraps


def retry(max_attempts: int = 5, delay: float = 1, exceptions=(asyncio.TimeoutError,)):
    """ """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = ValueError("No exceptions were raised")
            for _ in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper

    return decorator
