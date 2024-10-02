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

server = sc.Server()
server.connect()

tc = TempoClock()
tc.set_tempo(60 / 60)


def play():
    s = server.add_synth("default", "freq", midicps(60))
    yield 1
    s.set("freq", midicps(64))
    yield 1
    s.free()

    yield 0.5

    s = server.add_synth("nsetntest", "freqs", [midicps(69), midicps(71)])
    yield 1
    s.setn("freqs", midicps(65), midicps(76))
    yield 1
    s.setn("freqs", midicps(61), midicps(80))


tc.sched(play(), 2)

input(f"Hit Enter to stop...\n")
server.disconnect()
