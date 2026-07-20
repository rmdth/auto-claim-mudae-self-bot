from asyncio import TimeoutError, sleep
from functools import wraps

from src.ui import update_log_debug


def retry(max_attempts: int = 5, delay: float = 1, exceptions=(TimeoutError,)):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for _ in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    update_log_debug(f"Retry exception: {e}")
                    await sleep(delay)

            if last_exception:
                raise last_exception
            pass

        return wrapper

    return decorator
