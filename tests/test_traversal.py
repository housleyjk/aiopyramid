import unittest
import asyncio

from pyramid.traversal import traverse

from aiopyramid.helpers import spawn_greenlet, synchronize


class DummyResource:
    """ Dummy resource for testing async traversal. """

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self._dict = {}

    @synchronize
    @asyncio.coroutine
    def __getitem__(self, key):
        yield from asyncio.sleep(0.1)
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def add_child(self, name, klass):
        resource = klass(name=name, parent=self)
        self[name] = resource


class TestTraversal(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def test_async_traversed_length(self):
        resource = DummyResource('root', None)
        resource.add_child('cat', DummyResource)
        out = self.loop.run_until_complete(
            spawn_greenlet(traverse, resource, ['cat']),
        )
        self.assertEqual(len(out['traversed']), 1)

    def test_async_root(self):
        resource = DummyResource('root', None)
        resource.add_child('cat', DummyResource)
        out = self.loop.run_until_complete(
            spawn_greenlet(traverse, resource, ['']),
        )
        self.assertTrue(out.get('root') == out.get('context'))

    def test_async_depth(self):
        resource = DummyResource('root', None)
        resource.add_child('cat', DummyResource)
        out = self.loop.run_until_complete(
            spawn_greenlet(traverse, resource, ['cat']),
        )
        out['context'].add_child('dog', DummyResource)
        out = self.loop.run_until_complete(
            spawn_greenlet(traverse, resource, ['cat', 'dog']),
        )
        self.assertListEqual(list(out['traversed']), ['cat', 'dog'])

    def test_async_view_name(self):
        resource = DummyResource('root', None)
        resource.add_child('cat', DummyResource)
        out = self.loop.run_until_complete(
            spawn_greenlet(traverse, resource, ['cat', 'mouse']),
        )
        self.assertListEqual(list(out['traversed']), ['cat'])
        self.assertEqual(out['view_name'], 'mouse')
