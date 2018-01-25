from multiprocessing import Queue
from typing import Type

from stilly.actors.base_actor import BaseActor


def send_message(msg: dict):
    System.q.put(msg)


class System(BaseActor):
    q = Queue()

    def __init__(self, proc, queue):
        super().__init__(proc, queue)
        self.actors = {}

    def create_actor(self, actor_class: Type[BaseActor], address: str):
        ap = actor_class.start_actor(address)
        self.actors[address] = ap

    @classmethod
    def start_system(cls):
        return cls.start_actor('/local/system', cls.q)

    def handle_msg(self, msg: dict):
        print(msg)
        if msg.get('destination') == self.address:
            if msg.get('command') == 'launch_actor':
                self.create_actor(msg['actor_class'], address=msg['address'])
        elif msg.get('destination'):
            try:
                self.actors[msg['destination']].queue.put(msg, block=False)
            except AttributeError:
                self.logger.warning('Tried to send a msg to a nonexistant actor')

    def shutdown(self):
        for ap in self.actors.values():
            ap.queue.put({'command': 'shutdown'})
            ap.proc.join(1)
        self.running = False
