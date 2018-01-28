import multiprocessing as mp

from stilly.actors.base_actor import BaseActor, ActorProxy


class MultiprocActor(BaseActor):

    @classmethod
    def start_actor(cls, address: str, supervisor_queue: mp.Queue = None,
                    *args, **kwargs) -> ActorProxy:
        input_queue = mp.Queue()

        def start():
            a = cls(address, input_queue, supervisor_queue, *args, **kwargs)
            a.run()

        proc = mp.Process(target=start)
        proc.start()
        return ActorProxy(proc=proc, queue=input_queue)
