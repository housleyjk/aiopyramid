1. Install Aiopyramid and Initialize Project
============================================

It is highly recommended that you use a virtual environment for your project. The
tutorial will assume that you are using `virtualenvwrapper`_ with a virtualenv
created like so::

    mkvirtualenv aiotutorial --python=/path/to/python3.4/interpreter

Once you have your tutorial environment active, install ``Aiopyramid``::

    pip install aiopyramid

This will also install the :ref:`Pyramid <pyramid:index>` framework. Now create
a new project using the ``aio_websocket`` scaffold since we intend to use Websockets
as part of this project.

    pcreate -s aio_websocket aiotutorial

This will make an ``aiotutorial`` directory with the following structure::

    .
    ├── aiotutorial         << Our Python package
    │   ├── __init__.py     << main file, contains the app constructor
    │   ├── templates       << directory for storing jinja templates
    │   │   └── home.jinja2 << template for the example homepage, contains a websocket test
    │   ├── tests.py        << tests module, contains tests for each of our existing views
    │   └── views.py        << views module, contains view callables
    ├── CHANGES.rst         << file for tracking changes to the library
    ├── development.ini     << config file, contains project and server settings
    ├── MANIFEST.in         << manifest file for distributing the project
    ├── README.rst          << readme for bragging about the project
    └── setup.py            << Python module for distributing the package and managing dependencies

Let's look at some of these files a little closer.

App Constructor
...............

The ``aiotutorial/__init__.py`` file contains the constructor for our app. It loads the logging
config from the ``development.ini`` config file and sets up Python logging. This is necessary
because the logging configuration won't be automatically detected when using Python3. Then, it
sets up two routes ``home`` and ``echo`` that we can tie views into with our views. Finally,
the constructor scans the project for configuration decorators and builds the wsgi callable.

The app constructor is the place where we will connect Python libraries to our application and
perform other configuration tasks.

.. code-block:: python
    :linenos:

    import logging.config

    from pyramid.config import Configurator


    def main(global_config, **settings):
        """ This function returns a Pyramid WSGI application.
        """

        # support logging in python3
        logging.config.fileConfig(
            settings['logging.config'],
            disable_existing_loggers=False
        )

        config = Configurator(settings=settings)
        config.add_route('home', '/')
        config.add_route('echo', '/echo')
        config.scan()
        return config.make_wsgi_app()

.. note:: *Thinking Asynchronously*

   The app constructor is called once to setup the application, which means that it is
   a synchronous context. The app is constructed before any requests are served, so it
   is safe to call blocking code here.


Tests
.....

The ``aiotutorial/tests.py`` file is a Python module with unittests for each of our views.
Let's look at the test case for the home page:

.. code-block:: python
    :linenos:

    class HomeTestCase(unittest.TestCase):

        def test_home_view(self):
            from .views import home

            request = testing.DummyRequest()
            info = asyncio.get_event_loop().run_until_complete(home(request))
            self.assertEqual(info['title'], 'aiotutorial websocket test')

Since test runners for unittest expect tests, such as ``test_home_view``, to run synchronously
but our home view is a :term:`coroutine`, we need to manually obtain an :mod:`asyncio` event
loop and run our view. Line 6 obtains a dummy request from :mod:`pyramid.testing`. We then pass
that request to our view and run it on line 7. Finally, line 8 makes assertions about the kind
of output we expect from our view.


Views
.....

This is the brains of our application, the place where decisions about how to respond to a particular
:term:`request` are made, and as such this is the place where you will most often start `chaining together
coroutines`_ to perform asynchronous tasks. Let's look at each of the example
views in turn:

.. code-block:: python
    :linenos:
    :emphasize-lines: 2,5

    @view_config(route_name='home', renderer='aiotutorial:templates/home.jinja2')
    @asyncio.coroutine
    def home(request):
        wait_time = float(request.params.get('sleep', 0.1))
        yield from asyncio.sleep(wait_time)
        return {'title': 'aiotutorial websocket test', 'wait_time': wait_time}

