import asyncio

from aiohttp_wsgi.wsgi import WSGIHandler, ReadBuffer
from aiohttp.worker import GunicornWebWorker
from aiohttp.web import Application, Response, HTTPRequestEntityTooLarge

from aiopyramid.helpers import (
    spawn_greenlet,
)


def _run_application(application, environ):
    # Simple start_response callable.
    def start_response(status, headers, exc_info=None):
        nonlocal response_status, response_reason
        nonlocal response_headers, response_body
        status_code, reason = status.split(None, 1)
        status_code = int(status_code)
        # Start the response.
        response_status = status_code
        response_reason = reason
        response_headers = headers
        del response_body[:]
        return response_body.append
    # Response data.
    response_status = None
    response_reason = None
    response_headers = None
    response_body = []
    # Run the application.
    body_iterable = application(environ, start_response)
    try:
        response_body.extend(body_iterable)
        assert response_status is not None, "application did not call start_response()"  # noqa
        return (
            response_status,
            response_reason,
            response_headers,
            b"".join(response_body),
        )
    finally:
        # Close the body.
        if hasattr(body_iterable, "close"):
            body_iterable.close()


class AiopyramidWSGIHandler(WSGIHandler):

    def _get_environ(self, request, body, content_length):
        environ = super(AiopyramidWSGIHandler, self)._get_environ(
            request,
            body,
            content_length)
        # restore hop headers for websockets
        for header_name in request.headers:
            header_name = header_name.upper()
            if header_name not in ("CONTENT-LENGTH", "CONTENT-TYPE"):
                header_value = ",".join(request.headers.getall(header_name))
                environ["HTTP_" + header_name.replace("-", "_")] = header_value
        return environ

    @asyncio.coroutine
    def handle_request(self, request):
        # Check for body size overflow.
        if (
                request.content_length is not None and
                request.content_length > self._max_request_body_size):
            raise HTTPRequestEntityTooLarge()
        # Buffer the body.
        body_buffer = ReadBuffer(
            self._inbuf_overflow,
            self._max_request_body_size,
            self._loop,
            self._executor)

        try:
            while True:
                block = yield from request.content.readany()
                if not block:
                    break
                yield from body_buffer.write(block)
            # Seek the body.
            body, content_length = yield from body_buffer.get_body()
            # Get the environ.
            environ = self._get_environ(request, body, content_length)
            environ['async.writer'] = request.writer
            environ['async.protocol'] = request.protocol
            status, reason, headers, body = yield from spawn_greenlet(
                _run_application,
                self._application,
                environ,
            )
            # All done!
            return Response(
                status=status,
                reason=reason,
                headers=headers,
                body=body,
            )

        finally:
            yield from body_buffer.close()


class AsyncGunicornWorker(GunicornWebWorker):

    def make_handler(self, app):
        aio_app = Application()
        aio_app.router.add_route(
            "*",
            "/{path_info:.*}",
            AiopyramidWSGIHandler(
                app,
                loop=self.loop,
            ),
        )
        access_log = self.log.access_log if self.cfg.accesslog else None
        return aio_app.make_handler(
            loop=self.loop,
            logger=self.log,
            slow_request_timeout=self.cfg.timeout,
            keepalive_timeout=self.cfg.keepalive,
            access_log=access_log,
            access_log_format=self._get_valid_log_format(
                self.cfg.access_log_format))
