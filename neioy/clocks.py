import time
import queue
from dataclasses import dataclass, field
from typing import Any
from threading import Thread


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


class TempoClock:
    def __init__(self):
        self.tempo = 120 / 60
        self.routines = queue.PriorityQueue()

        self.runAsync()

    def play(self, routine):
        self.routines.put(PrioritizedItem(0, routine))

    def _sleep_until(self, until):
        while time.time() * self.tempo < until and not self._stop_thread:
            pass

    def run(self):
        self._run()

    def runAsync(self):
        self._play_thread = Thread(target=lambda: self.run(), daemon=True)
        self._play_thread.start()

    def elapsedBeats(self):
        return (time.time() - self._start_time) * self.tempo

    def beats(self):
        return self._beats

    def _run(self):
        self._start_time = time.time()
        self._stop_thread = False
        self._beats = 0

        while True:
            if self._stop_thread:
                print("Stopping clock...")
                return

            if self.routines.empty():
                continue

            x = self.routines.get()

            self._sleep_until(x.priority)
            if self._stop_thread:
                print("Stopping clock...")
                return

            physical_time = time.time() * self.tempo
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
        print("TempoClock.stop")
        self._stop_thread = True
        self._play_thread.join()
