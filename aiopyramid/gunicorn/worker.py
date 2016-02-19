import asyncio
import time
import io
import datetime
import os

from gunicorn.workers.gaiohttp import AiohttpWorker
from aiohttp.wsgi import WSGIServerHttpProtocol

from aiopyramid.helpers import (
    spawn_greenlet,
    spawn_greenlet_on_scope_error,
    synchronize,
)


def atoms(resp, req, environ, request_time):
    """ Gets atoms for log formating.
    """
    status = str(resp.status)
    atoms = {
        'h': environ.get('REMOTE_ADDR', '-'),
        'l': '-',
        'u': '-',
        't': time.strftime('[%d/%b/%Y:%H:%M:%S %z]'),
        'r': "%s %s %s" % (
            environ['REQUEST_METHOD'],
            environ['RAW_URI'],
            environ["SERVER_PROTOCOL"]),
        's': status,
        'm': environ.get('REQUEST_METHOD'),
        'U': environ.get('PATH_INFO'),
        'q': environ.get('QUERY_STRING'),
        'H': environ.get('SERVER_PROTOCOL'),
        'b': '-',
        'B': None,
        'f': environ.get('HTTP_REFERER', '-'),
        'a': environ.get('HTTP_USER_AGENT', '-'),
        'T': request_time.seconds,
        'D': (request_time.seconds * 1000000) + request_time.microseconds,
        'L': "%d.%06d" % (request_time.seconds, request_time.microseconds),
        'p': "<%s>" % os.getpid()
    }

    # add request headers
    if hasattr(req, 'headers'):
        req_headers = req.headers
    else:
        req_headers = req

    atoms.update(
        dict([("{%s}i" % k.lower(), v) for k, v in req_headers.items()]))

    # add response headers
    atoms.update(dict(
        [("{%s}o" % k.lower(), v) for k, v in resp.headers.items()]))

    return atoms


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

    def log_access(self, request, environ, response, time):
        catoms = atoms(
            response,
            request,
            environ,
            datetime.timedelta(0, 0, time))
        safe_atoms = self.logger.atoms_wrapper_class(catoms)
        self.logger.access_log.info(
            self.logger.cfg.access_log_format % safe_atoms)


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
