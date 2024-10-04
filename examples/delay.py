import time
import random
from icecream import ic

from neioy.clocks import TempoClock
from neioy.util import *
import neioy.supercollider as sc

tempo_clock = TempoClock()
tempo_clock.set_tempo(120 / 60)

server = sc.Server(tempo_clock)
server.connect()


time.sleep(1)


def metronome():
    print(f"metronome: {tempo_clock.beats()}")
    while True:
        with server.bind():
            server.add_synth("sinePerc", "freq", midicps(69 - 12), "amp", 0.25)
        yield 1


# plays notes just offset of the beat by a random amount.
def offbeat(note):
    print(f"offbeat: {tempo_clock.beats()}")
    # beat = tempo_clock.beats()
    beat_tracker = BeatTracker(tempo_clock)

    while True:
        print(f"beat: {tempo_clock.beats()}")
        with server.bind():
            server.add_synth("sinePerc", "freq", midicps(note), "amp", 0.25)

        def offset(x):
            return random.random() * x

        yield (beat_tracker + 1) + offset(0.25)
        # yield yield_time + offset(0.05)
        # yield yield_time


def random_burst():
    beat_tracker = BeatTracker(tempo_clock)

    while True:
        print(tempo_clock.beats())
        num_notes = random.randint(1, 8)
        for i in range(num_notes):
            with server.bind():
                server.add_synth(
                    "sinePerc", "freq", midicps(random.randint(50, 70)), "amp", 0.25
                )
            yield 0.5

        yield beat_tracker + 4
        # beat_tracker.advance(4)
        # yield beat_tracker.yield_time()


def basic():
    beat_tracker = BeatTracker(tempo_clock)
    while True:
        print(tempo_clock.beats())
        r = random.random() * 0.1
        yield (beat_tracker + 1) + r


# tempo_clock.play(metronome(), 2)
# for note in [57, 61, 68]:
#     tempo_clock.play(offbeat(note), 2)
#     tempo_clock.play(offbeat(note + 12), 2)
# tempo_clock.play(random_burst(), 2)
tempo_clock.play(basic(), 2)

input(f"Hit Enter to stop...\n")
time.sleep(1)

server.disconnect()
