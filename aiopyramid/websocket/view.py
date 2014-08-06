
import asyncio

from .config import UWSGIWebsocketMapper


class WebsocketConnectionView:
    """ :term:`view_callable` for websocket connections. """

    __view_mapper__ = UWSGIWebsocketMapper

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @asyncio.coroutine
    def __call__(self):
        yield from self.on_open()
        while True:
            message = yield from self._sock.recv()
            if message is None:
                yield from self.on_close()
                break
            yield from self.on_message(message)
            yield from self.send(message)

    @asyncio.coroutine
    def send(self, message):
        print('sending ', message)
        yield from self._sock.send(message)

    @asyncio.coroutine
    def on_message(self, message):
        print('got ', message)
        yield from self.send(message)

    @asyncio.coroutine
    def on_open(self):
        print('opening')

    @asyncio.coroutine
    def on_close(self):
        print('closing')
