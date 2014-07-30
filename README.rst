Introduction
===============

A library for leveraging pyramid infrastructure asyncronously using the new asyncio.

This library is based on `pyramid_asyncio <https://github.com/mardiros/pyramid_asyncio>`_.

Getting Started
---------------

aiopyramid includes a scaffold that creates a "hello world" application,
check it out. 

::

    pcreate -s aio_jinja2 <project>


Asyncronous Views
---------------

* config.add_coroutine_view()

This is a coroutine version of the ``config.add_view``.
Aiopyramid also provides decorator for adding a
coroutine view ``coroutine_view_config`` analogous to ``view_config``.

WSGI Application
--------------

* config.make_asyncio_app()

config.make_wsgi_app() could not be used because the pyramid router is
syncronous and we would like to allow for asyncronous view lookup and
traversal.


