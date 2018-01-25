from multiprocessing import Process, Queue
from queue import Empty

from stilly.logging import get_logger


class ActorProxy:
    def __init__(self, proc, queue):
        self.proc = proc
        self.queue = queue


class BaseActor:
    def __init__(self, address: str, input_queue: Queue):
        self.address = address
        self.logger = get_logger()
        self.input_queue = input_queue
        self.running = False

    @classmethod
    def start_actor(cls, address: str, queue=None) -> ActorProxy:
        input_queue = Queue() if queue is None else queue

        def start():
            a = cls(address, input_queue)
            a.run()

        proc = Process(target=start)
        proc.start()
        return ActorProxy(proc=proc, queue=input_queue)

    def run(self):
        self.running = True
        try:
            while self.running:
                try:
                    self._handle_msg(self.input_queue.get(timeout=.1))
                except Empty:
                    pass
        finally:
            self.input_queue.close()

    def shutdown(self):
        self.running = False

    def _handle_msg(self, msg: dict):
        if msg.get('command') == 'shutdown':
            self.shutdown()
        else:
            self.handle_msg(msg)

    def handle_msg(self, msg: dict):
        print(msg)
