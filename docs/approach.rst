Approach
========

`TL;DR` I chose to make a new :mod:`asyncio` extension because I wanted to support `uWSGI`_ and
existing non-asynchronous extensions such as `pyramid_debugtoolbar`_.

``Aiopyramid`` was originally based on `pyramid_asyncio`_, but I chose a different approach
for the following reasons:

    -   The `pyramid_asyncio`_ library depends on patches made to the :ref:`Pyramid <pyramid:index>` router that prevent it
        from working with the `uWSGI asyncio plugin`_.
    -   The `pyramid_asyncio`_ rewrites various parts of :ref:`Pyramid <pyramid:index>`,
        including tweens, to expect coroutines from :ref:`Pyramid <pyramid:index>` internals.

On the other hand ``Aiopyramid`` is designed to follow these principles:

    -   ``Aiopyramid`` should extend :ref:`Pyramid <pyramid:index>` through existing :ref:`Pyramid <pyramid:index>` mechanisms where possible.
    -    Asynchronous code should be wrapped so that existing callers can treat it as synchronous code.

The first principle is one of the reasons why I used view mappers rather than patching the router.
View mappers are a mechanism already in place to handle how views are called. We don't need to rewrite
vast parts of :ref:`Pyramid <pyramid:index>` to run a view in the :mod:`asyncio` event loop. Yes, :ref:`Pyramid <pyramid:index>` is that awesome.

The second principle is what allows ``Aiopyramid`` to support existing extensions. The goal is to isolate
asynchronous code from code that expects a synchronous response. Those methods that already exist in :ref:`Pyramid <pyramid:index>`
should not be rewritten as coroutines because we don't know who will
try to call them as regular methods.

Most of the :ref:`Pyramid <pyramid:index>` framework does not run io blocking code. So, it is not actually necessary to change the
framework itself. Instead we need tools for making application code asynchronous. It should be possible
to run an existing url dispatch application asynchronously without modification. Blocking code will naturally end
up being run in a separate thread via the `run_in_executor`_ method. This allows you to optimize
only those highly concurrent views in your application or add in websocket support without needing to refactor
all of the code.

It is easy to simulate a multithreaded server by increasing the number of threads available to the executor.

For example, include the following in your application's constructor:

.. code-block:: python

    import
    from concurrent.futures import ThreadPoolExecutor
    ...
    asyncio.get_event_loop().set_default_executor(ThreadPoolExecutor(max_workers=150))

It should be noted that ``Aiopyramid`` is not thread-safe by nature. You will need to ensure that in memory
resources are not modified by multiple non-coroutine :term:`view callables <view callable>`. For most existing applications, this
should not be a problem.

.. _uWSGI: https://github.com/unbit/uwsgi
.. _pyramid_debugtoolbar: https://github.com/Pylons/pyramid_debugtoolbar
.. _pyramid_asyncio: https://github.com/mardiros/pyramid_asyncio
.. _uWSGI asyncio plugin: http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html
.. _run_in_executor: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.BaseEventLoop.run_in_executor
