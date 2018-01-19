from stilly.actors.loop_actor import LoopActor


class StateActor(LoopActor):
    def __init__(self, address):
        super().__init__(address)
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

    async def process_message(self, message):
        command = message.get('command')
        body = message.get('body')
        if command == 'get':
            if body.get('id') is not None:
                id = body['id']
                if id >= len(self.state['TODOS']):
                    return {'error': 'Todo not found'}
                return self.state['TODOS'][id]
            return self.state['TODOS']
