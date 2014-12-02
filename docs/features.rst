Features
========

Rather than trying to rewrite :ref:`Pyramid <pyramid:index>`, ``Aiopyramid``
provides a set of features that will allow you to run existing code asynchronously
where possible.

Asynchronous Views
------------------
``Aiopyramid`` provides three view mappers for calling :term:`view callables <view callable>`:

    * :class:`~aiopyramid.config.CoroutineOrExecutorMapper` maps views to :term:`coroutines` or separate threads
    * :class:`~aiopyramid.config.CoroutineMapper` maps views to :term:`coroutines`
    * :class:`~aiopyramid.config.ExecutorMapper` maps views to separate threads

When you include ``Aiopyramid``,
the default view mapper is replaced with the :class:`~aiopyramid.config.CoroutineOrExecutorMapper`
which detects whether your :term:`view callable` is a coroutine and does a ``yield from`` to
call it asynchronously. If your :term:`view callable` is not a :term:`coroutine`, it will run it in a
separate thread to avoid blocking the thread with the main loop. :mod:`asyncio` is not thread-safe,
so you will need to guarantee that either in memory resources are not shared between :term:`view callables <view callable>`
running in the executor or that such resources are synchronized.

This means that you should not necessarily have to change existing views. Also,
it is possible to restore the default view mapper, but note that this will mean that
coroutine views that do not specify :class:`~aiopyramid.config.CoroutineMapper` as their
view mapper will fail.

Asynchronous Tweens
-------------------
:ref:`Pyramid <pyramid:index>` allows you to write :term:`tweens` which wrap the request/response chain. Most
existing :term:`tweens` expect those :term:`tweens` above and below them to run synchronously. Therefore,
if you have a :term:`tween` that needs to run asynchronously (e.g. it looks up some data from a
database for each request), then you will need to write that `tween` so that it can wait
without other :term:`tweens` needing to explicitly ``yield from`` it. An example of this pattern
is provided in :mod:`aiopyramid.tweens`.

Asynchronous Traversal
----------------------
When using :ref:`Pyramid's <pyramid:index>` :term:`traversal` view lookup,
it is often the case that you will want to
make some io calls to a database or storage when traversing via `__getitem__`. ``Aiopyramid``
provides a custom traverser that allows for `__getitem__` to be an :mod:`asyncio` :term:`coroutine`. To
use the traverser simply follow the :ref:`pyramid documentation <pyramid:hooks>` like so:

.. code-block:: python

    from aiopyramid.traversal import AsyncioTraverser

    ...

    config.registry.registerAdapter(AsyncioTraverser, (Interface,), ITraverser)

