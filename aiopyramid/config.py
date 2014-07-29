"""
This code is a big copy/paste of code from pyramid and change the
view in order to handle it as a coroutine
"""
import asyncio
import inspect

import greenlet
from pyramid.config.views import DefaultViewMapper


@asyncio.coroutine
def run_in_greenlet(back, future, func, *args):
    response = yield from func(*args)
    future.set_result(response)
    back.switch()


def _is_generator(func):
    return isinstance(func, asyncio.Future) or inspect.isgenerator(func)


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
        view = super().__call__(view)
        if not asyncio.iscoroutinefunction(view) and _is_generator(view):
            view = asyncio.coroutine(view)
            view = self.run_in_coroutine_view(view)
        return view


class ExecutorMapper(AsyncioMapperBase):

    def __call__(self, view):
        view = super().__call__(view)
        return self.run_in_executor_view(view)


class CoroutineOrExecutorMapper(AsyncioMapperBase):

    def __call__(self, view):
        view = super().__call__(view)

        if asyncio.iscoroutinefunction(view):
            view = self.run_in_coroutine_view(view)
        elif _is_generator(view):
            view = asyncio.coroutine(view)
            view = self.run_in_coroutine_view(view)
        else:
            view = self.run_in_executor_view(view)
        return view
