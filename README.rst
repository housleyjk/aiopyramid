Introduction
============

A library for leveraging pyramid infrastructure asynchronously using the new ``asyncio``.

See `Approach`_ for why I made this library.

Since this library is built on relatively new technology, it is not intended for production use.

Getting Started
---------------

``Aiopyramid`` includes a scaffold that creates a "hello world" application,
check it out. The scaffold is designed to work with either `gunicorn`_
via a custom worker or `uWSGI`_ via the `uWSGI asyncio plugin`_.

For example:

::

    pip install aiopyramid gunicorn
    pcreate -s aio_starter <project>
    cd <project>
    python setup.py develop
    pserve development.ini

There is also a ``websocket`` scaffold `aio_websocket` for those who basic tools for setting up
a ``websocket`` server.

Features
========
``Aiopyramid`` provides tools for making web applications with ``pyramid`` and ``aysncio``.
It will not necessarily make your application run faster Instead, it gives you some tools
and patterns to build an application on asynchronous servers.
Bear in mind that you will need to use asynchronous libraries for io where appropriate.

Asynchronous Views
------------------
``Aiopyramid`` provides three view mappers for calling ``view callables``:

    * ``CoroutineOrExecutorMapper`` maps views to coroutines or separate threads
    * ``CoroutineMapper`` maps views to coroutines
    * ``ExecutorMapper`` maps views to separate threads

When you include ``Aiopyramid``,
the default view mapper is replaced with the ``CoroutineOrExecutorMapper``
which detects whether your ``view_callable`` is a coroutine and does a ``yield from`` to
call it asynchronously. If your ``view_callable`` is not a coroutine, it will run it in a
separate thread to avoid blocking the thread with the main loop. ``Asyncio`` is not thread-safe,
so you will need to guarantee that either in memory resources are not shared between ``view callables``
running in the executor or that such resources are synchronized.

This means that you should not need to change existing views. Also,
it is possible to restore the default view mapper, but note that this will mean that
coroutine views that do not specify ``CoroutineMapper`` as their view mapper will fail.

Asynchronous Tweens
-------------------
``Pyramid`` allows you to write `tweens` which wrap the request/response chain. Most
existing `tweens` expect those `tweens` above and below them to run synchronously. Therefore,
if you have a tween that needs to run asynchronously (e.g. it looks up some data from a
database for each request), then you will need to write that `tween` so that it can wait
without other `tweens` needing explicitly to ``yield from`` it. An example of this pattern
is provided in ``aiopyramid.tweens``.

Asynchronous Traversal
----------------------
When using ``pyramid``'s traversal view lookup, it is often the case that you will want to
make some io calls to a database or storage when traversing via `__getitem__`. ``Aiopyramid``
provides a custom traverser that allows for `__getitem__` to be an ``asyncio`` coroutine. To
use the traverser simply follow the `pyramid documentation <http://docs.pylonsproject.org/
projects/pyramid/en/1.0-branch/narr/hooks.html#changing-the-traverser>`_ like so.

::

    from aiopyramid.traversal import AsyncioTraverser

    ...

    config.registry.registerAdapter(AsyncioTraverser, (Interface,), ITraverser)

Server Support
--------------
``Aiopyramid`` supports both asynchronous `gunicorn`_ and the `uWSGI asyncio plugin`_.

Example `gunicorn`_ config:

::

    [server:main]
    use = egg:gunicorn#main
    host = 0.0.0.0
    port = 6543
    worker_class = aiopyramid.gunicorn.worker.AsyncGunicornWorker

Example `uWSGI`_ config:

::

    [uwsgi]
    http-socket = 0.0.0.0:6543
    workers = 1
    plugins =
        asyncio = 50
        greenlet

Websockets
----------
``Aiopyramid`` provides additional view mappers for handling websocket connections with either
`gunicorn`_ or `uWSGI`. Websockets with `gunicorn`_ use the `websockets`_ library whereas with
`uWSGI` has native websocket support. In either case, the interface is the same.

A function ``view callable`` for a websocket connection follows this pattern:

::

    @view_config(mapper=<WebsocketMapper>)
    def websocket_callable(ws):
        # do stuff with ws


The ``ws`` argument passed to the callable has three methods for communicating with the websocket:
``recv``, ``send``, and ``close``, which correspond to similar methods in the `websockets`_ library.
A websocket connection that echoes all messages using `gunicorn`_  would be:

