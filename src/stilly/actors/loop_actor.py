import asyncio

from stilly.utils.messaging import server_socket, get_message, send_socket


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