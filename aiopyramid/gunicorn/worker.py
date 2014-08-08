import asyncio
import time
import io

from gunicorn.workers.gaiohttp import AiohttpWorker
from aiohttp.wsgi import WSGIServerHttpProtocol

from aiopyramid.helpers import spawn_greenlet


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

        environ = self.create_wsgi_environ(message, payload)
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
            wsgi, loop=self.loop,
            log=self.log,
            debug=self.cfg.debug,
            keep_alive=self.cfg.keepalive,
            access_log=self.log.access_log,
            access_log_format=self.cfg.access_log_format)
        return self.wrap_protocol(proto)
