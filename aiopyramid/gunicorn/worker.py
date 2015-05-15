import asyncio
import time
import io

from gunicorn.workers.gaiohttp import AiohttpWorker
from aiohttp.wsgi import WSGIServerHttpProtocol

from aiopyramid.helpers import (
    spawn_greenlet,
    spawn_greenlet_on_scope_error,
    synchronize,
)


class AiopyramidHttpServerProtocol(WSGIServerHttpProtocol):

    @asyncio.coroutine
    def handle_request(self, message, payload):
        """ Patched from aiohttp. """
        now = time.time()

        if self.readpayload:
            wsgiinput = io.BytesIO()
            wsgiinput.write((yield from payload.read()))
            wsgiinput.seek(0)
            payload = wsgiinput
        else:
            # allow read to be called from a synchronous context
            payload.read = synchronize(payload.read)
            payload.read = spawn_greenlet_on_scope_error(payload.read)

        environ = self.create_wsgi_environ(message, payload)
        # add a reference to this for switching protocols
        environ['async.protocol'] = self

        response = self.create_wsgi_response(message)

        riter = yield from spawn_greenlet(
            self.wsgi,
            environ,
            response.start_response
        )

        resp = response.response
        try:
            for item in riter:
                if isinstance(item, asyncio.Future):
                    item = yield from item
                yield from resp.write(item)

            yield from resp.write_eof()
        finally:
            if hasattr(riter, 'close'):
                riter.close()

        if resp.keep_alive():
            self.keep_alive(True)

        self.log_access(
            message, environ, response.response, time.time() - now)


class AsyncGunicornWorker(AiohttpWorker):

    def factory(self, wsgi, *args):
        proto = AiopyramidHttpServerProtocol(
            wsgi,
            loop=self.loop,
            readpayload=True,
            log=self.log,
            keep_alive=self.cfg.keepalive,
            access_log=self.log.access_log,
            access_log_format=self.cfg.access_log_format)
        return self.wrap_protocol(proto)
