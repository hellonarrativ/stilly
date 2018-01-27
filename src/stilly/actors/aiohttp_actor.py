import asyncio

from stilly.actors.loop_actor import LoopActor
from stilly.system import send_message
from stilly.utils.messaging import send_socket


class HTTPActor(LoopActor):

    def __init__(self, address, app_factory):
        super().__init__(address)
        self.app_factory = app_factory

        self.app = None
        self.handler = None
        self.srv = None

    def setup_tasks(self):
        self.app = self.app_factory()
        self.app['actor'] = self
        loop = asyncio.get_event_loop()
        self.handler = self.app.make_handler()
        f = loop.create_server(self.handler, '0.0.0.0', 8080)
        self.srv = loop.run_until_complete(f)
        self.logger.info('serving on {}'.format(self.srv.sockets[0].getsockname()))

    async def close(self):
        sock = send_socket('ipc:///tmp/master')
        await sock.send_json({
            'destination': '/local/master',
            'command': 'shutdown',
        })

    def shutdown(self):
        loop = asyncio.get_event_loop()
        self.srv.close()
        loop.run_until_complete(self.srv.wait_closed())
        loop.run_until_complete(self.app.shutdown())
        loop.run_until_complete(self.handler.shutdown(3))
        loop.run_until_complete(self.app.cleanup())
