from functools import partial
from collections.abc import Iterable
import random
from icecream import ic


# An iterable sequence of values
class Sequence:

    def __init__(self, iter_func):
        self._iter = iter_func

    def __iter__(self):
        return self._iter()


# An infinite generator
def inf():
    while True:
        yield None


def _get_range(repeats):
    if isinstance(repeats, Iterable):
        return repeats
    else:
        return range(0, repeats)


# Handle nested sequences
def _yield_item(item):
    if isinstance(item, Sequence):
        for i in item:
            yield i
    else:
        yield item


# Call `func` and return the result `repeats` times.
# func_sequence handles nested sequences and will only return `repeats` times.
def func_sequence(func, repeats=1):
    repeats = _get_range(repeats)

    def inner():
        it = iter(repeats)

        # We need to advance the iterator before we call `func`. If we advance the
        # iterator between the call to `func` and yielding the value, we risk calling the
        # func and then getting a StopIteration from the iterator, so we've called the
        # func and not yielded the value.
        # So we need to do: advance, call, yield, advance, call, yield, ...
        # This gets awkward with nested sequences, but if we put the first advance
        # outside the loop then the remaining order is:
        #   call, yield, advance, call, yield, advance, ...
        # That becomes really easy to manager because we can put the advance step at the
        # end of the `for i in _yield_item(item):` loop.
        try:
            next(it)
        except StopIteration:
            return

        while True:
            item = func()
            for i in _yield_item(item):
                yield i
                try:
                    next(it)
                except StopIteration:
                    return

    return Sequence(inner)


def random_choice(collection, repeats=1):
    return func_sequence(partial(random.choice, collection), repeats)


def white_noise(lo=0.0, hi=1.0, repeats=inf()):
    return func_sequence(partial(random.uniform, lo, hi), repeats)


def sequence(items, repeats=1):
    repeats = _get_range(repeats)

    def inner():
        for _ in repeats:
            for item in items:
                yield from _yield_item(item)

    return Sequence(inner)
