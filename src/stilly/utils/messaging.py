import zmq.asyncio
from zmq.utils import jsonapi


def server_socket(address):
    sock = zmq.asyncio.Context.instance().socket(zmq.ROUTER)
    sock.bind(address)
    return sock


def send_socket(address):
    sock = zmq.asyncio.Context.instance().socket(zmq.REQ)
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