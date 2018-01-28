from stilly.actors.aiohttp_actor import HTTPActor
from stilly.actors.level_db_actor import StateActor
from stilly.actors.multiproc_actor import MultiprocActor
from stilly.system import send_message, System, LaunchActorMessage
from stilly.communications.messages import Message, ShutdownMessage
from stilly_app.server import app_factory

supe = System.start_system()

initial_state = {
    b'todos::0': {
        'name': 'Start this tutorial',
        'finished': True
    },
    b'todos::1': {
        'name': 'Finish this tutorial',
        'finished': False
    }
}


send_message(Message(body={'msg': 'hi!'}))
send_message(LaunchActorMessage(MultiprocActor, '/local/a'))
send_message(LaunchActorMessage(StateActor, '/local/state', initial_state=initial_state))
send_message(LaunchActorMessage(HTTPActor, '/local/http', app_factory=app_factory))

send_message(Message('/local/a', body={'msg': 'yo'}))
send_message(Message('/local/a', body={'msg': 'adrian'}))
send_message(Message('/local/a', body={'msg': 'yo'}))
#send_message(ShutdownMessage('/local/system'))
supe.proc.join()
