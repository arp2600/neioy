import time
import queue
from dataclasses import dataclass, field
from typing import Any
from threading import Thread
import sys

import random


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


class TempoClock:
    def __init__(self, tempo):
        # TODO Make tempo adjustable from the main thread.
        # The issue is at the moment, elapsedBeats = time.time() * tempo
        # This means that for a given value of time.time(), changing the tempo changes elapsedBeats.
        # This messes with the scheduling. Changing tempo should not affect elapsedBeats.
        self._tempo = tempo
        self.routines = queue.PriorityQueue()

        self.runAsync()

    def play(self, routine):
        when = self.elapsedBeats() + 1
        self.routines.put(PrioritizedItem(when, routine))

    def _sleep_until(self, until):
        while self.elapsedBeats() < until and not self._stop_thread:
            pass

    def run(self):
        self._run()

    def runAsync(self):
        self._play_thread = Thread(target=lambda: self.run(), daemon=True)
        self._play_thread.start()

    def elapsedBeats(self):
        return time.time() * self._tempo

    def beats(self):
        return self._beats

    def beats2seconds(self, beats):
        return beats / self._tempo

    def _run(self):
        self._stop_thread = False
        self._beats = self.elapsedBeats()

        while True:
            if self._stop_thread:
                print("Stopping clock...")
                return

            if self.routines.empty():
                self._sleep_until(self._beats + 1)
                self._beats += 1
                continue

            x = self.routines.get()

            sys.stdout.flush()
            self._sleep_until(x.priority)
            if self._stop_thread:
                print("Stopping clock...")
                return

            physical_time = self.elapsedBeats()
            if x.priority == 0:
                logical_time = physical_time
            else:
                logical_time = x.priority

            try:
                yielded_time = next(x.item)
                schedule_time = yielded_time + logical_time
                self._beats += yielded_time
                self.routines.put(PrioritizedItem(schedule_time, x.item))
            except StopIteration:
                pass

    def stop(self):
        self._stop_thread = True
        self._play_thread.join()
