from stilly.system import send_message, System, LaunchActorMessage
from stilly.actors.base_actor import BaseActor, Message, ShutdownMessage, ThreadActor

supe = System.start_system()

send_message(Message(body='hi!'))
send_message(LaunchActorMessage(BaseActor, '/local/a'))
send_message(LaunchActorMessage(ThreadActor, '/local/b'))

send_message(Message('/local/a', body='yo'))
send_message(Message('/local/b', body='adrian'))
send_message(Message('/local/a', body='yo'))
send_message(ShutdownMessage('/local/system'))
supe.proc.join()
