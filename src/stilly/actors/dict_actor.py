import multiprocessing as mp

from stilly.actors.base_actor import BaseActor, Message, RequestMessage, ResponseMessage


class StateActor(BaseActor):
    def __init__(self, address, input_queue: mp.Queue,
                 supervisor_queue: mp.Queue):
        super().__init__(address, input_queue, supervisor_queue)
        self.state = {
            'TODOS': [
                {
                    'name': 'Start this tutorial',
                    'finished': True
                },
                {
                    'name': 'Finish this tutorial',
                    'finished': False
                }
            ]
        }

    def handle_msg(self, msg: RequestMessage):
        resp = {}
        if msg.body.get('action') == 'get':
            if msg.body.get('id') is not None:
                id = msg.body['id']
                if id >= len(self.state['TODOS']):
                    resp = {'error': 'Todo not found'}
                else:
                    resp = self.state['TODOS'][id]
            else:
                resp = self.state['TODOS']
        resp_msg = ResponseMessage(destination=msg.return_address,
                                      return_id=msg.return_id,
                                      body=resp)
        self.log(resp_msg)
        self.send_msg(resp_msg)
