Changes
=======

.. :changelog:

0.2.2 (2014-09-15)
------------------
    - Update example tween to work with gunicorn
    - Add kwargs support to helpers

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
    - added example tween that can come before or after syncronous tweens

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
