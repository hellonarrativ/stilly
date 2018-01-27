from stilly.actors.aiohttp_actor import HTTPActor
from stilly.actors.dict_actor import StateActor
from stilly.system import send_message, System, LaunchActorMessage
from stilly.actors.base_actor import BaseActor, Message, ShutdownMessage, ThreadActor
from stilly_app.server import app_factory

supe = System.start_system()

send_message(Message(body={'msg': 'hi!'}))
send_message(LaunchActorMessage(BaseActor, '/local/a'))
send_message(LaunchActorMessage(StateActor, '/local/state'))
send_message(LaunchActorMessage(HTTPActor, '/local/http', app_factory=app_factory))

send_message(Message('/local/a', body={'msg': 'yo'}))
send_message(Message('/local/a', body={'msg': 'adrian'}))
send_message(Message('/local/a', body={'msg': 'yo'}))
#send_message(ShutdownMessage('/local/system'))
supe.proc.join()
