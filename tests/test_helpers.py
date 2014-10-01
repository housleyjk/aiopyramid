import asyncio
import unittest

import greenlet
from pyramid.exceptions import ConfigurationError


class TestIsGenerator(unittest.TestCase):

    def test_regular_yield(self):
        from aiopyramid.helpers import is_generator

        def _sample():
            yield 1
            yield 2

        self.assertTrue(is_generator(_sample))

    def test_yield_from(self):
        from aiopyramid.helpers import is_generator

        def _placeholder():
            yield 6
            return 7

        def _sample():
            yield from _placeholder

        self.assertTrue(is_generator(_sample))

    def test_coroutine(self):
        from aiopyramid.helpers import is_generator

        @asyncio.coroutine
        def _sample():
            return 5

        self.assertTrue(is_generator(_sample))

    def test_false(self):
        from aiopyramid.helpers import is_generator

        def _sample():
            return "plain old function"

        self.assertFalse(is_generator(_sample))


class TestSpawnGreenlet(unittest.TestCase):

    def test_return_direct_result(self):
        from aiopyramid.helpers import spawn_greenlet

        def _return_4():
            return 4

        out = asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(_return_4),
        )
        self.assertEqual(out, 4)

    def test_switch_direct_result(self):
        from aiopyramid.helpers import spawn_greenlet

        def _switch_4_return_5():
            this = greenlet.getcurrent()
            this.parent.switch(4)
            return 5

        out = asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(_switch_4_return_5),
        )
        self.assertEqual(out, 4)

    def test_wait_on_future(self):
        from aiopyramid.helpers import spawn_greenlet

        future = asyncio.Future()

        def _switch_future():
            this = greenlet.getcurrent()
            this.parent.switch(future)
            return 5  # This should never get returned

        # the result is already set, but
        # spawn_greenlet will still need to yield from it
        future.set_result(4)
        out = asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(_switch_future),
        )
        self.assertEqual(out, 4)


class TestRunInGreenlet(unittest.TestCase):

    def test_result(self):
        from aiopyramid.helpers import spawn_greenlet
        from aiopyramid.helpers import run_in_greenlet

        @asyncio.coroutine
        def _sample(pass_back):
            return pass_back

        def _greenlet():
            this = greenlet.getcurrent()
            future = asyncio.Future()
            message = 12
            sub_task = asyncio.async(
                run_in_greenlet(this, future, _sample, message),
            )
            this.parent.switch(sub_task)
            self.assertEqual(future.result(), message)
            return message + 1

        out = asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(_greenlet),
        )
        self.assertEqual(13, out)

    def test_result_chain(self):
        from aiopyramid.helpers import spawn_greenlet
        from aiopyramid.helpers import run_in_greenlet

        @asyncio.coroutine
        def _sample(pass_back):
            return pass_back

        @asyncio.coroutine
        def _chain(pass_back):
            out = yield from _sample(pass_back)
            self.assertEqual(out, pass_back)
            return out - 1

        def _greenlet():
            this = greenlet.getcurrent()
            future = asyncio.Future()
            message = 12
            sub_task = asyncio.async(run_in_greenlet(
                this,
                future,
                _chain,
                message,
            ))
            this.parent.switch(sub_task)
            self.assertEqual(future.result(), message - 1)
            return message + 1

        out = asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(_greenlet),
        )
        self.assertEqual(13, out)

    def test_exception(self):
        from aiopyramid.helpers import spawn_greenlet
        from aiopyramid.helpers import run_in_greenlet

        @asyncio.coroutine
        def _sample():
            raise KeyError

        def _greenlet():
            this = greenlet.getcurrent()
            future = asyncio.Future()
            sub_task = asyncio.async(
                run_in_greenlet(this, future, _sample),
            )
            this.parent.switch(sub_task)
            self.assertRaises(KeyError, future.result)

        asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(_greenlet),
        )


class TestSynchronize(unittest.TestCase):

    @asyncio.coroutine
    def _sample(self, pass_back):
        return pass_back

    def _simple(self, pass_back):
        return pass_back

    def test_conversion(self):
        from aiopyramid.helpers import synchronize
        from aiopyramid.helpers import is_generator

        syncer = synchronize(strict=True)
        self.assertRaises(ConfigurationError, syncer, self._simple)
        self.assertFalse(is_generator(syncer(self._sample)))

    def test_scope_error(self):
        from aiopyramid.exceptions import ScopeError
        from aiopyramid.helpers import synchronize, spawn_greenlet

        synced = synchronize(self._sample)
        self.assertRaises(ScopeError, synced, 'val')

        five = asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(synced, 5),
        )
        self.assertEqual(five, 5)

        synced = synchronize(self._sample, strict=False)
        self.assertTrue(asyncio.iscoroutine(synced('val')))

    def test_as_decorator(self):
        from aiopyramid.helpers import synchronize, spawn_greenlet
        from aiopyramid.exceptions import ScopeError

        @synchronize
        @asyncio.coroutine
        def _synced(pass_back):
            yield
            return pass_back

        self.assertRaises(ScopeError, _synced, 'val')
        twelve = asyncio.get_event_loop().run_until_complete(
            spawn_greenlet(_synced, 12),
        )
        self.assertEqual(twelve, 12)
