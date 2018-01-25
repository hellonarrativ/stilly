from multiprocessing import Queue

from stilly.actors.base_actor import BaseActor, Message, ShutdownMessage


def send_message(msg: dict):
    System.q.put(msg)


class LaunchActorMessage(Message):
    def __init__(self, actor_class, address):
        super().__init__(destination='/local/system')
        self.actor_class = actor_class
        self.address = address


class System(BaseActor):
    q = Queue()

    def __init__(self, proc, queue):
        super().__init__(proc, queue)
        self.actors = {}

    def create_actor(self, msg: LaunchActorMessage):
        ap = msg.actor_class.start_actor(msg.address)
        self.actors[msg.address] = ap

    @classmethod
    def start_system(cls):
        return cls.start_actor('/local/system', cls.q)

    def handle_msg(self, msg: Message):
        print(msg)
        if msg.destination == self.address:
            if isinstance(msg, LaunchActorMessage):
                self.create_actor(msg)
        elif msg.destination:
            try:
                self.actors[msg.destination].queue.put(msg, block=False)
            except AttributeError:
                self.logger.warning('Tried to send a msg to a nonexistant actor')

    def shutdown(self):
        for address, ap in self.actors.items():
            ap.queue.put(ShutdownMessage(address))
            ap.proc.join(1)
            if ap.proc.is_alive():
                ap.proc.terminate()
        self.running = False
