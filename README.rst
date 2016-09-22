Introduction
============

A library for leveraging pyramid infrastructure asynchronously using the new ``asyncio``.

``Aiopyramid`` provides tools for making web applications with ``Pyramid`` and ``asyncio``.
It will not necessarily make your application run faster. Instead, it gives you some tools
and patterns to build an application on asynchronous servers.
Bear in mind that you will need to use asynchronous libraries for io where appropriate.

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

Documentation
-------------

Full documentation for ``Aiopyramid`` can be found `here`_.

.. _gunicorn: http://gunicorn.org
.. _uWSGI: https://github.com/unbit/uwsgi
.. _uWSGI asyncio plugin: http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html
.. _here: http://aiopyramid.readthedocs.io/
