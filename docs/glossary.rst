Glossary
========

.. glossary::
   :sorted:

   websocket
    WebSocket is a protocol providing full-duplex communications channels over a single TCP connection.
    See `websockets`_ for a simple python library to get started.

   coroutine
    A coroutine is a generator that follows certain conventions in :mod:`asyncio`. See `asyncio docs`_.

   synchronized coroutine
    A coroutine that has been wrapped or decorated by :func:`~aiopyramid.helpers.synchronize` so that
    it can be executed without using ``yield from`` in a child :term:`greenlet`. Synchronized coroutines are
    used to bridge the gap between framework code which expects normal Python functions and application
    code that uses coroutines.

.. _websockets: http://aaugustin.github.io/websockets/
.. _asyncio docs: https://docs.python.org/3/library/asyncio-task.html#coroutine
