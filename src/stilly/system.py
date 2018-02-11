import asyncio
from multiprocessing import Queue, Process
from time import time
from typing import Dict
from typing import Type

from stilly.actors.base_actor import ActorProxy, BaseActor
from stilly.actors.multiproc_actor import MultiprocActor
from stilly.communications.messages import Message, ShutdownMessage, HeartbeatMessage

system_queue: Queue = None


def send_message(msg: Message):
    system_queue.put(msg)


class ActorRecord:
    def __init__(self, actor_class: Type[BaseActor], address: str,
                 *args, **kwargs) -> None:
        self.actor_class = actor_class
        self.address = address
        self.args = args
        self.kwargs = kwargs
        self.instance: ActorProxy = None


class LaunchActorMessage(Message):
    def __init__(self, actor_class, address, *args, **kwargs):
        super().__init__(destination='/local/system')
        self.actor_record = ActorRecord(actor_class, address, *args, **kwargs)


class System(MultiprocActor):

    def __init__(self, proc, input_queue, supervisor_queue) -> None:
        super().__init__(proc, input_queue, supervisor_queue)
        self.actors: Dict[str, ActorRecord] = {}

    def create_actor(self, msg: LaunchActorMessage) -> None:
        record: ActorRecord = msg.actor_record
        ap = record.actor_class.start_actor(record.address,
                                            self.input_queue, *record.args, **record.kwargs)
        record.instance = ap
        self.actors[msg.actor_record.address] = record

    @classmethod
    def start_system(cls):
        global system_queue
        ap = cls.start_actor('/local/system')
        system_queue = ap.queue
        return ap

    async def _handle_msg(self, msg: Message):
        self.log(msg)
        if msg.destination == self.address:
            if isinstance(msg, LaunchActorMessage):
                self.create_actor(msg)
            elif isinstance(msg, ShutdownMessage):
                self.shutdown()
            elif isinstance(msg, HeartbeatMessage):
                self.actors[msg.heartbeat_address].instance.heartbeat = time()
        elif msg.destination:
            try:
                self.actors[msg.destination].instance.queue.put(msg, block=False)
            except AttributeError:
                self.logger.warning('Tried to send a msg to a nonexistant actor')

    def shutdown(self):
        self.log('Shutting down System')
        for address, record in self.actors.items():
            record.instance.queue.put(ShutdownMessage(address))
            record.instance.proc.join(1)
            if isinstance(record.instance.proc, Process) and record.instance.proc.is_alive():
                record.instance.proc.terminate()
        self.input_queue.close()
        asyncio.get_event_loop().stop()

    def work(self):
        for address, record in list(self.actors.items()):
            self.heartbeat(address, record.instance)

    def heartbeat(self, address: str, ap: ActorProxy):
        now = time()
        if now - ap.heartbeat > 2:
            ap.proc.join(1)
            self.actors.pop(address)
            self.log('actor {} has failed'.format(address))
        elif now - ap.heartbeat > 1:
            ap.queue.put(HeartbeatMessage(address))
