import asyncio
import inspect

import greenlet


def is_generator(func):
    return (
        inspect.isgeneratorfunction(func) or
        isinstance(func, asyncio.Future) or
        inspect.isgenerator(func)
    )


@asyncio.coroutine
def spawn_greenlet(func, *args):
    g = greenlet.greenlet(func)
    result = g.switch(*args)
    while True:
        if not result:
            raise ValueError(
                'You must pass a asyncio.Future or an interator '
                'to the parent greenlet when using gunicorn'
            )
        if isinstance(result, asyncio.Future):
            result = yield from result
        else:
            break

    return result


@asyncio.coroutine
def run_in_greenlet(back, future, func, *args):
    try:
        result = yield from func(*args)
    except Exception as ex:
        future.set_exception(ex)
    else:
        future.set_result(result)
    finally:
        return back.switch()
