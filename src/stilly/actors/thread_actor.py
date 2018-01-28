import multiprocessing as mp
import threading as t

from stilly.actors.base_actor import BaseActor, ActorProxy


class ThreadActor(BaseActor):

    @classmethod
    def start_actor(cls, address: str, supervisor_queue: mp.Queue=None,
                    *args, **kwargs) -> ActorProxy:
        input_queue = mp.Queue()

        def start():
            a = cls(address, input_queue, supervisor_queue, *args, **kwargs)
            a.run()

        proc = t.Thread(target=start)
        proc.start()
        return ActorProxy(proc=proc, queue=input_queue)
