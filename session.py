import asyncio
import time
from functools import wraps
import aiohttp
import logging
import requests

logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger(__name__)

def session_manager(async_function):
    @wraps(async_function)
    async def wrapped(*args, **kwargs):
        timeout = aiohttp.ClientTimeout(total=3, connect=3, sock_connect=3, sock_read=3)
        con = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(trust_env=True, timeout=timeout, connector=con)
        try:
            return await async_function(session=session, *args, **kwargs)
        except aiohttp.ClientError as e:
            logger.warning(e)
            pass
        finally:
            await session.close()
    return wrapped


def with_retries(max_tries, retries_sleep_second):
    def wrapper(function):
        @wraps(function)
        @session_manager
        async def async_wrapped(*args, **kwargs):
            tries = 1
            while tries <= max_tries:
                try:
                    return await function(*args, **kwargs)
                except asyncio.exceptions.TimeoutError as e:
                    logger.warning(f"Function: {function.__name__} Caused AiohttpError: {str(e)}, tries: {tries}")
                    tries += 1
                    await asyncio.sleep(retries_sleep_second)
            else:
                logger.warning('重试超上限')
                pass

        @wraps(function)
        def wrapped(*args, **kwargs):
            tries = 1
            while tries <= max_tries:
                try:
                    return function(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Function: {function.__name__} Caused RequestsError: {str(e)}, tries: {tries}")
                    tries += 1
                    time.sleep(retries_sleep_second)
            else:
                raise TimeoutError("Reached aiohttp max tries")

        if asyncio.iscoroutinefunction(function):
            return async_wrapped
        else:
            return wrapped

    return wrapper
