import unittest

from pyramid import testing
from pyramid_asyncio.testing import async_test

class HelloTestCase(unittest.TestCase):

    @async_test
    def test_passing_view(self):
        from .views import say_hello
        request = testing.DummyRequest()
        info = yield from say_hello(request)
        self.assertEqual(info['name'], 'asyncio')