For those already familiar with :ref:`Pyramid <pyramid:index>` most of this view should require
no explanation. The important parts for running asynchronously are lines 2 and 5.

The :func:`~pyramid.view.view_config` decorator on line 1 ties this view to the 'home'
route declared in the app constructor. It also assigns a :term:`renderer` to the view that will
render the data returned into the ``template/home.jinja`` template and return a response
to the user. Line 2 wraps the view in a coroutine which differentiates it from a generator
or native coroutine. Line 3 is the signature for the coroutine. ``Aiopyramid`` view mappers
do not change the two default signarures for views, i.e. views that accept a request
and views that accept a context and a request. On line 4, we retrieve a sleep parameter,
from the request (the parameter can be either part of the querystring or the body). If
the request doesn't include a sleep parameter, the view defaults to 0.1. We don't need to
use ``yield from`` because ``request.params.get`` doesn't return a :term:`coroutine` or future.
The data for the request exists in memory so retrieving the parameter should be very fast.
Line 5 simulates performing some asynchronous task by suspending the coroutine and delegating to
another coroutine, :func:`asyncio.sleep`, which uses events to wait for ``wait_time`` seconds.
Using ``yield from`` is very important, without it the coroutine would
continue without sleeping as we want it to. Line 6 returns a Python dictionary that will be passed to the
jinja2 renderer.

The second view accepts a websocket connection:

.. code-block:: python
    :linenos:

    @view_config(route_name='echo', mapper=WebsocketMapper)
    @asyncio.coroutine
    def echo(ws):
        while True:
            message = yield from ws.recv()
            if message is None:
                break
            yield from ws.send(message)

This view is tied to the 'echo' route from the app constructor. Note that we use a special view mapper
for websocket connections. The :class:`aiopyramid.websocket.config.WebsocketMapper` changes the signature
of the view to accept a single websocket connection instead of a request. The connection object has three methods
for communicating with the :term:`websocket` :meth:`recv`, :meth:`send`, and :meth:`close` that
correspond to similar methods in the `websockets`_ library.

This websocket view will run echoing the data it recieves until the connection is closed. On line 5 we use
``yield from`` to wait until a message is received. If the message is None, then we know that the websocket
has closed and we break the loop to complete the echo coroutine. Otherwise, line 7 simply returns the same
message back to the websocket. Very simple. In both cases when we need to perform some io we use ``yield from``
to suspend our coroutine and delegate to another.

This kind of explicit yielding is a nice advantage for readability in Python code. It shows us exactly where
asynchronous is being called.

Development.ini
...............

The ``development.ini`` file contains the config for the project. Most of these settings could be specified in
the app constructor but it makes sense to separate out these values from procedural code. Here is an overview
of the two most important sections::

    [app:main]
    use = egg:aiotutorial

    pyramid.includes =
        aiopyramid
        pyramid_jinja2

    # for py3
    logging.config = %(here)s/development.ini

The ``[app:main]`` section contains the settings that will be passed to the app constructor as ``settings``.
This is where we include extensions for :ref:`Pyramid <pyramid:index>` such as ``Aiopyramid`` and the ``jinja``
templating library.

The ``[server:main]`` configures the default server for the project, which in this case is :mod:`gunicorn`::

    [server:main]
    use = egg:gunicorn#main
    host = 0.0.0.0
    port = 6543
    worker_class = aiopyramid.gunicorn.worker.AsyncGunicornWorker

The ``port`` setting here is the port that we will use to access the application, such as in a browser. The
``worker_class`` is set to the :class:`aiopyramid.gunicorn.worker.AsyncGunicornWorker` because we need to have
:mod:`gunicorn` setup the :doc:`Aiopyramid Architecture <approach>` for us.

Setup
.....

