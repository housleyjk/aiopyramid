.. :changelog:

0.0.2 (2014-07-22)
++++++++++++++++++
    - Removed Gunicorn specific code
    - disabled excview_tween_factory
    - made viewresult_to_response a coroutine
    - added dummy code for testing with uwsgi

0.0.1 (2014-07-22)
++++++++++++++++++
    - Migrated from pyramid_asyncio (Thank you Guillaume)
        - Removed worker.py and Gunicorn dependency
        - Added greenlet dependency
        - Changed contact information in setup.py
