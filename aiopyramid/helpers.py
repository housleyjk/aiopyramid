import asyncio
import inspect

import greenlet


def is_generator(func):
    """ Tests whether `func` is capable of becoming an `asyncio.coroutine`. """
    return (
        inspect.isgeneratorfunction(func) or
        isinstance(func, asyncio.Future) or
        inspect.isgenerator(func)
    )


@asyncio.coroutine
def spawn_greenlet(func, *args):
    """
    Spawns a new greenlet and waits on any `asyncio.Future` objects returned.

    This is used by the Gunicorn worker to proxy a greenlet within an `asyncio`
    event loop.
    """
    g = greenlet.greenlet(func)
    result = g.switch(*args)
    while True:
        if isinstance(result, asyncio.Future):
            result = yield from result
        else:
            break
    return result


@asyncio.coroutine
def run_in_greenlet(back, future, func, *args):
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
