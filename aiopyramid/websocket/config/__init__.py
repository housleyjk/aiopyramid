__all__ = []

try:
    from .uwsgi import *
    __all__.append('UWSGIWebsocketMapper')
except ImportError:
    pass

try:
    from .gunicorn import *
    __all__.append('WebsocketMapper')
except ImportError:
    pass
