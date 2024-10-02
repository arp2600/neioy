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
from neioy.util import midicps
import neioy.supercollider as sc

server = sc.Server()
server.connect()

t = TempoClock()
t.set_tempo(100 / 60)

time.sleep(1)

print("Creating group...")
g = server.add_group(sc.AddAction.ADD_TO_TAIL)


def addFoo(note, *args):
    with server.bundle(t.time() + 0.25):
        server.add_synth("foo", "freq", midicps(note), *args, target=g)


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
        # add in a random sleep to demonstrate latency
        # compensation working.
        time.sleep(random.random() * 0.2)
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


print("Playing routines...")
t.play(main(x, y), quant=4)

input(f"Hit Enter to stop...\n")
server.disconnect()
