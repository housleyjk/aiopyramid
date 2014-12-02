"""
Run pyramid app using asyncio
"""

from .config import CoroutineOrExecutorMapper


def includeme(config):
    """
    Setup the basic configuration to run :ref:`Pyramid <pyramid:index>`
    with :mod:`asyncio`.
    """

    config.set_view_mapper(CoroutineOrExecutorMapper)
