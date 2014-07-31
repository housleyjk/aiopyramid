import asyncio


@asyncio.coroutine
def run_in_greenlet(back, future, func, *args):
    try:
        result = yield from func(*args)
    except Exception as ex:
        future.set_exception(ex)
    else:
        future.set_result(result)
    finally:
        back.switch()
