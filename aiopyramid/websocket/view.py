import asyncio


class WebsocketConnectionView:
    """ :term:`view callable` for websocket connections. """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @asyncio.coroutine
    def __call__(self, ws):
        self.ws = ws
        yield from self.on_open()
        while True:
            message = yield from self.ws.recv()
            if message is None:
                yield from self.on_close()
                break
            yield from self.on_message(message)

    @asyncio.coroutine
    def send(self, message):
        yield from self.ws.send(message)

    @asyncio.coroutine
    def on_message(self, message):
        """
        Callback called when a message is received.
        Default is a noop.
        """
        pass

    @asyncio.coroutine
    def on_open(self):
        """
        Callback called when the connection is first established.
        Default is a noop.
        """

    @asyncio.coroutine
    def on_close(self):
        """
        Callback called when the connection is closed.
        Default is a noop.
        """
        pass
