"""
Get pyramid working with asyncio
"""
import asyncio
import importlib

from pyramid.settings import aslist

from .config import add_coroutine_view, make_asyncio_app, add_exit_handler


def includeme(config):
    config.add_directive('add_coroutine_view', add_coroutine_view)
    config.add_directive('make_asyncio_app', make_asyncio_app)
    config.add_directive('add_exit_handler', add_exit_handler)
