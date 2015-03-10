2. Adding Persistence and Migrations
====================================

Most web applications require some kind of persistence, usually via a database.
In this chapter, you will learn one way to setup a database to work with ``Aiopyramid``.
This tutorial will use `aiopg`_ to access a Postgresql database asynchronously and
`alembic`_ to manage the database schema.

Before continuing with this tutorial, you will need to install Postgresql for your system
and create a database named ``aiotutorial``.


Adding Dependencies
...................

Update the ``setup.py`` file to add `alembic`_ and `aiopg`_ to the requires:

.. code-block:: python
    :emphasize-lines: 4-5

    requires = [
        'aiopyramid[gunicorn]',
        'pyramid_jinja2',
        'alembic',
        'aiopg',
    ]



`alembic`_ and `aiopg`_ both depend on `sqlalchemy`_, so it will be installed automatically by including
the previous two libraries. Now that we have specified the dependencies, we need to run install them by
rerunning::

    python setup.py develop

Defining the Schema
...................

Add a new ``database.py`` module to the ``aiotutorial`` package with the following contents:

.. code-block:: python

    import sqlalchemy as sa

    metadata = sa.MetaData()

    user = sa.Table(
        'users',
        metadata,
        sa.Column('username', sa.String(40), primary_key=True),
        sa.Column('phash', sa.String(128)),
    )

    chat = sa.Table(
        'chats',
        metadata,
        sa.Column('channel', sa.String(40), primary_key=True),
    )

    message = sa.Table(
        'messages',
        metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('channel', sa.String(40), sa.ForeignKey(chat.c.channel), nullable=False),
        sa.Column('user', sa.String(40), sa.ForeignKey(user.c.username), nullable=False),
        sa.Column('time', sa.DateTime, index=True, nullable=False),
        sa.Column('content', sa.Text, nullable=False, default=''),
    )

    game = sa.Table(
        'games',
        metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('channel', sa.String(40), sa.ForeignKey(chat.c.channel), nullable=False),
        sa.Column('finished', sa.DateTime, index=True),
    )

    score = sa.Table(
        'scores',
        metadata,
        sa.Column('game', sa.Integer, sa.ForeignKey(game.c.id), primary_key=True),
        sa.Column('user', sa.String(40), sa.ForeignKey(user.c.username), primary_key=True),
        sa.Column('points', sa.SmallInteger, nullable=False, default=0),
    )


Don't worry if you don't understand every part of this schema; the logic behind it will be
explained in later chapters. This ``database`` module provides an abstraction around the database
that allows us to write dynamic queries more easily. The ``metadata`` object captures our schema
definition and allows `alembic`_ to generate the necessary queries to migrate the database schema
automatically.

The ``user`` table will store the usernames of every user that chooses to play the game. It's useful for
associating other information, such as chat records or game results, with a particular user. The ``chat``
table is for tracking the various chat channels that we will use, whereas the actual messages that users
enter in the chat will be stored in the ``message`` table. The ``game`` table tracks the games that are
started and if/when they are finished, while the ``score`` table will be used to track the actual results
of the game for each player (user).

Creating the Database
.....................

Our first migration will be to create the database tables, but before we can perform any migrations, we
need to setup the `alembic`_ environment. The following command will add an ``alembic.ini`` config file to
our project root and init the `alembic`_ environment in the ``migrations`` directory::

    alembic init migrations

In order to create the first migration file, we need to let `alembic`_ know about our database metadata and
the address of the ``aiotutorial`` database. Edit the ``alembic.ini`` to point the database. For example::

    sqlalchemy.url = postgresql://localhost/aiotutorial

Then edit the newly created ``migrations/env.py`` file adding following import after ``create_engine``::

    from aiotutorial.database import metadata

and change::

    target_metadata = None

to::

    target_metadata = metadata

The command to create the first migration is very simple::

    alembic revision -m "create schema" --autogenerate

Likewise, to apply the migration, run::

    alembic upgrade head

This will create the necessary database tables according to the contents of the ``database`` module of our project
becuase we imported that metadata into the `alembic`_ environment environment.

Testing the Database
....................

Tests are a good way to get to know how to use a database in ``Aiopyramid``. You can try out different types of queries
and then if at some point your database changes, the fact that you left your experimitation in the test may forewarn you
that part of your application could break.

Let's add a new test case to our ``tests`` module:

.. code-block:: python

    from alembic.config import Config
    from alembic.command import upgrade

    # existing code redacted

    class DatabaseTest(unittest.TestCase):
        """ Test aiotutorial database schema. """

        def setUp(self):
            test_db = "postgresql://localhost/aiotutorial_testing"
            alembic_config = Config('/ABSOLUTE/PATH/TO/alembic.ini')
            alembic_config.set_main_option('sqlalchemy.url', test_db)
            upgrade(alembic_config, 'head')


When writing tests that interact with a database, it is a good idea to create a separate testing database so as not to
contaminate any live data. In the above, you will need to update the Config object to point to your `alembic`_ environment
by replacing ``/ABSOLUTE/PATH/TO/alembic.ini`` with the path to the correct path to your project on your system.
You will also need to create the ``aiotutorial_testing`` database on your Postgresql server. This ``setUp``
method will run for each test and ensure that we have the latest schema in the test database. This is the equivalent of the above
command we used to update the main ``aiotutorial`` database.

Also, when testing a database, it is best to run each test inside of a transaction and rollback that transaction at the end
of the test. This keeps different tests from interferring with each other. Since we want to run queries asynchronously we
need to setup the transaction asynchronously.

.. code-block:: python
    :emphasize-lines: 1, 8-12, 14-17, 24-25, 27-28

    from aiopg.sa import create_engine

    # existing code redacted

    class DatabaseTest(unittest.TestCase):
        """ Test aiotutorial database schema. """

        @asyncio.coroutine
        def begin_transaction(self, db_url):
            db_engine = yield from create_engine(db_url)
            connection = yield from db_engine.acquire()
            self.transaction = yield from connection.begin()

        @asyncio.coroutine
        def cleanup_transaction(self):
            yield from self.transaction.rollback()
            yield from self.transaction.connection.close()

        def setUp(self):
            test_db = "postgresql://localhost/aiotutorial_testing"
            alembic_config = Config('/ABSOLUTE/PATH/TO/alembic.ini')
            alembic_config.set_main_option('sqlalchemy.url', test_db)

            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.start_transaction(test_db))

        def tearDown(self):
            self.loop.run_until_complete(self.cleanup_transaction())

The connection is accessible on the transaction as ``self.transaction.connection``. With this infrastructure in place,
we can run any queries that we think are necessary to test the database. This is a good way to familiarize yourself with
one way to obtain and update date in an ``Aiopyramid`` project. As in the previous chapter, each test needs to be run
from a synchronous context, whereas our actual query code needs to use coroutines. An example test, might look like this:

.. code-block:: python

    # import the database module

    from . import database as db

    # inside DatabaseTest

    def test_user(self):

        conn = self.transaction.connection

        @asyncio.coroutine
        def add_and_return_user(username):

            yield from conn.execute(db.user.insert().values(username=username))
            users = yield from conn.execute(db.user.select(db.user.username == username))
            return (yield from users.fetchone())

        username = 'my-test-user'
        user_obj = self.loop.run_until_complete(add_and_return_user(username))
        self.assertEqual(user_obj.username, username)

You can find more tests by obtaining the code for this chapter from github.

.. _aiopg: http://aiopg.readthedocs.org/en/stable/
.. _alembic: https://alembic.readthedocs.org/en/latest/
.. _sqlalchemy: http://www.sqlalchemy.org/



