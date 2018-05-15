import multiprocessing as mp

from stilly.actors.base_actor import BaseActor, ActorProxy
from stilly.communications.messages import Message
from stilly.utils.messaging import send_message


class MultiprocActor(BaseActor):

    @classmethod
    def start_actor(cls, address: str, *args, **kwargs) -> ActorProxy:
        def start():
            a = cls(address, *args, **kwargs)
            a.run()

        proc = mp.Process(target=start)
        proc.start()
        return ActorProxy(proc=proc)


class EchoActor(MultiprocActor):
    def handle_msg(self, msg: Message):
        dest = msg.body['dest']
        txt = msg.body['text']
        send_message(Message(destination=dest, body={'text': txt}))
