import multiprocessing as mp
import threading as t
from builtins import classmethod
from time import time, sleep
from queue import Empty, Queue
from typing import Union

from stilly.logging import get_logger

Proc = Union[mp.Process, t.Thread]
Q = Union[mp.Queue, Queue]


class ActorProxy:
    def __init__(self, proc: Union[mp.Process, t.Thread], queue) -> None:
        self.proc = proc
        self.queue = queue
        self.heartbeat = time()


class Message:
    def __init__(self, destination: str='', body: str='') -> None:
        self.destination = destination
        self.body = body

    def __repr__(self) -> str:
        return '<{} destination={} body={}>'.format(
            self.__class__.__name__,
            self.destination,
            self.body,
        )


class ShutdownMessage(Message):
    def __init__(self, destination: str) -> None:
        super().__init__(destination=destination)


class HeartbeatMessage(Message):
    def __init__(self, destination: str, heartbeat_address: str='') -> None:
        super().__init__(destination=destination)
        self.heartbeat_address = heartbeat_address


class BaseActor:
    def __init__(self, address: str, input_queue: Q) -> None:
        self.address = address
        self.logger = get_logger()
        self.input_queue = input_queue
        self.running = False

    def log(self, message, level='debug'):
        log_msg = 'Actor: {} -- {}'.format(self.address, message)
        getattr(self.logger, level)(log_msg)

    @classmethod
    def start_actor(cls, address: str, queue: mp.Queue=None) -> ActorProxy:
        input_queue = mp.Queue() if queue is None else queue

        def start():
            a = cls(address, input_queue)
            a.run()

        proc = mp.Process(target=start)
        proc.start()
        return ActorProxy(proc=proc, queue=input_queue)

    def run(self):
        self.running = True
        while self.running:
            self.work()
            try:
                self._handle_msg(self.input_queue.get(timeout=.1))
            except Empty:
                pass

    def shutdown(self):
        self.running = False

    def _handle_msg(self, msg: Message):
        if isinstance(msg, ShutdownMessage):
            self.shutdown()
        else:
            self.handle_msg(msg)

    def handle_msg(self, msg: Message):
        """
        This hook lets you respond to messages that come in
        it should handle any message type that it expects
        """
        self.log(msg)

    def work(self):
        """
        This is a hook to allow you to do work in between messages
        This should not block for longer than the shutdown timeout
        :return:
        """
        pass


class ThreadActor(BaseActor):
    """
    Actor that uses a Thread instead of a Process
    The rest of the API should be the same
    """
    @classmethod
    def start_actor(cls, address: str, queue: Queue=None) -> ActorProxy:
        input_queue = Queue() if queue is None else queue

        def start():
            a = cls(address, input_queue)
            a.run()

        proc = t.Thread(target=start)
        proc.start()
        return ActorProxy(proc=proc, queue=input_queue)