from stilly.system import System, LaunchActorMessage
from stilly.actors.base_actor import BaseActor, Message, ShutdownMessage

supe = System.start_system()

System.q.put(Message())
System.q.put(Message())
System.q.put(Message())
System.q.put(LaunchActorMessage(BaseActor, '/local/a'))
System.q.put(LaunchActorMessage(BaseActor, '/local/b'))

System.q.put(Message('/local/a'))
System.q.put(Message('/local/b'))
System.q.put(ShutdownMessage('/local/system'))
