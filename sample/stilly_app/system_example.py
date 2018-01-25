from stilly.system import System
from stilly.actors.base_actor import BaseActor


supe = System.start_system()

System.q.put({'a': 7})
System.q.put({'a': 7})

System.q.put({'a': 7})
System.q.put({'destination': '/local/system', 'command': 'launch_actor', 'actor_class': BaseActor, 'address': '/local/a'})
System.q.put({'destination': '/local/system', 'command': 'launch_actor', 'actor_class': BaseActor, 'address': '/local/b'})
System.q.put({'destination': '/local/a', 'command': 'HI'})
System.q.put({'destination': '/local/b', 'command': 'HI'})
System.q.put({'destination': '/local/system', 'command': 'shutdown'})


