from icecream import ic
from neioy.clocks import TempoClock
import time
import threading
import pytest
from contextlib import contextmanager


@pytest.fixture
def tempo_clock():
    clock = TempoClock()
    yield clock
    clock.stop()


def sleep(seconds):
    now = time.time()
    while time.time() < now + seconds:
        pass


def are_close(a, b, tolerance=1e-3):
    return abs(a - b) < tolerance


def test_beats(tempo_clock):
    tempo_clock.set_tempo(100 / 60)

    start = time.time()
    start_beats = tempo_clock.beats()

    # wait for 2 seconds
    while time.time() - start < 2:
        pass

    # the elapsed time multiplied by the tempo should match the elapsed beats
    delta_t = time.time() - start
    delta_b = tempo_clock.beats() - start_beats
    assert are_close(delta_t * 100 / 60, delta_b, tolerance=1e-2)


def test_beats2seconds(tempo_clock):
    tempo_clock.set_tempo(100 / 60)

    time.sleep(1)

    now_in_seconds = time.time()
    now_in_beats = tempo_clock.beats()

    assert are_close(now_in_seconds, tempo_clock.beats2seconds(now_in_beats),
                     1e-2)


def test_set_tempo(tempo_clock):
    tempo_clock.set_tempo(240 / 60)

    def r():
        # first beat should be 1 because we used quant=1 when calling play
        now = time.time()
        assert are_close(tempo_clock.beats(), 1)

        yield 1

        # duration in seconds between beats is 0.25 at 240 bpm
        delta_t = time.time() - now
        now += delta_t
        assert are_close(tempo_clock.beats(), 2)
        assert are_close(delta_t, 0.25, 1e-1)

        yield 1

        delta_t = time.time() - now
        now += delta_t
        assert are_close(tempo_clock.beats(), 3)
        assert are_close(delta_t, 0.25, 1e-1)

        tempo_clock.set_tempo(120 / 60)
        yield 1

        # duration in seconds between beats is 0.5 at 240 bpm
        delta_t = time.time() - now
        now += delta_t
        assert are_close(tempo_clock.beats(), 4)
        assert are_close(delta_t, 0.5, 1e-1)

    tempo_clock.play(r(), quant=1)
    tempo_clock.wait()


def test_wait(tempo_clock):
    tempo_clock.set_tempo(100 / 60)

    x = []

    def r():
        for i in range(3):
            yield 1
            x.append(1)

    assert len(x) == 0
    tempo_clock.play(r())
    tempo_clock.wait()
    assert len(x) == 3


def test_multiple_routines(tempo_clock):
    x = []

    def r1():
        for i in [0, 2, 4]:
            x.append(i)
            yield 0.2

    def r2():
        yield 0.1
        for i in [1, 3, 5]:
            x.append(i)
            yield 0.2

    tempo_clock.play(r1())
    tempo_clock.play(r2())
    tempo_clock.wait()
    assert x == [0, 1, 2, 3, 4, 5]


def test_passing_function_to_play(tempo_clock):
    x = []

    def r1():
        for i in [0, 2, 4]:
            x.append(i)
            yield 0.1

    def r2():
        yield 0.05
        for i in [1, 3, 5]:
            x.append(i)
            yield 0.1

    # use sched_abs to ensure both routines start at exactly the same time
    when = tempo_clock.beats() + 0.1
    tempo_clock.sched_abs(r1(), when)  # call tempo_clock.sched_abs with a generator
    tempo_clock.sched_abs(r2, when)  # call tempo_clock.sched_abs with a function
    tempo_clock.wait()
    assert x == [0, 1, 2, 3, 4, 5]


def test_exceptions(tempo_clock):
    x = []

    def r1():
        x.append(0)
        yield 0.1
        raise Exception('foo')
        x.append(1)

    def r2():
        yield 0.1
        x.append(2)
        yield 0.1
        x.append(3)

    # r1 raises an exception but that shouldn't prevent r2 from running to completion.
    tempo_clock.play(r1())
    tempo_clock.play(r2())
    tempo_clock.wait()

    def r3():
        x.append(4)
        yield 0.1
        x.append(5)

    # clock should still be able to run a new routine even after a previous routine raise
    # an exception.
    tempo_clock.play(r3())
    tempo_clock.wait()

    assert x == [0, 2, 3, 4, 5]


def test_sleep(tempo_clock):
    start = tempo_clock.beats()
    elapsed = tempo_clock.beats() - start
    assert 0.0 <= elapsed < 0.1

    start = tempo_clock.beats()
    tempo_clock.sleep(1.0)
    elapsed = tempo_clock.beats() - start
    assert 0.9 < elapsed < 1.1

    start = tempo_clock.beats()
    tempo_clock.sleep(2.0)
    elapsed = tempo_clock.beats() - start
    assert 1.9 < elapsed < 2.1
