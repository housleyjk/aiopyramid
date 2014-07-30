"""
Run pyramid app using asyncio
"""

from .config import CoroutineOrExecutorMapper


def includeme(config):
    config.set_view_mapper(CoroutineOrExecutorMapper)
