import zmq.asyncio
from zmq.utils import jsonapi

from stilly.communications.messages import Message


def server_socket(address):
    sock = zmq.asyncio.Context.instance().socket(zmq.PULL)
    sock.bind(f'ipc:///tmp{address}')
    return sock


def send_socket(address):
    sock = zmq.asyncio.Context.instance().socket(zmq.PUSH)
    sock.connect(address)
    return sock


async def get_message(sock):
    ident, _, raw_msg = await sock.recv_multipart()
    msg = jsonapi.loads(raw_msg)
    return msg, Responder(sock, ident)


class Responder:
    def __init__(self, sock, ident):
        self.sock = sock
        self.ident = ident

    async def send(self, response):
        frames = [self.ident, b'', jsonapi.dumps(response)]
        await self.sock.send_multipart(frames)

    def close(self):
        self.sock.close()


class Mailbox:
    def __init__(self, address):
        self.sock = zmq.Context.instance().socket(zmq.PULL)
        self.sock.bind(f'ipc:///tmp{address}')

    def retrieve(self):
        return self.sock.recv_pyobj(flags=zmq.NOBLOCK)


def send_message(msg: Message):
    sock = zmq.Context.instance().socket(zmq.PUSH)
    sock.connect(f'ipc:///tmp{msg.destination}')
    sock.send_pyobj(msg)
