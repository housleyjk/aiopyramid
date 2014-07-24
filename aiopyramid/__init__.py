"""
Run pyramid app using asyncio
"""

from .config import add_coroutine_view, make_asyncio_app


def includeme(config):
    config.add_directive('add_coroutine_view', add_coroutine_view)
    config.add_directive('make_asyncio_app', make_asyncio_app)
