import asyncio
import multiprocessing as mp

from stilly.actors.multiproc_actor import MultiprocActor
from stilly.communications.messages import ShutdownMessage


class HTTPActor(MultiprocActor):

    def __init__(self, address: str, input_queue: mp.Queue,
                 supervisor_queue: mp.Queue, app_factory):
        super().__init__(address, input_queue, supervisor_queue)
        self.app_factory = app_factory

        self.app = None
        self.handler = None
        self.srv = None

    def setup(self):
        self.app = self.app_factory()
        self.app['actor'] = self
        loop = asyncio.get_event_loop()
        self.handler = self.app.make_handler()
        f = loop.create_server(self.handler, '0.0.0.0', 8080)
        self.srv = loop.run_until_complete(f)
        self.logger.info('serving on {}'.format(self.srv.sockets[0].getsockname()))

    async def close(self):
        self.send_msg(ShutdownMessage('/local/system'))

    def cleanup(self):
        loop = asyncio.get_event_loop()

        self.srv.close()
        loop.run_until_complete(self.srv.wait_closed())
        loop.run_until_complete(self.app.shutdown())
        loop.run_until_complete(self.handler.shutdown(3))
        loop.run_until_complete(self.app.cleanup())
