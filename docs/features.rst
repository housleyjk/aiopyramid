Features
========

Rather than trying to rewrite :ref:`Pyramid <pyramid:index>`, ``Aiopyramid``
provides a set of features that will allow you to run existing code asynchronously
where possible.

Views
-----
``Aiopyramid`` provides three view mappers for calling :term:`view callables <view callable>`:

    * :class:`~aiopyramid.config.CoroutineOrExecutorMapper` maps views to :term:`coroutines <coroutine>` or separate threads
    * :class:`~aiopyramid.config.CoroutineMapper` maps views to :term:`coroutines <coroutine>`
    * :class:`~aiopyramid.config.ExecutorMapper` maps views to separate threads

When you include ``Aiopyramid``,
the default view mapper is replaced with the :class:`~aiopyramid.config.CoroutineOrExecutorMapper`
which detects whether your :term:`view callable` is a coroutine and does a ``yield from`` to
call it asynchronously. If your :term:`view callable` is not a :term:`coroutine`, it will run it in a
separate thread to avoid blocking the thread with the main loop. :mod:`asyncio` is not thread-safe,
so you will need to guarantee that either in memory resources are not shared between
:term:`view callables <view callable>` running in the executor or that such resources are synchronized.

This means that you should not necessarily have to change existing views. Also,
it is possible to restore the default view mapper, but note that this will mean that
coroutine views that do not specify :class:`~aiopyramid.config.CoroutineMapper` as their
view mapper will fail.

Authorization
-------------

If you are using the default authorization policy, then you will generally not need to make any modifications
to authorize users with ``Aiopyramid``. The exception is if you want to use a callable that performs
some io for your __acl__. In that case you will simply need to use a :term:`synchronized coroutine` so
that the authorization policy can call your :term:`coroutine` like a normal Python function during view lookup.

For example:

.. code-block:: python

    import asyncio

    from aiopyramid.helpers import synchronize


    class MyResource:
        """
        This resource uses a callable for it's __acl__ that accesses the db.
        """

        # this
        __acl__ = synchronize(my_coroutine)

        # or this

        @synchronize
        @asyncio.coroutine
        def __acl__(self):
            ...

        # will work

If you are using a custom authorization policy, most likely it will work with ``Aiopyramid`` in the same
fashion, but it is up to you to guarantee that it does.

Authentication
--------------

Authentication poses a problem because the interface for
:term:`authentication policies <authentication policy>` uses normal Python methods that the framework expects
to call noramlly but at the same time it is usually necessary to perform some io to retrieve relevant information.
The built-in :term:`authentication policies <authentication policy>` generally accept a callback function that
delegates retrieving :term:`principals <principal>` to the application, but this callback function is also expected
to be called in the regular fashion. So, it is necessary to use a :term:`synchronized coroutine` as a callback
function.

The final problem is that :term:`synchronized coroutines <synchronized coroutine>` are expected
to be called from within a child :term:`greenlet`, or in other words from within framework code (see :ref:`architecture`).
However, it is often the case that we will want to access the policy through :attr:`pyramid.request.Request.authenticated_userid`
or by calling :func:`~pyramid.security.remember`, etc. from within another coroutine such as a :term:`view callable`.

To handle both situations, ``Aiopyramid`` provides tools for wrapping a callback-based :term:`authentication policy` to
work asynchronously. For example, the following code in your app constructor will allow you to use a :term:`coroutine` as
a callback.

.. code-block:: python

    from pyramid.authentication import AuthTktAuthenticationPolicy  # for example
    from aiopyramid.auth import authn_policy_factory

    from .myauth import get_principals

    ...

    # In the includeme or constructor
    authentication = authn_policy_factory(
        AuthTktAuthenticationPolicy,
        get_principals,
        'sosecret',
        hashalg='sha512'
    )
    config.set_authentication_policy(authentication)


Relevant authentication tools will now return a :term:`coroutine` when called from another :term:`coroutine`, so you
would access the :term:`authentication policy` using ``yield from`` in your :term:`view callable` since it performs io.

