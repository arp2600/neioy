import queue
from icecream import ic
from dataclasses import dataclass, field
from typing import Any
import time


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


def r1():
    for item in "ABCD":
        print(item)
        yield 3


def r2():
    yield 1
    for item in "abcd":
        print(item)
        yield 1
        print(item)
        yield 2


now = time.time()

q = queue.PriorityQueue()
q.put(PrioritizedItem(0, r1()))
q.put(PrioritizedItem(0, r2()))

while not q.empty():
    x = q.get()
    # need to wait until execution time
    delta_t = x.priority - now
    if delta_t > 0:
        time.sleep(delta_t)
        now = time.time()

    try:
        wait_time = next(x.item)
        q.put(PrioritizedItem(now + wait_time, x.item))
    except StopIteration:
        pass
