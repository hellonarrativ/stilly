import multiprocessing as mp

import plyvel
from zmq.utils import jsonapi

from stilly.actors.thread_actor import ThreadActor
from stilly.communications.messages import RequestMessage, ResponseMessage


class StateActor(ThreadActor):
    def __init__(self, address, input_queue: mp.Queue,
                 supervisor_queue: mp.Queue, initial_state,
                 filename='/tmp/lvldb'):
        super().__init__(address, input_queue, supervisor_queue)

        self.db = plyvel.DB(filename, create_if_missing=True)
        for key, value in initial_state.items():
            self.db.put(key, jsonapi.dumps(value))

    def handle_msg(self, msg: RequestMessage):
        resp = {}
        if msg.body.get('action') == 'get':

            if msg.body.get('id'):
                val = self.db.get(msg.body['id'])
                if val:
                    resp = jsonapi.loads(val)
                else:
                    resp = {'error': 'Todo not found'}
            elif msg.body.get('prefix'):
                items = self.db.iterator(prefix=msg.body['prefix'])
                resp = [jsonapi.loads(value) for key, value in items]
        resp_msg = ResponseMessage(destination=msg.return_address,
                                      return_id=msg.return_id,
                                      body=resp)
        self.log(resp_msg)
        self.send_msg(resp_msg)
