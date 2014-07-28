"""
Override the Pyramid Router in order to get request handler as
asyncio coroutine.
"""

import asyncio
import logging
import greenlet

from zope.interface import implementer, providedBy
from pyramid.interfaces import (
    IRequest,
    IRouteRequest,
    IRouter,
    ITraverser,
    IView,
    IViewClassifier,
    # ITweens,
)
from pyramid.events import (
    ContextFound,
    NewRequest,
    NewResponse,
)
from pyramid.exceptions import PredicateMismatch
from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import ResourceTreeTraverser

from pyramid.router import Router as RouterBase

# from .tweens import excview_tween_factory

log = logging.getLogger(__name__)


@asyncio.coroutine
def lift():
    return "lift"


@asyncio.coroutine
def sleeping(me, f):
    print('before sleep')
    body = yield from lift()
    # body is a byterray !
    f.set_result(body)
    print('switching back')
    me.switch()
    print('post response')


@implementer(IRouter)
class Router(RouterBase):

    def __init__(self, config):
        self.config = config
        # config.registry.registerUtility(excview_tween_factory, ITweens)
        super().__init__(config.registry)

    @asyncio.coroutine
    def handle_request(self, request):
        attrs = request.__dict__
        registry = attrs['registry']

        request.request_iface = IRequest
        context = None
        routes_mapper = self.routes_mapper
        debug_routematch = self.debug_routematch
        adapters = registry.adapters
        has_listeners = registry.has_listeners
        notify = registry.notify
        logger = self.logger

        has_listeners and notify(NewRequest(request))
        # find the root object
        root_factory = self.root_factory
        if routes_mapper is not None:
            info = routes_mapper(request)
            match, route = info['match'], info['route']
            if route is None:
                if debug_routematch:
                    msg = ('no route matched for url %s' %
                           request.url)
                    logger and logger.debug(msg)
            else:
                attrs['matchdict'] = match
                attrs['matched_route'] = route

                if debug_routematch:
                    msg = (
                        'route matched for url {}; '
                        'route_name: {}, '
                        'path_info: {}, '
                        'pattern: {}, '
                        'matchdict: {}, '
                        'predicates: {}'.format(
                            request.url,
                            route.name,
                            request.path_info,
                            route.pattern,
                            match,
                            ', '.join([p.text() for p in route.predicates])
                        )
                    )
                    logger and logger.debug(msg)

                request.request_iface = registry.queryUtility(
                    IRouteRequest,
                    name=route.name,
                    default=IRequest)

                root_factory = route.factory or self.root_factory

        root = root_factory(request)
        attrs['root'] = root

        # find a context
        traverser = adapters.queryAdapter(root, ITraverser)
        if traverser is None:
            traverser = ResourceTreeTraverser(root)
        tdict = traverser(request)

        context, view_name, subpath, traversed, vroot, vroot_path = (
            tdict['context'],
            tdict['view_name'],
            tdict['subpath'],
            tdict['traversed'],
            tdict['virtual_root'],
            tdict['virtual_root_path']
        )

        attrs.update(tdict)
        has_listeners and notify(ContextFound(request))

        # find a view callable
        context_iface = providedBy(context)
        view_callable = adapters.lookup(
            (IViewClassifier, request.request_iface, context_iface),
            IView, name=view_name, default=None)

        # invoke the view callable
        if view_callable is None:
            if self.debug_notfound:
                msg = (
                    'debug_notfound of url %s; path_info: %r, '
                    'context: %r, view_name: %r, subpath: %r, '
                    'traversed: %r, root: %r, vroot: %r, '
                    'vroot_path: %r' % (
                        request.url, request.path_info, context,
                        view_name, subpath, traversed, root, vroot,
                        vroot_path)
                )
                logger and logger.debug(msg)
            else:
                msg = request.path_info
            raise HTTPNotFound(msg)
        else:
            try:
                if asyncio.iscoroutinefunction(view_callable):
                    response = yield from view_callable(context, request)
                else:
                    response = view_callable(context, request)
            except PredicateMismatch:
                # look for other views that meet the predicate
                # criteria
                for iface in context_iface.__sro__[1:]:
                    previous_view_callable = view_callable
                    view_callable = adapters.lookup(
                        (IViewClassifier, request.request_iface, iface),
                        IView, name=view_name, default=None)
                    # intermediate bases may lookup same view_callable
                    if view_callable is previous_view_callable:
                        continue
                    if view_callable is not None:
                        try:
                            response = yield from view_callable(context,
                                                                request)
                            break
                        except PredicateMismatch:
                            pass
                else:
                    raise
        return response

    @asyncio.coroutine
    def invoke_subrequest(self, request, use_tweens=False):
        """Obtain a response object from the Pyramid application based on
        information in the ``request`` object provided.  The ``request``
        object must be an object that implements the Pyramid request
        interface (such as a :class:`pyramid.request.Request` instance).  If
        ``use_tweens`` is ``True``, the request will be sent to the
        :term:`tween` in the tween stack closest to the request ingress.  If
        ``use_tweens`` is ``False``, the request will be sent to the main
        router handler, and no tweens will be invoked.

        See the API for pyramid.request for complete documentation.
        """
        registry = self.registry
        has_listeners = self.registry.has_listeners
        notify = self.registry.notify
        threadlocals = {'registry': registry, 'request': request}
        manager = self.threadlocal_manager
        manager.push(threadlocals)
        request.registry = registry
        request.invoke_subrequest = self.invoke_subrequest

        if use_tweens:
            handle_request = self.handle_request
        else:
            handle_request = self.orig_handle_request

        try:

            try:
                extensions = self.request_extensions
                if extensions is not None:
                    request._set_extensions(extensions)
                response = yield from handle_request(request)

                if request.response_callbacks:
                    request._process_response_callbacks(response)

                has_listeners and notify(NewResponse(request, response))

                return response

            finally:
                if request.finished_callbacks:
                    request._process_finished_callbacks()

        finally:
            manager.pop()

    def __call__(self, environ, start_response):
        """
        Accept ``environ`` and ``start_response``; create a
        :term:`request` and route the request to a :app:`Pyramid`
        view based on introspection of :term:`view configuration`
        within the application registry; call ``start_response`` and
        return an iterable.
        """
        #request = self.request_factory(environ)
        #response = yield from self.invoke_subrequest(request, use_tweens=True)

        #response = response(request.environ, start_response)
        myself = greenlet.getcurrent()
        future = asyncio.Future()
        asyncio.Task(sleeping(myself, future))
        myself.parent.switch()
        return bytes(future.result(), 'utf-8')       #return response
