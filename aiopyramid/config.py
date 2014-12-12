"""
This module provides view mappers for running views in asyncio.
"""
import asyncio

from pyramid.config.views import DefaultViewMapper
from pyramid.exceptions import ConfigurationError

from .helpers import synchronize, is_generator


class AsyncioMapperBase(DefaultViewMapper):
    """
    Base class for asyncio view mappers.
    """

    def run_in_coroutine_view(self, view):

        return synchronize(view)

    def run_in_executor_view(self, view):

        synchronizer = synchronize(strict=False)

        def executor_view(context, request):
            try:
                # since we are running in a new thread,
                # remove the old wsgi.file_wrapper for uwsgi
                request.environ.pop('wsgi.file_wrapper')
            finally:
                exe = synchronizer(asyncio.get_event_loop().run_in_executor)
                return exe(None, view, context, request)

        return executor_view


class CoroutineMapper(AsyncioMapperBase):

    def __call__(self, view):
        original = view
        view = super().__call__(view)

        if is_generator(original) or is_generator(
            getattr(original, '__call__', None)
        ):
            view = asyncio.coroutine(view)
        elif not asyncio.iscoroutinefunction(original):
            raise ConfigurationError(
                'Non-coroutine {} mapped to coroutine.'.format(original)
            )

        return self.run_in_coroutine_view(view)


class ExecutorMapper(AsyncioMapperBase):

    def __call__(self, view):
        if asyncio.iscoroutinefunction(view) or asyncio.iscoroutinefunction(
            getattr(view, '__call__', None)
        ):
            raise ConfigurationError(
                'Coroutine {} mapped to executor.'.format(view)
            )
        view = super().__call__(view)
        return self.run_in_executor_view(view)


class CoroutineOrExecutorMapper(AsyncioMapperBase):

    def __call__(self, view):
        original = view
        view = super().__call__(view)

        if (
            asyncio.iscoroutinefunction(original) or
            is_generator(original) or
            is_generator(
                getattr(original, '__call__', None)
            )
        ):
            view = asyncio.coroutine(view)
            return self.run_in_coroutine_view(view)
        else:
            return self.run_in_executor_view(view)

