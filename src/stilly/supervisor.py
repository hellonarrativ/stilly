import asyncio
import multiprocessing as mp
import uvloop

import zmq
import zmq.asyncio
from zmq.utils import jsonapi

from .actor import HTTPActor, StateActor
from .server import app_factory

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def mp_actor(actor_class, address, **kwargs):
    a = actor_class(address=address, **kwargs)
    a.run()


class Supervisor:

    def __init__(self):
        self.actors = {}

    def run(self):
        self.actors['/local/http'] = {
            'proc': mp.Process(target=mp_actor, args=(HTTPActor, 'ipc:///tmp/actor1'),
                               kwargs={'app_factory': app_factory}),
            'address': 'ipc:///tmp/actor1'
        }
        self.actors['/local/state'] = {
            'proc': mp.Process(target=mp_actor, args=(StateActor, 'ipc:///tmp/actor2')),
            'address': 'ipc:///tmp/actor2'
        }

        self.actors['/local/http']['proc'].start()
        self.actors['/local/state']['proc'].start()

        loop = asyncio.get_event_loop()
        loop.create_task(self.get_messages('ipc:///tmp/master'))
        try:
            loop.run_forever()
        finally:
            remaining_tasks = asyncio.Task.all_tasks()
            loop.run_until_complete(asyncio.wait_for(asyncio.gather(*remaining_tasks), 5))
            loop.close()

    async def close_children(self):
        for actor in self.actors.values():
            sock = zmq.asyncio.Context.instance().socket(zmq.REQ)
            sock.connect(actor['address'])
            await sock.send_json({
                'command': 'shutdown',
            })

    async def get_messages(self, address):
        sock = zmq.asyncio.Context.instance().socket(zmq.ROUTER)
        loop = asyncio.get_event_loop()
        try:
            sock.bind(address)
            while True:
                recvd = await sock.recv_multipart()
                ret_add, _, raw_msg = recvd
                msg = jsonapi.loads(raw_msg)
                if msg.get('destination') == '/local/master' and msg.get('command') == 'shutdown':
                    await self.close_children()
                    return
                loop.create_task(self.handle_message(msg, sock, ret_add))
        finally:
            loop.create_task(self.close_socket(sock))
            loop.stop()

    @staticmethod
    async def close_socket(sock):
        print('Closing socket')
        sock.close()

    async def handle_message(self, message, sock, ret_add):
        resp = await self.send_message(message['destination'], message['command'], message['message'])
        await sock.send_multipart([ret_add, b'', jsonapi.dumps(resp)])

    async def send_message(self, destination, command, message=None):
        sock = zmq.asyncio.Context.instance().socket(zmq.REQ)
        sock.connect(self.actors.get(destination)['address'])
        await sock.send_json({
            'command': command,
            'message': message,
        })
        return await sock.recv_json()
