"""
This module provides view mappers for running views in asyncio.
"""
import asyncio
import inspect

import greenlet
from pyramid.config.views import DefaultViewMapper
from pyramid.exceptions import ConfigurationError


@asyncio.coroutine
def run_in_greenlet(back, future, func, *args):
    response = yield from func(*args)
    future.set_result(response)
    back.switch()


def _is_generator(func):
    return (
        inspect.isgeneratorfunction(func) or
        isinstance(func, asyncio.Future) or
        inspect.isgenerator(func)
    )


class AsyncioMapperBase(DefaultViewMapper):
    """
    Base class for asyncio view mappers.
    """

    def run_in_coroutine_view(self, view):

        def coroutine_view(*args):
            this = greenlet.getcurrent()
            future = asyncio.Future()
            asyncio.async(run_in_greenlet(this, future, view, *args))
            this.parent.switch()
            return future.result()

        return coroutine_view

    def run_in_executor_view(self, view):

        def executor_view(*args):
            this = greenlet.getcurrent()
            future = asyncio.Future()
            asyncio.async(
                run_in_greenlet(
                    this,
                    future,
                    asyncio.get_event_loop().run_in_executor,
                    None,
                    view,
                    *args
                )
            )
            this.parent.switch()
            return future.result()
        return executor_view


class CoroutineMapper(AsyncioMapperBase):

    def __call__(self, view):
        if not asyncio.iscoroutinefunction(view) and _is_generator(view):
            view = asyncio.coroutine(view)
        else:
            raise ConfigurationError('Non-coroutine {} mapped to coroutine.'.format(view))

        view = super().__call__(view)
        return self.run_in_coroutine_view(view)


class ExecutorMapper(AsyncioMapperBase):

    def __call__(self, view):
        if asyncio.iscoroutinefunction(view) or _is_generator(view):
            raise ConfigurationError('Coroutine {} mapped to executor.'.format(view))
        view = super().__call__(view)
        return self.run_in_executor_view(view)


class CoroutineOrExecutorMapper(AsyncioMapperBase):

    def __call__(self, view):

        if asyncio.iscoroutinefunction(view):
            wrapper = self.run_in_coroutine_view
        elif _is_generator(view):
            view = asyncio.coroutine(view)
            wrapper = self.run_in_coroutine_view
        else:
            wrapper = self.run_in_executor_view

        view = super().__call__(view)
        return wrapper(view)
