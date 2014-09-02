
from .exceptions import WebsocketClosed


def ignore_websocket_closed(app):
    """ Wrapper for ignoring closed websockets. """

    def _call_app_ignoring_ws_closed(environ, start_response):
        try:
            return app(environ, start_response)
        except WebsocketClosed:
            return ('')
    return _call_app_ignoring_ws_closed
