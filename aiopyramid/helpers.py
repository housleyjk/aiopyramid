import asyncio
import inspect
import functools

import greenlet
from pyramid.exceptions import ConfigurationError


def is_generator(func):
    """ Tests whether `func` is capable of becoming an `asyncio.coroutine`. """
    return (
        inspect.isgeneratorfunction(func) or
        isinstance(func, asyncio.Future) or
        inspect.isgenerator(func)
    )


@asyncio.coroutine
def spawn_greenlet(func, *args, **kwargs):
    """
    Spawns a new greenlet and waits on any `asyncio.Future` objects returned.

    This is used by the Gunicorn worker to proxy a greenlet within an `asyncio`
    event loop.
    """

    g = greenlet.greenlet(func)
    result = g.switch(*args, **kwargs)
    while True:
        if isinstance(result, asyncio.Future):
            result = yield from result
        else:
            break
    return result


@asyncio.coroutine
def run_in_greenlet(back, future, func, *args, **kwargs):
    """
    Wait for :term:`coroutine` func and switch back to the request greenlet
    setting any result in the future or an Exception where approrpiate.

    func is often a :term:`view callable`
    """
    try:
        result = yield from func(*args)
    except Exception as ex:
        future.set_exception(ex)
    else:
        future.set_result(result)
    finally:
        return back.switch()


def synchronize(coroutine_func, safe=True):
    """
    Decorator for transforming an async coroutine function into a regular
    function relying on the `aiopyramid` architecture to schedule
    the coroutine and obtain the result.
    """

    if safe and not asyncio.iscoroutinefunction(coroutine_func):
        raise ConfigurationError(
            'Attempted to synchronize a non-coroutine.'.format(coroutine_func)
        )

    @functools.wraps(coroutine_func)
    def _wrapped_coroutine(*args, **kwargs):

        this = greenlet.getcurrent()
        future = asyncio.Future()
        sub_task = asyncio.async(
            run_in_greenlet(this, future, coroutine_func, *args, **kwargs)
        )
        while not future.done():
            this.parent.switch(sub_task)
        return future.result()

    return _wrapped_coroutine
