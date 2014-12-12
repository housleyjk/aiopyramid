import unittest
import asyncio

from pyramid import testing


class HelloTestCase(unittest.TestCase):

    def test_demo_view(self):
        from .views import say_hello

        request = testing.DummyRequest()
        info = asyncio.get_event_loop().run_until_complete(say_hello(request))
        self.assertEqual(info, 'Welcome to Pyramid with Asyncio.')
