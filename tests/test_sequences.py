from icecream import ic
import neioy.sequences as ns
from statistics import mean


def test_func_sequence():
    x = 0

    def test_func():
        nonlocal x
        x += 1
        return x

    seq = ns.func_sequence(test_func, repeats=5)
    assert list(seq) == [1, 2, 3, 4, 5]
    assert list(seq) == [6, 7, 8, 9, 10]
    assert x == 10


def test_sequence():
    seq = ns.sequence([2, 4, 6, 8], repeats=2)
    assert list(seq) == ([2, 4, 6, 8] * 2)
    assert list(seq) == ([2, 4, 6, 8] * 2)


# nest a sequence in a func
def test_nesting():
    x = 0

    def test_func():
        nonlocal x
        x += 1
        if x in [2, 6]:
            return ns.sequence(['a', 'b', 'c'], 1)
        else:
            return x

    seq = ns.func_sequence(test_func, repeats=5)
    assert list(seq) == [1, 'a', 'b', 'c', 3]
    assert list(seq) == [4, 5, 'a', 'b', 'c']
    assert x == 6


# nest a sequence in a sequence in a func
def test_double_nesting():
    x = 0

    def test_func():
        nonlocal x
        x += 1
        if x in [2, 7]:
            return ns.sequence(['a', ns.sequence(['x', 'y'], 2), 'b', 'c'], 1)
        else:
            return x

    seq = ns.func_sequence(test_func, repeats=10)
    assert list(seq) == [1, 'a', 'x', 'y', 'x', 'y', 'b', 'c', 3, 4]
    assert list(seq) == [5, 6, 'a', 'x', 'y', 'x', 'y', 'b', 'c', 8]
    assert x == 8


def test_random_choice():
    choices = [1, 2, 3]
    seq = ns.random_choice(choices, repeats=20)

    x = list(seq)
    assert len(x) == 20

    # Potentially this could fail, but it's unlikely to if repeats is high enough.
    assert set(x) == set(choices)
    ic(x)


def test_white_noise():
    repeats = 100
    lo = 10.0
    hi = 20.0
    seq = ns.white_noise(lo, hi, repeats=repeats)
    x = list(seq)
    ic(mean(x))
    ic(min(x))
    ic(max(x))
    # Check the mean average of the result is about halfway between `lo` and `hi`.
    center = (lo + (hi - lo) / 2)
    assert abs(mean(x) - center) < 1.0
    # The minimum value should be around `lo`.
    assert lo <= min(x) < (lo + 1)
    assert (hi - 1) < max(x) <= hi
