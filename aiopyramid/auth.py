"""
Utilities for making :ref:`Pyramid <pyramid:index>` authentication
and authorization work with Aiopyramid.
"""


from .helpers import spawn_greenlet_on_scope_error, synchronize


def coroutine_callback_authentication_policy_factory(
    policy_class,
    coroutine=None,
    *args,
    **kwargs
):
    """
    Factory function for creating an AuthenticationPolicy instance that uses
    a :term:`coroutine` as a callback.

    :param policy_class: The AuthenticationPolicy to wrap.
    :param coroutine coroutine: If provided this is passed to
    the AuthenticationPolicy as the callback argument.

    Extra arguments and keyword arguments are passed to
    the AuthenticationPolicy, so if the AuthenticationPolicy expects
    a callback under another name, it is necessary to pass
    a :term:`synchronized coroutine` as an argument or keyword argument
    to this factory or use
    :class:`~aiopyramid.auth.CoroutineAuthenticationPolicyProxy` directly.

    This function is also aliased as
    :func:`aiopyramid.auth.authn_policy_factory`.
    """

    if coroutine:
        coroutine = synchronize(coroutine)
        policy = policy_class(callback=coroutine, *args, **kwargs)
    else:
        policy = policy_class(*args, **kwargs)
    return CoroutineAuthenticationPolicyProxy(policy)


authn_policy_factory = coroutine_callback_authentication_policy_factory


class CoroutineAuthenticationPolicyProxy:
    """
    This authentication policy proxies calls to another policy that uses
    a callback to retrieve principals. Because this callback may be a
    :term:`synchronized coroutine`, this class handles the case where the
    callback fails due to a :class:`~aiopyramid.exceptions.ScopeError` and
    generates the appropriate ``Aiopyramid`` architecture.
    """

    def __init__(self, policy):
        """
        :param class policy: The authentication policy to wrap.
        """

        self._policy = policy

    @spawn_greenlet_on_scope_error
    def remember(self, request, principal, **kwargs):
        return self._policy.remember(request, principal, **kwargs)

    @spawn_greenlet_on_scope_error
    def forget(self, request):
        return self._policy.forget(request)

    @spawn_greenlet_on_scope_error
    def unauthenticated_userid(self, request):
        return self._policy.unauthenticated_userid(request)

    @spawn_greenlet_on_scope_error
    def authenticated_userid(self, request):
        return self._policy.authenticated_userid(request)

    @spawn_greenlet_on_scope_error
    def effective_principals(self, request):
        return self._policy.effective_principals(request)
