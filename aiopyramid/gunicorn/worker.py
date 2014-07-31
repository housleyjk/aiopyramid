import asyncio

from greenlet import greenlet
from aiohttp.worker import AsyncGunicornWorker as BaseWorker


class AsyncGunicornWorker(BaseWorker):

    def run(self):
        self._runner = asyncio.async(self._run(), loop=self.loop)
        main = greenlet(self.loop.run_until_complete)
        try:
            main.switch(self._runner)
        finally:
            self.loop.close()

    def handle_quit(self, sig, frame):
        self.alive = False

    handle_exit = handle_quit
