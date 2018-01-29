import asyncio
import multiprocessing as mp
import random
from queue import Empty
from time import time
from typing import List

from stilly.actors.thread_actor import ThreadActor
from stilly.communications.messages import Message


class LogEntry:
    def __init__(self, index, term, command):
        self.index = index
        self.term = term
        self.command = command


class RequestVoteMessage(Message):
    def __init__(self, destination: str, term: int, candidate_id: str,
                 last_log_index: int, last_log_term: int):
        super().__init__(destination=destination)
        self.term = term
        self.candidate_id = candidate_id
        self.last_log_index = last_log_index
        self.last_log_term = last_log_term


class VoteResponseMessage(Message):
    def __init__(self, destination: str, term: int, vote_granted: bool):
        super().__init__(destination=destination)
        self.term = term
        self.vote_granted = vote_granted


class AppendEntriesMessage(Message):
    def __init__(self, destination: str, term: int, leader_id: str,
                 prev_log_index: int, prev_log_term: int, entries: List[LogEntry],
                 leader_commit: int):

        super().__init__(destination=destination)
        self.term = term
        self.leader_id = leader_id
        self.prev_log_index = prev_log_index
        self.prev_log_term = prev_log_term
        self.entries = entries
        self.leader_commit = leader_commit


class RaftActor(ThreadActor):
    def __init__(self, address, input_queue: mp.Queue,
                 supervisor_queue: mp.Queue, servers: List[str]):
        super().__init__(address, input_queue, supervisor_queue)

        self.is_leader = False
        self.interval = 1
        self.current_term = 0
        self.voted_for = None
        self.log_entries: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0
        self.cluster = servers
        self.timeout = None
        self.votes_received = 0
        self.server_next = {}
        self.reset_timeout()

    def reset_timeout(self):
        if self.is_leader:
            self.timeout = time() + self.interval
        else:
            self.timeout = time() + random.uniform(2 * self.interval, 4 * self.interval)

    def send_request_vote(self, address):
        req = RequestVoteMessage(
            destination=address,
            term=self.current_term,
            candidate_id=self.address,
            last_log_index=self.log_entries[-1].index if self.log_entries else 0,
            last_log_term=self.log_entries[-1].term if self.log_entries else 0
        )
        self.send_msg(req)

    def respond_to_vote_request(self, msg: RequestVoteMessage):
        last_term = self.log_entries[-1].term if self.log_entries else 0
        last_index = self.log_entries[-1].index if self.log_entries else 0
        if msg.term >= self.current_term \
            and msg.last_log_term >= last_term \
            and msg.last_log_index >= last_index:
                self.current_term = msg.term
                self.votes_received = 0
                self.voted_for = msg.candidate_id
                self.send_msg(VoteResponseMessage(destination=msg.candidate_id,
                                                  term=self.current_term,
                                                  vote_granted=True))
        else:
            self.send_msg(VoteResponseMessage(destination=msg.candidate_id,
                                              term=self.current_term,
                                              vote_granted=False))

    def handle_vote_response(self, msg: VoteResponseMessage):
        if msg.vote_granted and msg.term == self.current_term:
            self.votes_received += 1
            if self.votes_received > len(self.cluster)/2:
                self.is_leader = True
                self.votes_received = 0
                for server in self.cluster:
                    self.server_next[server] = self.last_applied + 1
                self.send_heartbeats()
        else:
            if msg.term > self.current_term:
                self.current_term = msg.term
                self.votes_received = 0

    def request_vote(self):
        self.votes_received = 1
        self.current_term += 1
        self.voted_for = self.address
        self.reset_timeout()
        for address in [x for x in self.cluster if x != self.address]:
            self.send_request_vote(address)

    def send_heartbeats(self):
        self.log('I am the leader')
        for server in [x for x in self.cluster if x != self.address]:
            prev = self.log_entries[-1] if self.log_entries else LogEntry(0, 0, {})
            self.send_append_log(server, prev, [])
        self.reset_timeout()

    def recieve_append_entries(self, msg: AppendEntriesMessage):
        # TODO finish this
        if msg.term >= self.current_term:
            if self.is_leader:
                self.is_leader = False
            self.reset_timeout()
            self.log('%s is the leader' % msg.leader_id)

    def send_append_log(self, address, prev_entry: LogEntry, entries: List[LogEntry]):
        self.send_msg(AppendEntriesMessage(
            destination=address,
            term=self.current_term,
            leader_id=self.address,
            leader_commit=self.commit_index,
            prev_log_index=prev_entry.index,
            prev_log_term=prev_entry.term,
            entries=entries
        ))

    def append_log(self, command):
        self.last_applied += 1
        entry = LogEntry(index=self.last_applied, term=self.current_term, command=command)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.setup()

        async def get():
            while not loop._stopping:
                try:
                    # keep this timeout short as it blocks the event loop
                    # TODO need a non-blocking implementation of multiprocessing.Queue
                    loop.create_task(self._handle_msg(self.input_queue.get(timeout=.01)))
                except Empty:
                    # Yield to the event loop to allow other coroutines to run
                    if time() > self.timeout:
                        if self.is_leader:
                            self.send_heartbeats()
                        else:
                            self.request_vote()
                    await asyncio.sleep(0)

        loop.create_task(get())
        try:
            loop.run_forever()
        finally:
            self.cleanup()
            remaining_tasks = asyncio.Task.all_tasks()
            loop.run_until_complete(asyncio.wait_for(asyncio.gather(*remaining_tasks), 5))
            loop.close()

    def handle_msg(self, msg: Message):
        if isinstance(msg, RequestVoteMessage):
            self.respond_to_vote_request(msg)
        elif isinstance(msg, VoteResponseMessage):
            self.handle_vote_response(msg)
        elif isinstance(msg, AppendEntriesMessage):
            self.recieve_append_entries(msg)
