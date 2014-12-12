Tutorial
========

This tutorial will show you how to develop a multiplayer game using JavaScript
that relies on a horizontally scalable asynchronous server using ``Aiopyramid``.
The application will include the following technical features:

    * Persistance using a Postgres database and the :mod:`aiopg` library.
    * Chat service with channels using Websockets and redis
    * Url dispatch and Asynchronous traversal
    * Database migrations using alembic

This tutorial assumes the reader has at least a basic knowledge of 
the :ref:`Pyramid <pyramid:index>` framework so concepts like 
:term:`view callables <view callable>` and :term:`renderers <renderer>`
will not be explained. Please refer to the :ref:`Pyramid Documentation <pyramid:index>`.


Chapters
--------

.. toctree::
    :maxdepth: 1

    one

