from time import sleep

from stilly.actors.multiproc_actor import EchoActor
from stilly.communications.messages import Message, ShutdownMessage
from stilly.system import LaunchActorMessage, System
from stilly.utils.messaging import Mailbox, send_message




supe = System.start_system()
sleep(1)
mailbox = Mailbox('/local/test')
sleep(1)
send_message(LaunchActorMessage(EchoActor, '/local/echo'))
sleep(1)
send_message(Message('/local/echo', {'dest': '/local/test', 'text': 'wut'}))
resp = mailbox.retrieve()


def test_stilly_system():
    """
    1. Start the stilly system from a process
    2. Verify that it reports good status
    3. Start another process and check that the system
    can be accessed from that as well.
    :return:
    """


    supe = System.start_system()

    # start mailbox at '/self/test'
    mailbox = Mailbox('/local/test')
    # send_message('/local', startActor(echo_server))
    send_message(LaunchActorMessage(EchoActor, '/local/echo'))
    # send message('/local/echo')
    sleep(1)

    send_message(Message('/local/echo', {'dest': '/local/test', 'text': 'wut'}))
    # receive message
    sleep(3)
    resp = mailbox.retrieve()
    assert resp.body == {'text': 'wut'}
    send_message(ShutdownMessage('/local/system'))
    print(supe.proc)
    assert False


def test_stilly_consensus():
    pass
    # start 1 system with a set of 3 raft addresses
    # verify no master
    # start 1 more
    # verify master
    # start third
    # verify it joins
    # verify message to each of the 3 starts an actor