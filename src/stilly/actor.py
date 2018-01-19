import asyncio

from stilly.messaging import server_socket, get_message, send_socket


class LoopActor:

    def __init__(self, address):
        self.address = address

    def setup_tasks(self):
        pass

    def shutdown(self):
        pass

    def run(self):
        self.setup_tasks()
        loop = asyncio.get_event_loop()
        loop.create_task(self.get_messages(self.address))
        try:
            loop.run_forever()
        finally:
            self.shutdown()
            remaining_tasks = asyncio.Task.all_tasks()
            loop.run_until_complete(asyncio.wait_for(asyncio.gather(*remaining_tasks), 5))
            loop.close()

    async def get_messages(self, address):
        loop = asyncio.get_event_loop()
        sock = server_socket(address)
        try:
            while True:
                msg, responder = await get_message(sock)
                if msg.get('command') == 'shutdown':
                    return
                loop.create_task(self.handle_message(msg, responder))
        finally:
            loop.create_task(self.close_socket(sock))
            loop.stop()

    @staticmethod
    async def close_socket(sock):
        print('Closing socket')
        sock.close()

    async def handle_message(self, message, responder):
        resp = await self.process_message(message)
        await responder.send(resp)

    async def process_message(self, message):
        pass

    async def send_message(self, destination, command, body=None):
        sock = send_socket('ipc:///tmp/master')
        await sock.send_json({
            'destination': destination,
            'command': command,
            'body': body,
        })
        return await sock.recv_json()


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
        print('serving on', self.srv.sockets[0].getsockname())

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


class StateActor(LoopActor):
    def __init__(self, address):
        super().__init__(address)
        self.state = {
            'TODOS': [
                {
                    'name': 'Start this tutorial',
                    'finished': True
                },
                {
                    'name': 'Finish this tutorial',
                    'finished': False
                }
            ]
        }

    async def process_message(self, message):
        command = message.get('command')
        body = message.get('body')
        if command == 'get':
            if body.get('id') is not None:
                id = body['id']
                if id >= len(self.state['TODOS']):
                    return {'error': 'Todo not found'}
                return self.state['TODOS'][id]
            return self.state['TODOS']
