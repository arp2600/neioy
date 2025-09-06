from icecream import ic
from neioy.clocks import TempoClock
import time
import threading


def sleep(seconds):
    now = time.time()
    while time.time() < now + seconds:
        pass


def are_close(a, b, tolerance=1e-3):
    return abs(a - b) < tolerance


def test_beats():
    t = TempoClock()
    t.set_tempo(100 / 60)

    start = time.time()
    start_beats = t.beats()

    # run the clock for 4 seconds
    while time.time() - start < 2:
        pass

    # the elapsed time multiplied by the tempo should match the elapsed beats
    delta_t = time.time() - start
    delta_b = t.beats() - start_beats
    assert are_close(delta_t * 100 / 60, delta_b, tolerance=1e-2)


def test_beats2seconds():
    t = TempoClock()
    t.set_tempo(100 / 60)

    time.sleep(1)

    now_in_seconds = time.time()
    now_in_beats = t.beats()

    assert are_close(now_in_seconds, t.beats2seconds(now_in_beats), 1e-2)


def test_set_tempo():
    t = TempoClock()
    t.set_tempo(240 / 60)

    def r():
        # first beat should be 1 because we used quant=1 when calling play
        now = time.time()
        assert are_close(t.beats(), 1)

        yield 1

        # duration in seconds between beats is 0.25 at 240 bpm
        delta_t = time.time() - now
        now += delta_t
        assert are_close(t.beats(), 2)
        assert are_close(delta_t, 0.25, 1e-1)

        yield 1

        delta_t = time.time() - now
        now += delta_t
        assert are_close(t.beats(), 3)
        assert are_close(delta_t, 0.25, 1e-1)

        t.set_tempo(120 / 60)
        yield 1

        # duration in seconds between beats is 0.5 at 240 bpm
        delta_t = time.time() - now
        now += delta_t
        assert are_close(t.beats(), 4)
        assert are_close(delta_t, 0.5, 1e-1)

    t.play(r(), quant=1)
    t.wait()


def test_wait():
    t = TempoClock()
    t.set_tempo(100 / 60)

    x = []

    def r():
        for i in range(3):
            yield 1
            x.append(1)

    assert len(x) == 0
    t.play(r())
    t.wait()
    assert len(x) == 3


def test_multiple_routines():
    t = TempoClock()
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

    t.play(r1())
    t.play(r2())
    t.wait()
    assert x == [0, 1, 2, 3, 4, 5]


def test_passing_function_to_play():
    t = TempoClock()
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

    t.play(r1())  # call t.play with a generator
    t.play(r2)  # call t.play with a function
    t.wait()
    assert x == [0, 1, 2, 3, 4, 5]


def test_exceptions():
    t = TempoClock()

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
    t.play(r1())
    t.play(r2())
    t.wait()

    def r3():
        x.append(4)
        yield 0.1
        x.append(5)

    # clock should still be able to run a new routine even after a previous routine raise
    # an exception.
    t.play(r3())
    t.wait()

    assert x == [0, 2, 3, 4, 5]
