"""
The aiopyramid.traversal module is deprecated, use aiopyramid.helpers.synchronize instead.
See http://aiopyramid.readthedocs.org/en/latest/features.html#traversal.
"""  # NOQA

import asyncio
import warnings

from pyramid.traversal import (
    ResourceTreeTraverser as TraverserBase,
    is_nonstr_iter,
    split_path_info,
)
from pyramid.exceptions import URLDecodeError
from pyramid.interfaces import VH_ROOT_KEY
from pyramid.compat import decode_path_info

from .helpers import synchronize

SLASH = "/"

warnings.warn(__doc__, DeprecationWarning)


@synchronize
@asyncio.coroutine
def traverse(
    i,
    ob,
    view_selector,
    vpath_tuple,
    vroot_idx,
    vroot,
    vroot_tuple,
    root,
    subpath,
):
    """
    A version of :func:`pyramid.traversal.traverse` that expects `__getitem__`
    to be a :term:`coroutine`.
    """

    for segment in vpath_tuple:
        if segment[:2] == view_selector:
            return {
                'context': ob,
                'view_name': segment[2:],
                'subpath': vpath_tuple[i + 1:],
                'traversed': vpath_tuple[:vroot_idx + i + 1],
                'virtual_root': vroot,
                'virtual_root_path': vroot_tuple,
                'root': root,
            }
        try:
            getitem = ob.__getitem__
        except AttributeError:
            return {
                'context': ob,
                'view_name': segment,
                'subpath': vpath_tuple[i + 1:],
                'traversed': vpath_tuple[:vroot_idx + i + 1],
                'virtual_root': vroot,
                'virtual_root_path': vroot_tuple,
                'root': root,
            }

        try:
            tsugi = yield from getitem(segment)
        except KeyError:
            return {
                'context': ob,
                'view_name': segment,
                'subpath': vpath_tuple[i + 1:],
                'traversed': vpath_tuple[:vroot_idx + i + 1],
                'virtual_root': vroot,
                'virtual_root_path': vroot_tuple,
                'root': root,
            }
        if i == vroot_idx:
            vroot = tsugi
        ob = tsugi
        i += 1

    return {
        'context': ob,
        'view_name': "",
        'subpath': subpath,
        'traversed': vpath_tuple,
        'virtual_root': vroot,
        'virtual_root_path': vroot_tuple,
        'root': root
    }


class AsyncioTraverser(TraverserBase):
    """
    Traversal algorithm patched from the default traverser to execute
    __getitem__ as a coroutine.
    """

    def __call__(self, request):
        environ = request.environ
        matchdict = request.matchdict

        if matchdict is not None:

            path = matchdict.get('traverse', SLASH) or SLASH
            if is_nonstr_iter(path):
                # this is a *traverse stararg (not a {traverse})
                # routing has already decoded these elements, so we just
                # need to join them
                path = '/' + SLASH.join(path) or SLASH

            subpath = matchdict.get('subpath', ())
            if not is_nonstr_iter(subpath):
                # this is not a *subpath stararg (just a {subpath})
                # routing has already decoded this string, so we just need
                # to split it
                subpath = split_path_info(subpath)

        else:
            # this request did not match a route
            subpath = ()
            try:
                # empty if mounted under a path in mod_wsgi, for example
                path = request.path_info or SLASH
            except KeyError:
                # if environ['PATH_INFO'] is just not there
                path = SLASH
            except UnicodeDecodeError as e:
                raise URLDecodeError(e.encoding, e.object, e.start, e.end,
                                     e.reason)

        if VH_ROOT_KEY in environ:
            # HTTP_X_VHM_ROOT
            vroot_path = decode_path_info(environ[VH_ROOT_KEY])
            vroot_tuple = split_path_info(vroot_path)
            vpath = vroot_path + path
            vroot_idx = len(vroot_tuple) - 1
        else:
            vroot_tuple = ()
            vpath = path
            vroot_idx = - 1

        root = self.root
        ob = vroot = root

        if vpath == SLASH:
            vpath_tuple = ()
        else:
            i = 0
            view_selector = self.VIEW_SELECTOR
            vpath_tuple = split_path_info(vpath)
            return traverse(
                i,
                ob,
                view_selector,
                vpath_tuple,
                vroot_idx,
                vroot,
                vroot_tuple,
                root,
                subpath,
            )

        return {
            'context': ob,
            'view_name': "",
            'subpath': subpath,
            'traversed': vpath_tuple,
            'virtual_root': vroot,
            'virtual_root_path': vroot_tuple,
            'root': root
        }
