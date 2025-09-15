from neioy.routine import routine
from neioy.clocks import TempoClock
import pytest


@pytest.fixture
def clock():
    clock = TempoClock()
    yield clock
    clock.stop()


def test_args(clock):
    x = []
    y = []

    @routine
    def test_routine(arg, output):
        for i in arg:
            output.append(i)
            yield 0.1

    test_routine('hello world', x).play(clock)
    test_routine('fubar', y).play(clock)
    clock.wait()
    assert x == [i for i in 'hello world']
    assert y == [i for i in 'fubar']


def test_wait(clock):
    x = []
    y = []

    @routine
    def test_routine(arg, output):
        # Loop over all but the last element.
        for i in arg[:-1]:
            output.append(i)
            yield 0.1
        # Output the last element but don't yield after it.
        # Without this, there is a yield after outputting 'fubar' and
        # the ' 'in 'hello world' gets added to x before the asserts.
        output.append(arg[-1])

    r_hello = test_routine('hello world', x).play(clock, quant=1)
    r_fubar = test_routine('fubar', y).play(clock, quant=1)

    # wait on r_fubar to finish
    r_fubar.wait()
    assert x == [i for i in 'hello'] # r_hello shouldn't have finished yet
    assert y == [i for i in 'fubar']

    clock.wait()
    assert x == [i for i in 'hello world']


def test_pause(clock):
    x = []

    @routine
    def test_routine():
        for i in range(10):
            x.append(i)
            yield 0.1

    r0 = test_routine().play(clock)

    while len(x) < 6:
        pass
    assert x == [0, 1, 2, 3, 4, 5]

    # sleep for a beat and confirm no values added to x
    r0.pause()
    clock.sleep(1.0)
    assert x == [0, 1, 2, 3, 4, 5]

    # resume r0 and wait for it before confirming x
    r0.play(clock)
    r0.wait()
    assert x == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

