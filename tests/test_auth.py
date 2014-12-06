import asyncio

import pytest
from pyramid import testing
from aiopyramid.helpers import spawn_greenlet, synchronize


@pytest.yield_fixture
def web_request():
    request = testing.DummyRequest()
    yield request


class TestAuthentication:

    @pytest.yield_fixture
    def wrapped_policy(self):
        from pyramid.authentication import CallbackAuthenticationPolicy
        from aiopyramid.auth import authn_policy_factory

        @asyncio.coroutine
        def callback(userid, request):
            yield from asyncio.sleep(0.1)
            return ['test_user']

        class TestAuthenticationPolicy(CallbackAuthenticationPolicy):
            def __init__(self, callback):
                self.callback = callback
                self.debug = True

            def unauthenticated_userid(self, request):
                return 'theone'

        yield authn_policy_factory(TestAuthenticationPolicy, callback)

    def call_authn_policy_methods(self, policy, request):
        assert policy.unauthenticated_userid(request) == 'theone'
        assert policy.authenticated_userid(request) == 'theone'
        assert policy.effective_principals(request) == [
            'system.Everyone',
            'system.Authenticated',
            'theone',
            'test_user',
        ]

    @asyncio.coroutine
    def yield_from_authn_policy_methods(self, policy, request):
        assert (yield from policy.unauthenticated_userid(request)) == 'theone'
        assert (yield from policy.authenticated_userid(request)) == 'theone'
        assert (yield from policy.effective_principals(request)) == [
            'system.Everyone',
            'system.Authenticated',
            'theone',
            'test_user',
        ]

    def test_wrapper_in_sync(self, wrapped_policy, web_request):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(spawn_greenlet(
            self.call_authn_policy_methods,
            wrapped_policy,
            web_request,
        ))

    def test_wrapper_in_coroutine(self, wrapped_policy, web_request):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(spawn_greenlet(
            synchronize(self.yield_from_authn_policy_methods),
            wrapped_policy,
            web_request,
        ))