The ``setup.py`` file makes the ``aiotutorial`` package easy to distirbute, and it is also a good way, although
not the only good way, to manage dependencies for our project. Lines 18-21 list the Python packages that we need
for this project. We will be visiting the ``setup.py`` file in later chapters as we add more libraries::

    requires = [
        'aiopyramid[gunicorn]',
        'pyramid_jinja2',
    ]

Tweaking the defaults
.....................

The default view mapper that ``Aiopyramid`` sets up when it is included by the application tries to be as
robust as possible. It will inspect all of the views that we configure and try to guess whether or not
they are :term:`coroutines <coroutine>`. If the view looks like a :term:`coroutine`, in other words if it has
a ``yield from`` in it, the framework will treat it as a :term:`coroutine`, otherwise it will assume it is
legacy code and will run it in a separate thread to avoid blocking the event loop. This is very important
in principle, but since we know that we have no legacy views in this project, it makes sense to replace
the default mapper with one that expects views to be :term:`coroutines <coroutine>` always.

Adding the following line to the app constructor will do the trick:

.. code-block:: python
    :emphasize-lines: 2

    config = Configurator(settings=settings)
    config.set_view_mapper('aiopyramid.config.CoroutineMapper')
    config.add_route('home', '/')

.. note::

    When using ``Aiopyramid`` view mappers, it is actually not necessary to explicitly decorate :term:`view callables <view callable>`
    with :func:`asyncio.coroutine` as in the examples because the mapper will wrap views that appear to be :term:`coroutines <coroutine>`
    for you. It is still good practice to explicitly wrap your views because it facilitates using them in places where a
    view mapper may not be active, but if you are annoyed by the repetition, then you can skip writing ``@asyncio.coroutine`` before
    every view as long as you remember what is a :term:`coroutine`.

Making Sure it Works
....................

The last step in initializing the project is to install out dependencies and test out that the scaffold works as we expect::

    python setup.py develop

You can also use ``setup.py`` to run unittests::

    python setup.py test

You should see the following at the end of the output::


    test_home_view (aiotutorial.tests.HomeTestCase) ... ok
    test_echo_view (aiotutorial.tests.WSTest) ... ok

    ----------------------------------------------------------------------
    Ran 2 tests in 1.709s

    OK

If you don't like the test output from ``setup.py``, consider using a test runner like `pytest`_.

Now try running the server and visiting the homepage::

    gunicorn --paste development.ini

Open your browser to http://127.0.0.1:6543 to see the JavaScript test of the our echo websocket.
You should see the following output::

    aiotutorial websocket test

    CONNECTED

    SENT: Aiopyramid echo test.

    RESPONSE: Aiopyramid echo test.

    DISCONNECTED

This shows that the websocket is working. If you want to verify that the server is able to handle
multiple requests on a single thread, simply open a different browser (to avoid browser connection
limitations) and go to http://127.0.0.1:6543?sleep=10. The new browser should take roughly ten seconds
to load the page because our view is waiting for the value of ``sleep``. However, while that request is
ongoing, you can refresh your first browser and see that the server is still able to fulfill requests.

Congratulations! You have successfuly setup a highly configurable asynchronous server using ``Aiopyramid``!

.. note:: *Extra Credit*

    If you really want to see the power of asynchronous programming in Python, obtain a copy of `slowloris`_
    and run it against your knew ``Aiopyramid`` server and some non-asynchronous server. For example,
    you could run a simple ``Django`` application with gunicorn. You should see that the ``Aiopyramid`` server
    is still able to respond to requests whereas the ``Django`` server is bogged down. You could also use a simple
    PHP application using Apache to see this difference.

.. _pytest: http://pytest.org
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/
.. _chaining together coroutines: https://docs.python.org/3/library/asyncio-task.html#example-chain-coroutines
.. _websockets: http://aaugustin.github.io/websockets/
.. _slowloris: http://ha.ckers.org/slowloris/
