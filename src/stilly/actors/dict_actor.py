import multiprocessing as mp

import plyvel
from zmq.utils import jsonapi

from stilly.actors.thread_actor import ThreadActor
from stilly.communications.messages import RequestMessage, ResponseMessage


class StateActor(ThreadActor):
    def __init__(self, address, input_queue: mp.Queue,
                 supervisor_queue: mp.Queue):
        super().__init__(address, input_queue, supervisor_queue)
        todos = [
                {
                    'name': 'Start this tutorial',
                    'finished': True
                },
                {
                    'name': 'Finish this tutorial',
                    'finished': False
                }
            ]

        self.db = plyvel.DB('/tmp/testdb/', create_if_missing=True)
        self.db.put(b'todos::0', jsonapi.dumps(todos[0]))
        self.db.put(b'todos::1', jsonapi.dumps(todos[1]))

    def handle_msg(self, msg: RequestMessage):
        resp = {}
        if msg.body.get('action') == 'get':
            todos = self.db.iterator(prefix=b'todos::')
            if msg.body.get('id') is not None:
                id = msg.body['id']
                key = b'todos::' + bytes(str(id), 'utf-8')
                try:
                    todos.seek(key)
                    resp = jsonapi.loads(next(todos)[1])
                except StopIteration:
                    resp = {'error': 'Todo not found'}
            else:
                resp = [jsonapi.loads(todo) for key, todo in todos]
        resp_msg = ResponseMessage(destination=msg.return_address,
                                      return_id=msg.return_id,
                                      body=resp)
        self.log(resp_msg)
        self.send_msg(resp_msg)
