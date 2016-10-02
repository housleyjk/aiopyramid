Changes
=======

.. :changelog:

0.3.6 (2016-09-22)
------------------
    - Fix header normalization for Gunicorn

0.3.5 (2016-02-18)
------------------
    - Fix Gunicorn logging support

0.3.4 (2016-02-03)
------------------
    - Fix compatiblity with websockets 3+

0.3.3 (2015-11-21)
------------------
    - Merge fix for `ignore_websocket_closed` to allow chained exceptions
    - Add option to coerce bytes to str for uwsgi websockets

0.3.2 (2015-09-24)
------------------
    - Support Python3.5

0.3.1 (2015-01-31)
-------------------
    - Fix issues related to POST requests
    - Fix issues related to coroutine mappers
    - Sync with Gunicorn settings a la issue #917

0.3.0 (2014-12-06)
------------------
    - Add sphinx
    - Migrate README to sphinx docs
    - Add helpers for authentication
    - Deprecated aiopyramid.traversal, use aiopyramid.helpers.synchronize
    - Deprecated aiopyramid.tweens, moved examples to docs

0.2.4 (2014-10-06)
------------------
    - Fix issue with gunicorn websockets
    - Fix issue with class-based view mappers

0.2.3 (2014-10-01)
------------------
    - Fix issue with `synchronize`

0.2.2 (2014-09-30)
------------------
    - Update example tween to work with gunicorn
    - Add kwargs support to helpers
    - Add tox for testing
    - Add decorator `synchronize` for wrapping coroutines
    - Refactored mappers and tween example to use `synchronize`
    - Bug fixes

0.2.1 (2014-09-15)
------------------
    - Update scaffold example tests
    - Add test suite
    - Update README

0.2.0 (2014-09-01)
------------------
    - Update README
    - added websocket mappers for uwsgi and gunicorn
    - added websocket view class

0.1.2 (2014-08-02)
------------------
    - Update MANIFEST.in

0.1.0 (2014-08-01)
------------------
    - Update README ready for release
    - Added asyncio traverser (patched from `ResourceTreeTraverser`)
    - Added custom gunicorn worker
    - Fix issue with uwsgi and executor threads
    - Update starter scaffold

0.0.3 (2014-07-30)
------------------
    - Moving to an extension-based rather than patched-based approach
    - removed most code based on pyramid_asyncio except testing and scaffolds
    - added view mappers for running views in asyncio
    - added example tween that can come before or after synchronous tweens

0.0.2 (2014-07-22)
------------------
    - Removed Gunicorn specific code
    - disabled excview_tween_factory
    - made viewresult_to_response a coroutine
    - added dummy code for testing with uwsgi

0.0.1 (2014-07-22)
------------------
    - Migrated from pyramid_asyncio (Thank you Guillaume)
    - Removed worker.py and Gunicorn dependency
    - Added greenlet dependency
    - Changed contact information in setup.py
