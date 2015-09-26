"""
The aiopyramid.tweens module is deprecated. See example in the docs:
http://aiopyramid.readthedocs.org/en/latest/features.html#tweens.
"""

import asyncio
import warnings

from .helpers import synchronize

warnings.warn(__doc__, DeprecationWarning)


def coroutine_logger_tween_factory(handler, registry):
    """
    Example of an asynchronous tween that delegates a synchronous function to
    a child thread. This tween asynchronously logs all requests and responses.
    """

    # We use the synchronize decorator because we will call this
    # coroutine from a normal python context
    @synchronize
    # this is a coroutine
    @asyncio.coroutine
    def _async_print(content):
        # print doesn't really need to be run in a separate thread
        # but it works for demonstration purposes

        yield from asyncio.get_event_loop().run_in_executor(
            None,
            print,
            content
        )

    def coroutine_logger_tween(request):
        # The following calls are guaranteed to happen in order but they do not
        # block the event loop

        # print the request on the aio event loop without needing to say yield
        # at this point, other coroutines and requests can be handled
        _async_print(request)

        # get response, this should be done in this greenlet
        # and not as a coroutine because this will call
        # the next tween and subsequently yield if necessary
        response = handler(request)

        # print the response on the aio event loop
        _async_print(request)

        # return response after logging is done
        return response

    return coroutine_logger_tween
