Websockets
==========

``Aiopyramid`` provides additional view mappers for handling websocket connections with either
`gunicorn`_ or `uWSGI`_. Websockets with `gunicorn`_ it uses the `websockets`_ library whereas
`uWSGI`_ has native :term:`websocket` support. In either case, the interface is the same.

A function :term:`view callable` for a :term:`websocket` connection follows this pattern:

.. code-block:: python

    @view_config(mapper=<WebsocketMapper>)
    def websocket_callable(ws):
        # do stuff with ws


The ``ws`` argument passed to the callable has three methods for communicating with the :term:`websocket`
:meth:`recv`, :meth:`send`, and :meth:`close` methods, which correspond to similar methods in the `websockets`_ library.
A :term:`websocket` connection that echoes all messages using `gunicorn`_  would be:

.. code-block:: python

    from pyramid.view import view_config
    from aiopyramid.websocket.config import WebsocketMapper

    @view_config(route_name="ws", mapper=WebsocketMapper)
    def echo(ws):
        while True:
            message = yield from ws.recv()
            if message is None:
                break
            yield from ws.send(message)

``Aiopyramid`` also provides a :term:`view callable` class :class:`~aiopyramid.websocket.view.WebsocketConnectionView`
that has :meth:`~aiopyramid.websocket.view.WebsocketConnectionView.on_message`,
:meth:`~aiopyramid.websocket.view.WebsocketConnectionView.on_open`,
and :meth:`~aiopyramid.websocket.view.WebsocketConnectionView.on_close` callbacks.
Class-based websocket views also have a :meth:`~aiopyramid.websocket.view.WebsocketConnectionView.send` convenience method,
otherwise the underyling ``ws`` may be accessed as :attr:`self.ws`.
Simply extend :class:`~aiopyramid.websocket.view.WebsocketConnectionView`
specifying the correct :term:`view mapper` for your server either via the :attr:`__view_mapper__` attribute or the
:func:`view_config <pyramid:pyramid.view.view_config>` decorator. The above example could be rewritten in a larger project, this time using `uWSGI`_,
as follows:

.. code-block:: python

    from pyramid.view import view_config
    from aiopyramid.websocket.view import WebsocketConnectionView
    from aiopyramid.websocket.config import UWSGIWebsocketMapper

    from myproject.resources import MyWebsocketContext

    class MyWebsocket(WebsocketConnectionView):
        __view_mapper__ = UWSGIWebsocketMapper


    @view_config(context=MyWebsocketContext)
    class EchoWebsocket(MyWebsocket):

        def on_message(self, message):
            yield from self.send(message)


uWSGI Special Note
..................

``Aiopyramid`` uses a special :class:`~aiopyramid.websocket.exceptions.WebsocketClosed` exception
to disconnect a :term:`greenlet` after a :term:`websocket`
has been closed. This exception will be visible in log ouput when using `uWSGI`_. In order to squelch this
message, wrap the wsgi application in the :func:`~aiopyramid.websocket.helpers.ignore_websocket_closed` middleware
in your application's constructor like so:

.. code-block:: python

    from aiopyramid.websocket.helpers import ignore_websocket_closed

    ...
    app = config.make_wsgi_app()
    return ignore_websocket_closed(app)


.. _gunicorn: http://gunicorn.org
.. _uWSGI: https://github.com/unbit/uwsgi
.. _websockets: http://aaugustin.github.io/websockets/
