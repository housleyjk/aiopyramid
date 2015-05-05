.. _architecture:

Architecture
============

``Aiopyramid`` uses a design similar to the `uWSGI asyncio plugin`_. The :mod:`asyncio` event loop runs in a
parent greenlet, while wsgi callables run in child greenlets. Because the callables are running in greenlets,
it is possible to suspend a callable and switch to parent to run :term:`coroutines <coroutine>` all on one event loop.
Each task tracks which child greenlet it belongs to and switches back to the appropriate callable when it is done.

The greenlet model makes it possible to have any Python code wait for a coroutine even when that code is unaware of
:mod:`asyncio`. The `uWSGI asyncio plugin`_ sets up the architecture by itself, but it is also possible to setup this
architecture whenever we have a running :mod:`asyncio` event loop using :func:`~aiopyramid.helpers.spawn_greenlet`.

For example, there may be times when a :term:`coroutine` would need to call some function ``a`` that later calls
a :term:`coroutine` ``b``. Since :term:`coroutines <coroutine>` run in the parent greenlet (i.e. on the event loop) and the function ``a``
cannot ``yield from`` ``b`` because it is not a :term:`coroutine` itself, the parent :term:`coroutine` will need to
set up the ``Aiopyramid`` architecture so that ``b`` can be synchronized with :func:`~aiopyramid.helpers.synchronize` and
called like a normal function from inside ``a``.

The following code demonstrates this usage without needing to setup a server.

.. doctest::


    >>> import asyncio
    >>> from aiopyramid.helpers import synchronize, spawn_greenlet
    >>>
    >>> @synchronize
    ... @asyncio.coroutine
    ... def some_async_task():
    ...   print('I am a synchronized coroutine.')
    ...   yield from asyncio.sleep(0.2)
    ...   print('Synchronized task done.')
    ...
    >>> def normal_function():
    ...   print('I am normal function that needs to call some_async_task')
    ...   some_async_task()
    ...   print('I (normal_function) called it, and it is done now like I expect.')
    ...
    >>> @asyncio.coroutine
    ... def parent():
    ...   print('I am a traditional coroutine that needs to call the naive normal_function')
    ...   yield from spawn_greenlet(normal_function)
    ...   print('All is done.')
    ...
    >>> loop = asyncio.get_event_loop()
    >>> loop.run_until_complete(parent())
    I am a traditional coroutine that needs to call the naive normal_function
    I am normal function that needs to call some_async_task
    I am a synchronized coroutine.
    Synchronized task done.
    I (normal_function) called it, and it is done now like I expect.
    All is done.

Please feel free to use this in other :mod:`asyncio` projects that don't use :ref:`Pyramid <pyramid:index>`
because it's awesome.

To avoid confusion, it is worth making explicit the fact that this approach is for incorporating code that is
fast and non-blocking itself but needs to call a coroutine to do some io. Don't try to use this to
call long-running or blocking Python functions. Instead, use `run_in_executor`_, which is what ``Aiopyramid``
does by default with :term:`view callables <view callable>` that don't appear to be :term:`coroutines <coroutine>`.


History
-------

``Aiopyramid`` was originally based on `pyramid_asyncio`_, but I chose a different approach
for the following reasons:

    -   The `pyramid_asyncio`_ library depends on patches made to the :ref:`Pyramid <pyramid:index>` router that prevent it
        from working with the `uWSGI asyncio plugin`_.
    -   The `pyramid_asyncio`_ rewrites various parts of :ref:`Pyramid <pyramid:index>`,
        including tweens, to expect :term:`coroutines <coroutine>` from :ref:`Pyramid <pyramid:index>` internals.

On the other hand ``Aiopyramid`` is designed to follow these principles:

    -   ``Aiopyramid`` should extend :ref:`Pyramid <pyramid:index>` through existing :ref:`Pyramid <pyramid:index>` mechanisms where possible.
    -    Asynchronous code should be wrapped so that existing callers can treat it as synchronous code.
    -   Ultimately, no framework can guarantee that all io calls are non-blocking because it is always possible for a programmer
        to call out to some function that blocks (in other words, the programmer forgets to wrap long-running calls in `run_in_executor`_).
        So, frameworks should leave the determination of what code is safe to the programmer and instead provide tools for
        programmers to make educated decisions about what Python libraries can be used on an asynchronous server. Following the
        :ref:`Pyramid <pyramid:index>` philosophy, frameworks should not get in the way.

The first principle is one of the reasons why I used :term:`view mappers <view mapper>` rather than patching the router.
:term:`View mappers <view mapper>` are a mechanism already in place to handle how views are called. We don't need to rewrite
vast parts of :ref:`Pyramid <pyramid:index>` to run a view in the :mod:`asyncio` event loop.
Yes, :ref:`Pyramid <pyramid:index>` is that awesome.

The second principle is what allows ``Aiopyramid`` to support existing extensions. The goal is to isolate
asynchronous code from code that expects a synchronous response. Those methods that already exist in :ref:`Pyramid <pyramid:index>`
should not be rewritten as :term:`coroutines <coroutine>` because we don't know who will try to call them as regular methods.

Most of the :ref:`Pyramid <pyramid:index>` framework does not run io blocking code. So, it is not actually necessary to change the
framework itself. Instead we need tools for making application code asynchronous. It should be possible
to run an existing simple url dispatch application asynchronously without modification. Blocking code will naturally end
up being run in a separate thread via the `run_in_executor`_ method. This allows you to optimize
only those highly concurrent views in your application or add in websocket support without needing to refactor
all of the code.

It is easy to simulate a multithreaded server by increasing the number of threads available to the executor.

For example, include the following in your application's constructor:

.. code-block:: python

    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    ...
    asyncio.get_event_loop().set_default_executor(ThreadPoolExecutor(max_workers=150))

.. note::
    It should be noted that ``Aiopyramid`` is not thread-safe by nature. You will need to ensure that in memory
    resources are not modified by multiple non-coroutine :term:`view callables <view callable>`. For most existing applications, this
    should not be a problem.

.. _uWSGI: https://github.com/unbit/uwsgi
.. _pyramid_debugtoolbar: https://github.com/Pylons/pyramid_debugtoolbar
.. _pyramid_asyncio: https://github.com/mardiros/pyramid_asyncio
.. _uWSGI asyncio plugin: http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html
.. _run_in_executor: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.BaseEventLoop.run_in_executor
