
import asyncio

import greenlet
from aiopyramid.config import AsyncioMapperBase
from aiopyramid.helpers import run_in_greenlet

try:
    import uwsgi
except ImportError:
    pass


def uwsgi_recv_msg(g):
    g.has_message = True
    g.switch()


class UWSGIWebsocket:

    def __init__(self, back, q_in, q_out):
        print('initializing socket')
        self.back = back
        self.q_in = q_in
        self.q_out = q_out

    @asyncio.coroutine
    def recv(self):
        print('in receive')
        print(self.q_in.qsize())
        return (yield from self.q_in.get())

    @asyncio.coroutine
    def send(self, message):
        yield from self.q_out.put(message)
        self.back.switch()


class UWSGIWebsocketMapper(AsyncioMapperBase):

    def launch_websocket_view(self, view):

        def websocket_view(context, request):
            uwsgi.websocket_handshake()
            this = greenlet.getcurrent()
            this.has_message = False
            q_in = asyncio.Queue()
            q_out = asyncio.Queue()

            # make socket proxy
            view._sock = UWSGIWebsocket(this, q_in, q_out)

            # start monitoring websocket events
            asyncio.get_event_loop().add_reader(
                uwsgi.connection_fd(),
                uwsgi_recv_msg,
                this
            )

            # wait for pingback
            this.parent.switch()

            future = asyncio.Future()
            asyncio.async(run_in_greenlet(this, future, view(context, request)))

            while True:
                if this.has_message:
                    this.has_message = False
                    msg = uwsgi.websocket_recv_nb()
                    if msg or msg is None:
                        q_in.put_nowait(msg)
                    if msg is None:
                        break
                if not q_out.empty():
                    msg = q_out.get_nowait()
                    uwsgi.websocket_send(msg)

                this.parent.switch()

        return websocket_view

    def __call__(self, view):
        """ Accepts a view_callable class. """
        return self.launch_websocket_view(view)
