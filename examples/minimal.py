import time
import queue
from dataclasses import dataclass, field
from typing import Any
import concurrent.futures
import enum
import random
from threading import Thread
import __main__
from icecream import ic
import sys
from neioy.clocks import TempoClock

from supriya.enums import RequestName
from supriya.osc import HealthCheck, OscMessage, OscBundle, ThreadedOscProtocol

LATENCY = 0.25


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


t = TempoClock()
t.set_tempo(100 / 60)


def add_synth(osc_protocol, synthdef_name, synth_id, add_action, target_node, *args):
    msg = OscMessage(
        RequestName.SYNTH_NEW, synthdef_name, synth_id, add_action, target_node, *args
    )
    # osc_protocol.send(msg)
    bundle = OscBundle(timestamp=t.beats2seconds(t.beats()) + LATENCY, contents=(msg,))
    osc_protocol.send(bundle)


print("Connecting...")
osc_protocol.connect(
    ip_address="127.0.0.1",
    port=57110,
    healthcheck=DEFAULT_HEALTHCHECK,
)

time.sleep(1)

print("Creating group...")
g = add_group(osc_protocol, 34, 1, 1)


def midicps(note):
    return 2 ** ((note - 69) / 12) * 440


uid = 57


def addFoo(note, *args):
    global uid
    add_synth(osc_protocol, "foo", uid, 1, g.id(), "freq", midicps(note), *args)
    uid += 1


# base notes on the quarter with random harmony notes thrown in
def bassline(note):
    addFoo(note, "amp", 0.4, "decay", 4)

    for _ in range(12):
        # harmonising base notes played randomly
        if random.random() < 0.05:
            addFoo(note + 7, "amp", 0.2, "decay", 4, "pan", random.choice([-0.5, 0.5]))

        yield 0.5


def main(seq1, seq2):
    i = 0
    while True:
        xAmp = 0.3 if i % 3 == 0 else 0.2
        xDecay = 0.5 if i % 3 == 0 else 0.3
        xNote = seq1[i % len(seq1)]
        xPan = random.uniform(-1, 1)
        yPan = random.uniform(-1, 1)

        # first voice, plays seq1
        addFoo(xNote, "amp", xAmp, "decay", xDecay, "pan", xPan)

        yNote = seq2[i % len(seq2)]

        # second voice, plays seq2 and sometimes seq1
        if yNote > 0:
            addFoo(yNote + 12, "amp", xAmp * 0.6, "decay", 1.2, "pan", yPan * 0.5)
            yAmp2 = 0.1
        elif yNote < 1:
            addFoo(xNote + 12, "amp", yAmp2, "decay", xDecay, "pan", 0 - xPan)
            yAmp2 = yAmp2 * 1.4

        # base notes on the quarter
        if i % 12 == 0:
            # trigger a routine from a routine
            t.play(bassline(xNote - 12))

        yield 0.5
        i += 1


x = [52, 62, 61, 62, 64]
# yapf: disable
y = [
    67, 64, 67, 0, 0, 0, 64, -1, -1, -1, -1, -1,
    61, 62, 61, 0, 0, 0, 61, -1, -1, -1, -1, -1,
    61, 62, 64, 0, 0, 0, 64, -1, -1, -1, -1, -1,
    61, 62, 61, 0, 0, 0, 61, -1, -1, -1, -1, -1,
    61, 62, 64, 0, 0, 0, 64, -1, -1, -1, -1, -1
]
# yapf: enable
x = [i - 12 for i in x]
y = [i - 12 for i in y]


if sys.flags.interactive == 0:
    print("Playing routines...")
    t.play(main(x, y), quant=2)

    input(f"Hit Enter to stop...\n")
    osc_protocol.disconnect()