::

    from pyramid.view import view_config
    from aiopyramid.websocket.config import WebsocketMapper

    @view_config(route_name="ws", mapper=WebsocketMapper)
    def echo(ws):
        while True:
            message = yield from ws.recv()
            if message is None:
                break
            yield from ws.send(message)

``Aiopyramid`` also provides a ``view callable`` class ``WebsocketConnectionView`` that has ``on_message``,
``on_open``, and ``on_close`` callbacks. Class-based websocket views also have a ``send`` convenience method,
otherwise the underyling ``ws`` may be accessed as ``self.ws``. Simply extend ``WebsocketConnectionView``
specifying the correct view mapper for your server either via the ``__view_mapper__`` attribute or the
``view_config`` decorator. The above example could be rewritten in a larger project, this time using `uWSGI`_,
as follows:

::

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

``Aiopyramid`` uses a special ``WebsocketClosed`` exception to disconnect a ``greenlet`` after a websocket
has been closed. This exception will be visible in log ouput when using `uWSGI`_. In order to squelch this
message, wrap the wsgi application in the ``ignore_websocket_closed`` middleware
in your application's constructor like so:

::

    from aiopyramid.websocket.helpers import ignore_websocket_closed

    ...
    app = config.make_wsgi_app()
    return ignore_websocket_closed(app)


Tests
=====

Core functionality is backed by tests. The recommended test runner is `pytest`_. To run the
tests, grab the code on `github`_, install `pytest`_, and run it like so:

::

    git clone https://github.com/housleyjk/aiopyramid
    cd aiopyramid
    pip install pytest
    py.test



Approach
========

`TL;DR` I chose to make a new ``asyncio`` extension because I wanted to support `uWSGI`_ and
existing non-asynchronous extensions such as `pyramid_debugtoolbar`_.

``Aiopyramid`` was originally based on `pyramid_asyncio`_, but I followed a different approach
for the following reasons:

    -   The `pyramid_asyncio`_ library depends on patches made to the ``pyramid`` router that prevent it
        from working with the `uWSGI asyncio plugin`_.
    -   The `pyramid_asyncio`_ rewrites various parts of ``pyramid``,
        including tweens, to expect coroutines from ``pyramid`` internals.

On the other hand ``aiopyramid`` is designed to follow these principles:

    -   ``Aiopyramid`` should extend ``pyramid`` through existing ``pyramid`` mechanisms where possible.
    -    Asynchronous code that should be wrapped so that existing callers can treat it as synchronous code.

The first principle is one of the reasons why I used view mappers rather than patching the router.
View mappers are a mechanism already in place to handle how views are called. We don't need to rewrite
vast parts of ``pyramid`` to run a view in the ``asyncio`` event loop. Yes, ``pyramid`` is that awesome.

The second principle is what allows ``aiopyramid`` to support existing extensions. The goal is to isolate
asynchronous code from code that expects a synchronous response. Those methods that already exist in ``pyramid``
should not be rewritten as coroutines because we don't know who will
try to call them as regular methods.

Most of the ``pyramid`` framework does not run io blocking code. So, it is not actually necessary to change the
framework itself. Instead we need tools for making application code asynchronous. It should be possible
to run an existing url dispatch application asynchronously without modification. Blocking code will naturally end
up being run in a separate thread via the ``asyncio run_in_executor`` method. This allows you to optimize
only those highly concurrent views in your application or add in websocket support without needing to refactor
all of the code.

It is easy to simulate a multithreaded server by increasing the number of threads available to the executor.

For example, include the following in your application's constructor:

::

    import
    from concurrent.futures import ThreadPoolExecutor
    ...
    asyncio.get_event_loop().set_default_executor(ThreadPoolExecutor(max_workers=150))

It should be noted that ``Aiopyramid`` is not thread-safe by nature. You will need to ensure that in memory
resources are not modified by multiple non-coroutine ``view callables``. For most existing applications, this
should not be a problem.

.. _pyramid_asyncio: https://github.com/mardiros/pyramid_asyncio
.. _gunicorn: http://gunicorn.org
.. _uWSGI: https://github.com/unbit/uwsgi
.. _pyramid_debugtoolbar: https://github.com/Pylons/pyramid_debugtoolbar
.. _uWSGI asyncio plugin: http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html
.. _websockets: http://aaugustin.github.io/websockets/
.. _pytest: http://pytest.org
.. _github: https://github.com/housleyjk/aiopyramid
