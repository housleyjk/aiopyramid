import asyncio
import inspect
import functools
import logging

import greenlet
from pyramid.exceptions import ConfigurationError

from .exceptions import ScopeError

SCOPE_ERROR_MESSAGE = '''
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

log = logging.getLogger(__name__)


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


def synchronize(*args, strict=True):
    """
    Decorator for transforming an async coroutine function into a regular
    function relying on the `aiopyramid` architecture to schedule
    the coroutine and obtain the result.

    .. code-block:: python

        @synchronize
        @asyncio.coroutine
        def my_coroutine():
            ... code that yields
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
                        SCOPE_ERROR_MESSAGE.format(coroutine_func)
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

    try:
        coroutine_func = args[0]
        return _wrapper(coroutine_func)
    except IndexError:
        return _wrapper


def spawn_greenlet_on_scope_error(func):
    """
    Wraps a callable handling any
    :class:`ScopeErrors <~aiopyramid.exceptions.ScopeError>` that may
    occur because the callable is called from inside of a :term:`coroutine`.

    If no :class:`~aiopyramid.exceptions.ScopeError` occurs, the callable is
    executed normally and return arguments are passed through, otherwise, when
    a :class:`~aiopyramid.exceptions.ScopeError` does occur, a coroutine to
    retrieve the result of the callable is returned instead.
    """

    @functools.wraps(func)
    def _run_or_return_future(*args, **kwargs):
        this = greenlet.getcurrent()
        # Check if we should see a ScopeError
        if this.parent is None:
            return spawn_greenlet(func, *args, **kwargs)
        else:
            try:
                return func(*args, **kwargs)
            except ScopeError:
                # ScopeError generated in multiple levels of indirection
                log.warn('Unexpected ScopeError encountered.')
                return spawn_greenlet(func, *args, **kwargs)

    return _run_or_return_future


def use_executor(*args, executor=None):
    """
    A decorator for running a callback in the executor.

    This is useful to provide a declarative style for converting some
    thread-based code to a :term:`coroutine`. It creates a :term:`coroutine`
    by running the wrapped code in a separate thread.

    """
    def _wrapper(callback):
        @functools.wraps(callback)
        @asyncio.coroutine
        def _wrapped_function(*args, **kwargs):
            loop = asyncio.get_event_loop()
            r = yield from loop.run_in_executor(
                executor,
                functools.partial(
                    callback,
                    *args,
                    **kwargs
                )
            )
            return r
        return _wrapped_function

    try:
        func = args[0]
        return _wrapper(func)
    except IndexError:
        return _wrapper
