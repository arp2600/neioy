import time
import random
from icecream import ic

from neioy.clocks import TempoClock
from neioy.util import *
import neioy.supercollider as sc

server = sc.Server()
server.connect()

tempo_clock = server.get_clock()
tempo_clock.set_tempo(60 / 60)

time.sleep(1)


def triangle_note(note):
    root_freq = midicps(note)
    root_amp = 0.7

    while True:
        with server.bind():
            i = 1
            phase = 1
            while True:
                amp = root_amp * (1 / i**2) * phase
                phase *= -1
                freq = root_freq * i
                if freq >= (44100 / 2):
                    break

                server.add_synth("sinePerc", "freq", freq, "amp", amp, "decay", 3)

                i += 2

        yield 4


class Harmonic:
    def __init__(self, freq, amp):
        self.freq = freq
        self.amp = amp
        self.synth = server.add_synth("sine", "freq", freq, "amp", amp)

    def set_freq(self, freq):
        self.synth.set("freq", freq)

    def set_amp(self, amp):
        self.synth.set("amp", amp)

    def free(self):
        self.synth.free()


stop = False


def shifting():
    def create_harmonic_data(note):
        root_freq = midicps(note)
        root_amp = 0.5

        harmonic_data = []
        i = 1
        for _ in range(20):
            amp = root_amp * (1 / i**2)
            freq = root_freq * i
            if freq >= (44100 / 2):
                break
            harmonic_data.append((freq, amp))
            i += 2
        return harmonic_data

    harmonic_data = create_harmonic_data(69 - 12)

    # Initialize voices
    voices = []
    with server.bind():
        for data in harmonic_data:
            freq = data[0]
            amp = data[1]
            voice = Harmonic(freq, amp)
            voices.append(voice)

    yield 10

    while not stop:
        with server.bind():
            harmonic_data = create_harmonic_data(random.randint(50, 62))

            random.shuffle(harmonic_data)
            for i, data in enumerate(harmonic_data):
                freq = data[0]
                amp = data[1]
                voices[i].set_freq(freq)
                voices[i].set_amp(amp)
        yield 10

    for voice in voices:
        voice.free()


def sine_test():
    synth = server.add_synth("sine", "freq", midicps(69))
    yield 1
    synth.set("amp", 0.25)
    yield 1
    synth.set("amp", 1)
    yield 1
    synth.set("freq", midicps(75))
    yield 1

    note = 75
    while note >= 69:
        synth.set("freq", midicps(note))
        note -= 1
        yield (1 / 5)

    yield 1

    synth.free()


# tempo_clock.play(triangle_note(69))
# tempo_clock.play(sine_test())
tempo_clock.play(shifting())

input(f"Hit Enter to stop...\n")
stop = True
time.sleep(12)

server.disconnect()
