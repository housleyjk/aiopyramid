Introduction
============

A library for leveraging pyramid infrastructure asyncronously using the new ``asyncio``.

This library provides some of the same functionality as
`pyramid_asyncio`_, but it has more features
and follows a different approach. See `The Why`_.

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

Features
========
``Aiopyramid`` provides tools for making web applications with ``pyramid`` and ``aysncio``.
It will not by itself make your application asyncronous. Instead, it gives you some tools
and patterns to build an application on asyncronous servers.
Bear in mind that you will need to use asyncronous libraries for io where appropriate.

Asyncronous Views
-----------------
``Aiopyramid`` provides three view mappers for calling ``view callables``:

    * ``CoroutineOrExecutorMapper`` maps views to coroutines or separate threads
    * ``CoroutineMapper`` maps views to coroutines
    * ``ExecutorMapper`` maps views to separate threads

When you include ``Aiopyramid``,
the default view mapper is replaced with the ``CoroutineOrExecutorMapper``
which detects whether your ``view_callable`` is a coroutine and does a ``yield from`` to
call it asyncronously. If your ``view_callable`` is not a coroutine, it will run it in a
separate thread to avoid blocking the thread with the main loop.

This means that you do not need to change existing views in anyway. Also, via ``pyramid``
it is possible to restore the default view mapper, but note that this will mean that
coroutine views that do not specify ``CoroutineMapper`` as their view mapper will fail.

Asyncronous Tweens
------------------
``Pyramid`` allows you to write `tweens` which wrap the request/response chain. Most
existing `tweens` expect those `tweens` above and below them to run syncronously. Therefore,
if you have a tween that needs to run asyncronously (e.g. it looks up some data from a
database for each request), then you will need to write that `tween` so that it can wait
without other `tweens` needing to ``yield from`` it. An example of this pattern is provided
in ``aiopyramid.tweens``.

Asyncronous Traversal
---------------------
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
``Aiopyramid`` supports both asyncronous `gunicorn`_
and the `uWSGI asyncio plugin <http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html>`_.

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


The Why
=======

`TL;DR` I wanted to support `uWSGI`_ and existing extensions
such as `pyramid_debugtoolbar`_.

Q: So, why make a new library when `pyramid_asyncio`_
already exists?

A: I tried out `pyramid_asyncio`_, but as soon as I installed `pyramid_debugtoolbar`_, it broke. It
didn't break because `pyramid_debugtoolbar`_ does blocking io, rather it broke because of the fact
that `pyramid_asyncio`_ rewrites the ``pyramid`` router to expect coroutines from
``pryamid`` internals. Moreover, the fact that `pyramid_asyncio`_ patches the wsgi callable from
``pyramid`` prevents it from working with the `uWSGI asyncio plugin`_. In essence, it ties developers
to `gunicorn`_.

Since the `pyramid_asyncio`_ depends on the patching made to the ``pyramid`` router, I needed to write
a new library.

In this new approach, I tried to follow these principles:

    1. ``Aiopyramid`` should extend ``pyramid`` through existing ``pyramid`` mechanisms where possible.
    2. Asyncronous code should be wrapped to that callers can treat it as syncronous code.

The first principle is one of the reasons why I used view mappers rather than patching the router.
View mappers are a mechanism already in place to handle how views are called. We don't need to rewrite
vast parts of ``pyramid`` to run a view in the ``asyncio`` event loop. Yes, ``pyramid`` is that awesome.

The second principle is what allows ``aiopyramid`` to support existing extensions. The goal is to isolate
asyncronous code from code that expects a syncronous response. Those methods that already exist in ``pyramid``
(i.e. those that comprise its API) should never be rewritten as coroutines because we don't know who will
try to call them as regular methods.

This approach allows for making only those parts of ``pyramid`` that necessarily run blocking code actually
run in the ``asyncio`` event loop. Therefore, it should be possible to run an existing url dispatch application
asyncronously without modification. Blocking code will naturally end up being run in a separate thread via
the ``asyncio run_in_executor`` method. This allows you to optimize only those highly concurrent views in your
application or add in websocket support without needing to refactor all of the code.

It is easy to simulate a multithreaded server by increasing the number of threads available to the executor.

For example, include the following in your application's constructor:

::

    import
    from concurrent.futures import ThreadPoolExecutor
    ...
    asyncio.get_event_loop().set_default_executor(ThreadPoolExecutor(max_workers=150))

This kind of flexibility is not available int `pyramid_asyncio`_.

.. _pyramid_asyncio: https://github.com/mardiros/pyramid_asyncio
.. _gunicorn: http://gunicorn.org
.. _uWSGI: https://github.com/unbit/uwsgi
.. _pyramid_debugtoolbar: https://github.com/Pylons/pyramid_debugtoolbar
.. uWSGI asyncio plugin: http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html
