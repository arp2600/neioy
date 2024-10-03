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
from neioy.util import midicps, amp_comp
import neioy.supercollider as sc

t = TempoClock()
t.set_tempo(60 / 60)

server = sc.Server(t)
server.connect()

time.sleep(1)

print("Creating group...")

# %%

g = server.add_group(sc.AddAction.ADD_TO_TAIL)


def addFoo(note, *args):
    with server.bind():
        server.add_synth(
            "foo", "freq", note, *args, target=g, add_action=sc.AddAction.ADD_TO_TAIL
        )


# %%

notes = [38, 42, 45, 50, 54, 57, 62, 64, 66, 69, 74, 81, 90]
freqs = [midicps(i) ** 1.007 for i in notes]
shifts = [0.25 * i for i in range(len(notes))]

# %%


def play(index):
    pan = random.random() * 2 - 1
    while True:
        freq = freqs[index]
        freq = freq * (1 + random.random() * 0.03)
        amp = 0.1 * amp_comp(midicps(38), freq, 0.444)
        addFoo(freq, "amp", amp, "decay", 4.0, "pan", pan)
        yield 4 + shifts[index]


now = t.beats()
for i in range(len(notes)):
    t.sched_abs(play(i), now + 1 + shifts[i])

# %%

server.add_synth(
    "FreeVerb2x2",
    "outbus",
    0,
    "room",
    0.7,
    "mix",
    0.33,
    "damp",
    0.9,
    add_action=sc.AddAction.ADD_TO_TAIL,
)

# %%

input(f"Hit Enter to stop...\n")
server.disconnect()

# How about introducing a panning scheme where notes repel each other,
# and the closer two notes are to each other the stronger the repellant force.
# So say not 60 plays, and the pan is 0.1, and note 61 plays and the pan is 0.2
# The two notes will pan away from each other so 60 ends up at say -0.7 and 61 is at 0.9.
#
# Maybe lower notes have less force, so bass notes stay more central?
#
# Will have to implement a Synth.set method for this.
