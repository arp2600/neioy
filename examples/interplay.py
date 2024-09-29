import time
import queue
from dataclasses import dataclass, field
from typing import Any
import concurrent.futures
import enum
import random

from supriya.enums import RequestName
from supriya.osc import HealthCheck, OscMessage, ThreadedOscProtocol


def sleep_until(until):
    while time.time() < until:
        pass


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


class TempoClock:
    def __init__(self):
        self.tempo = 120 / 60
        self.routines = queue.PriorityQueue()

    def play(self, routine):
        self.routines.put(PrioritizedItem(0, routine))

    def run(self):
        # physical_time = time.time()
        # logical_time = time.time()

        while not self.routines.empty():
            x = self.routines.get()

            sleep_until(x.priority)

            physical_time = time.time()
            if x.priority == 0:
                logical_time = physical_time
            else:
                logical_time = x.priority

            try:
                schedule_time = next(x.item) + logical_time
                self.routines.put(PrioritizedItem(schedule_time, x.item))
            except StopIteration:
                pass


class ServerShutdownEvent(enum.Enum):
    QUIT = enum.auto()
    DISCONNECT = enum.auto()
    OSC_PANIC = enum.auto()
    PROCESS_PANIC = enum.auto()
    TOO_MANY_CLIENTS = enum.auto()


DEFAULT_HEALTHCHECK = HealthCheck(
    active=False,
    backoff_factor=1.5,
    max_attempts=5,
    request_pattern=["/status"],
    response_pattern=["/status.reply"],
    timeout=1.0,
)

shutdown_future: concurrent.futures.Future[
    ServerShutdownEvent
] = concurrent.futures.Future()

osc_protocol = ThreadedOscProtocol(
    name="",
    on_panic_callback=lambda: shutdown_future.set_result(ServerShutdownEvent.OSC_PANIC),
)


class Group:
    def __init__(self, osc_protocol, group_id):
        self.osc_protocol = osc_protocol
        self.group_id = group_id

    def free(self):
        msg = OscMessage(RequestName.NODE_FREE, self.group_id)
        self.osc_protocol.send(msg)

    def id(self):
        return self.group_id


def add_group(osc_protocol, group_id, add_action, target_node):
    msg = OscMessage(RequestName.GROUP_NEW, group_id, add_action, target_node)
    osc_protocol.send(msg)
    return Group(osc_protocol, group_id)


def add_synth(osc_protocol, synthdef_name, synth_id, add_action, target_node, *args):
    msg = OscMessage(
        RequestName.SYNTH_NEW, synthdef_name, synth_id, add_action, target_node, *args
    )
    osc_protocol.send(msg)


print("Connecting...")
osc_protocol.connect(
    ip_address="127.0.0.1",
    port=57110,
    healthcheck=DEFAULT_HEALTHCHECK,
)

time.sleep(1)

print("Creating group...")
g = add_group(osc_protocol, 34, 1, 1)

t = TempoClock()
t.tempo = 120 / 60

start = time.time()

scale = []
for octave in range(0, 12 * 7, 12):
    for note in [0, 2, 4, 5, 7, 9, 11]:
        scale.append(octave + note)

uid = 57


# yields the next note every 4 ticks
def notes1():
    while True:
        for note in range(8):
            yield scale[note] + 12 * 5
            yield None
            yield None
            yield None

        for note in range(7, -1, -1):
            yield scale[note] + 12 * 5
            yield None
            yield None
            yield None


def notes2():
    while True:
        for note in range(8):
            yield scale[note] + 12 * 5
            for _ in range(random.choice([1, 2, 2, 3, 3, 3])):
                yield None

        for note in range(7, -1, -1):
            yield scale[note] + 12 * 5
            for _ in range(random.choice([1, 2, 2, 3, 3, 3])):
                yield None


def r1():
    nr1 = notes1()
    nr2 = notes2()

    while True:
        global uid
        n1 = next(nr1)
        n2 = next(nr2)
        # n2 = None

        if n1 and not n2:
            add_synth(osc_protocol, "foo", uid, 1, g.id(), "note", n1)
            uid += 1
        elif n2 and not n1:
            add_synth(osc_protocol, "foo", uid, 1, g.id(), "note", n2)
            uid += 1
        elif n1 and n2:
            add_synth(
                osc_protocol, "foo", uid, 1, g.id(), "note", random.choice([n1, n2])
            )
            uid += 1

        yield 0.125


t.play(r1())

# Blocks until all queued routines have finished playing.
print("Playing routines...")
t.run()

time.sleep(1)

print("Freeing group...")
g.free()

print("Disconnecting...")
osc_protocol.disconnect()
