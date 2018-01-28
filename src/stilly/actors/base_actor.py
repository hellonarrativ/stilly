import asyncio
import multiprocessing as mp
import threading as t
from builtins import classmethod
from time import time
from queue import Empty
from typing import Union
from uuid import uuid4

from stilly.communications.messages import Message, ShutdownMessage, RequestMessage, ResponseMessage
from stilly.logging import get_logger

Proc = Union[mp.Process, t.Thread]


class ActorProxy:
    def __init__(self, proc: Union[mp.Process, t.Thread], queue) -> None:
        self.proc = proc
        self.queue = queue
        self.heartbeat = time()


class BaseActor:
    def __init__(self, address: str, input_queue: mp.Queue,
                 supervisor_queue: mp.Queue, *args, **kwargs) -> None:
        self.address = address
        self.logger = get_logger()
        self.input_queue = input_queue
        self.supervisor_queue = supervisor_queue
        self.running = False
        self.pending_responses = {}

    def log(self, message, level='debug'):
        log_msg = 'Actor: {} -- {}'.format(self.address, message)
        getattr(self.logger, level)(log_msg)

    @classmethod
    def start_actor(cls, address: str, supervisor_queue: mp.Queue=None,
                    *args, **kwargs) -> ActorProxy:
        raise NotImplementedError()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.setup()

        async def get():
            while not loop._stopping:
                try:
                    # keep this timeout short as it blocks the event loop
                    # TODO need a non-blocking implementation of multiprocessing.Queue
                    loop.create_task(self._handle_msg(self.input_queue.get(timeout=.01)))
                except Empty:
                    # Yield to the event loop to allow other coroutines to run
                    await asyncio.sleep(0)

        loop.create_task(get())
        try:
            loop.run_forever()
        finally:
            self.cleanup()
            remaining_tasks = asyncio.Task.all_tasks()
            loop.run_until_complete(asyncio.wait_for(asyncio.gather(*remaining_tasks), 5))
            loop.close()

    def setup(self):
        pass

    def cleanup(self):
        pass

    def shutdown(self):
        self.log('Shutting down')
        asyncio.get_event_loop().stop()

    async def _handle_msg(self, msg: Message):
        self.log(msg)
        if isinstance(msg, ShutdownMessage):
            self.shutdown()
        elif isinstance(msg, ResponseMessage):
            ret_id = msg.return_id
            ev = self.pending_responses[ret_id][0]
            self.pending_responses[ret_id] = (None, msg)
            ev.set()
        else:
            self.handle_msg(msg)

    def handle_msg(self, msg: Message):
        """
        This hook lets you respond to messages that come in
        it should handle any message type that it expects
        """
        self.log(msg)

    def send_msg(self, msg: Message):
        self.supervisor_queue.put(msg)

    async def get_response(self, destination: str, body: dict):
        """
        create a unique return id and associate an asyncio.Event
        flag with it. Register the Event with the return id on the
        main event loop. Wait until the flag becomes true and
        fetch the result
        """
        event = asyncio.Event()
        id = uuid4()
        self.pending_responses[id] = (event, None)
        self.send_msg(RequestMessage(destination,
                                     return_address=self.address,
                                     return_id=id,
                                     body=body))
        await event.wait()
        return self.pending_responses.pop(id)[1].body

    def work(self):
        """
        This is a hook to allow you to do work in between messages
        This should not block for longer than the shutdown timeout
        :return:
        """
        pass
