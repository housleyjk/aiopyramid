Server Support
==============

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


.. _gunicorn: http://gunicorn.org
.. _uWSGI: https://github.com/unbit/uwsgi
.. _uWSGI asyncio plugin: http://uwsgi-docs.readthedocs.org/en/latest/asyncio.html
