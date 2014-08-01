"""
Helper for tests taken from pyramid_asyncio
"""

import asyncio


def async_test(func):

    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(func)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    return wrapper
