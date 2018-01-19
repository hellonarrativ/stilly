import asyncio
import multiprocessing as mp
import uvloop

from stilly.utils.messaging import send_socket, server_socket, get_message
from stilly.actors.dict_actor import StateActor
from stilly.actors.aiohttp_actor import HTTPActor

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def mp_actor(actor_class, address, **kwargs):
    a = actor_class(address=address, **kwargs)
    a.run()


def get_actor_record(actor_config):
    classes = {
        'aiohttp': HTTPActor,
        'dict': StateActor,
    }
    address = 'ipc:///tmp/{}'.format(actor_config[0])
    return {
        'proc': mp.Process(
            target=mp_actor,
            args=(classes[actor_config[1]], address),
            kwargs=actor_config[2]
        ),
        'address': address,
    }


class Supervisor:

    def __init__(self, actor_configs):
        self.actors = {'/local/{}'.format(x[0]): get_actor_record(x) for x in actor_configs}

    def run(self):
        for a in self.actors.values():
            a['proc'].start()

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
            sock = send_socket(actor['address'])
            await sock.send_json({
                'command': 'shutdown',
            })

    async def get_messages(self, address):
        loop = asyncio.get_event_loop()
        sock = server_socket(address)
        try:
            while True:
                msg, responder = await get_message(sock)
                if msg.get('destination') == '/local/master' and msg.get('command') == 'shutdown':
                    await self.close_children()
                    return
                loop.create_task(self.handle_message(msg, responder))
        finally:
            loop.create_task(self.close_socket(sock))
            loop.stop()

    @staticmethod
    async def close_socket(sock):
        print('Closing supervisor socket')
        sock.close()

    async def handle_message(self, message, responder):
        destination = message['destination']
        command = message['command']
        body = message['body']
        resp = await self.send_message(destination, command, body)
        await responder.send(resp)

    async def send_message(self, destination, command, message=None):
        sock = send_socket(self.actors.get(destination)['address'])
        await sock.send_json({
            'command': command,
            'body': message,
        })
        return await sock.recv_json()
