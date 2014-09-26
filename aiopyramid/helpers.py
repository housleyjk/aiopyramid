import asyncio
import inspect
import functools

import greenlet
from pyramid.exceptions import ConfigurationError

from .exceptions import ScopeError


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
        result = yield from func(*args, **kwargs)
    except Exception as ex:
        future.set_exception(ex)
    else:
        future.set_result(result)
    finally:
        return back.switch()


def synchronize(strict=True):
    """
    Decorator for transforming an async coroutine function into a regular
    function relying on the `aiopyramid` architecture to schedule
    the coroutine and obtain the result.

    NOTE: Remeber to use () even when using the defaults.

    @synchronize()
    @asyncio.coroutine
    def my_coroutine():
        pass
    """

    def _wrapper(coroutine_func):
        if strict and not asyncio.iscoroutinefunction(coroutine_func):
            raise ConfigurationError(
                'Attempted to synchronize a non-coroutine {}.'.format(
                    coroutine_func
                )
            )

        @functools.wraps(coroutine_func)
        def _wrapped_coroutine(*args, **kwargs):

            this = greenlet.getcurrent()
            if this.parent is None:
                if strict:
                    raise ScopeError(
                        '''
                        Synchronized coroutine {} called in the parent
                        greenlet.

                        This is most likely because you called the synchronized
                        coroutine inside of another coroutine. You need to
                        yield from the coroutine directly without wrapping
                        it in aiopyramid.helpers.synchronize.

                        If you are calling this coroutine indirectly from
                        a regular function and therefore cannot yield from it,
                        then you need to run the first caller inside a new
                        greenlet using aiopyramid.helpers.spawn_greenlet.
                        '''
                    )
                else:
                    return coroutine_func(*args, **kwargs)
            else:
                future = asyncio.Future()
                sub_task = asyncio.async(
                    run_in_greenlet(
                        this,
                        future,
                        coroutine_func,
                        *args,
                        **kwargs
                    )
                )
                while not future.done():
                    this.parent.switch(sub_task)
                return future.result()

        return _wrapped_coroutine

    return _wrapper
