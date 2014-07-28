"""
Run pyramid app using asyncio
"""

from .config import add_coroutine_view


def includeme(config):
    config.add_directive('add_coroutine_view', add_coroutine_view)
