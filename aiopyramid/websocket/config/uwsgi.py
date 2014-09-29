import inspect
import asyncio

import greenlet

from aiopyramid.config import AsyncioMapperBase
from aiopyramid.helpers import run_in_greenlet
from aiopyramid.websocket.exceptions import WebsocketClosed

try:
    import uwsgi
except ImportError:
    pass


def uwsgi_recv_msg(g):
    g.has_message = True
    g.switch()


class UWSGIWebsocket:

    def __init__(self, back, q_in, q_out):
        self.back = back
        self.q_in = q_in
        self.q_out = q_out
        self.open = True

    @asyncio.coroutine
    def recv(self):
        return (yield from self.q_in.get())

    @asyncio.coroutine
    def send(self, message):
        yield from self.q_out.put(message)
        self.back.switch()

    @asyncio.coroutine
    def close(self):
        yield from self.q_in.put(None)
        self.back.throw(WebsocketClosed)


class UWSGIWebsocketMapper(AsyncioMapperBase):

    def launch_websocket_view(self, view):

        def websocket_view(context, request):
            uwsgi.websocket_handshake()
            this = greenlet.getcurrent()
            this.has_message = False
            q_in = asyncio.Queue()
            q_out = asyncio.Queue()

            # make socket proxy
            if inspect.isclass(view):
                view_callable = view(context, request)
            else:
                view_callable = view
            ws = UWSGIWebsocket(this, q_in, q_out)

            # start monitoring websocket events
            asyncio.get_event_loop().add_reader(
                uwsgi.connection_fd(),
                uwsgi_recv_msg,
                this
            )

            # NOTE: don't use synchronize because we aren't waiting
            # for this future, instead we are using the reader to return
            # to the child greenlet.

            future = asyncio.Future()
            asyncio.async(
                run_in_greenlet(this, future, view_callable, ws)
            )

            # switch to open
            this.parent.switch()

            while True:
                if future.done():
                    raise WebsocketClosed

                # message in
                if this.has_message:
                    this.has_message = False
                    try:
                        msg = uwsgi.websocket_recv_nb()
                    except OSError:
                        msg = None

                    if msg or msg is None:
                        q_in.put_nowait(msg)

                # message out
                if not q_out.empty():
                    msg = q_out.get_nowait()
                    try:
                        uwsgi.websocket_send(msg)
                    except OSError:
                        q_in.put_nowait(None)

                this.parent.switch()

        return websocket_view

    def __call__(self, view):
        """ Accepts a view_callable class. """
        return self.launch_websocket_view(view)
