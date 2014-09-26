import asyncio


class WebsocketConnectionView:
    """ :term:`view_callable` for websocket connections. """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @asyncio.coroutine
    def __call__(self, ws):
        print('called ws callable')
        self.ws = ws
        print(self.ws)
        yield from self.on_open()
        print('opened')
        while True:
            message = yield from self.ws.recv()
            print('got', message)
            if message is None:
                print('closing')
                yield from self.on_close()
                print('breaking')
                break
            print('firing on message')
            yield from self.on_message(message)

    @asyncio.coroutine
    def send(self, message):
        print('sending', message)
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