.. code-block:: python

    from pyramid.security import remember, forget

    ...

    # in some coroutine

    maybe = yield from request.unauthenticated_userid
    checked = yield from request.authenticated_userid
    principals = yield from request.effective_principals
    headers = yield from remember(request, 'george')
    fheaders = yield from forget(request)


.. note::

    If you don't perform asynchronous io or wrap the :term:`authentication policy` as above,
    then don't use ``yield from`` in your view. This approach only works for :term:`coroutine`
    views. If you have both :term:`coroutine` views and legacy views running in an executor,
    you will probably need to write a custom :term:`authentication policy`.

Tweens
------
:ref:`Pyramid <pyramid:index>` allows you to write :term:`tweens <tween>` which wrap the request/response chain. Most
existing :term:`tweens <tween>` expect those :term:`tweens <tween>` above and below them to run synchronously. Therefore,
if you have a :term:`tween` that needs to run asynchronously (e.g. it looks up some data from a
database for each request), then you will need to write that `tween` so that it can wait
without other :term:`tweens <tween>` needing to explicitly ``yield from`` it. For example:

.. code-block:: python

    import asyncio

    from aiopyramid.helpers import synchronize


    def coroutine_logger_tween_factory(handler, registry):
        """
        Example of an asynchronous tween that delegates a synchronous function to
        a child thread. This tween asynchronously logs all requests and responses.
        """

        # We use the synchronize decorator because we will call this
        # coroutine from a normal python context
        @synchronize
        # this is a coroutine
        @asyncio.coroutine
        def _async_print(content):
            # print doesn't really need to be run in a separate thread
            # but it works for demonstration purposes

            yield from asyncio.get_event_loop().run_in_executor(
                None,
                print,
                content
            )

        def coroutine_logger_tween(request):
            # The following calls are guaranteed to happen in order but they do not
            # block the event loop

            # print the request on the aio event loop without needing to say yield
            # at this point, other coroutines and requests can be handled
            _async_print(request)

            # get response, this should be done in this greenlet
            # and not as a coroutine because this will call
            # the next tween and subsequently yield if necessary
            response = handler(request)

            # print the response on the aio event loop
            _async_print(request)

            # return response after logging is done
            return response

        return coroutine_logger_tween

Traversal
---------
When using :ref:`Pyramid's <pyramid:index>` :term:`traversal` view lookup,
it is often the case that you will want to
make some io calls to a database or storage when traversing via `__getitem__`. When using the default
traverser, :ref:`Pyramid <pyramid:index>` will call `__getitem__` as a normal Python function. Therefore,
it is necessary to synchronize `__getitem__` on any asynchronous resources like so:

.. code-block:: python

    import asyncio

    from aiopyramid.helpers import synchronize


    class MyResource:
        """ This resource performs some asynchronous io. """

        __name__ = "example"
        __parent__ = None

        @synchronize
        @asyncio.coroutine
        def __getitem__(self, key):
            yield from self.example_coroutine()
            return self  # no matter the path, this is the context

        @asyncio.coroutine
        def example_coroutine(self):
            yield from asyncio.sleep(0.1)
            print('I am some async task.')

Servers
-------

``Aiopyramid`` supports both asynchronous `gunicorn`_ and the `uWSGI asyncio plugin`_.

Example `gunicorn`_ config:

.. code-block:: ini

    [server:main]
    use = egg:gunicorn#main
    host = 0.0.0.0
    port = 6543
    worker_class = aiopyramid.gunicorn.worker.AsyncGunicornWorker

Example `uWSGI`_ config:

.. code-block:: ini

    [uwsgi]
    http-socket = 0.0.0.0:6543
    workers = 1
    plugins =
        asyncio = 50
        greenlet

For those setting up ``Aiopyramid`` on a Mac, Ander Ustarroz's `tutorial`_ may prove useful.

Websockets
----------

``Aiopyramid`` provides additional view mappers for handling websocket connections with either
`gunicorn`_ or `uWSGI`_. Websockets with `gunicorn`_ use the `websockets`_ library whereas
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
.. _uWSGI asyncio plugin: http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html
.. _websockets: http://aaugustin.github.io/websockets/
.. _tutorial: http://www.developerfiles.com/installing-uwsgi-with-asyncio-on-mac-os-x-10-10-yosemite/
