import time
import queue
from dataclasses import dataclass, field
from typing import Any
from threading import Thread
import threading
import math


@dataclass(order=True)
class ScheduledEvent:
    scheduled_time: int
    event: Any = field(compare=False)


class TempoClock:
    def __init__(self):
        self._tempo = 120 / 60
        self._ref_time = time.time()
        self._ref_beats = 0
        self._beats = 0

        self._routines = queue.PriorityQueue()
        # flag for when all routines have been processed.
        # we can't use `self._routines.empty()` because even
        # if `self._routines` is empty, there might still be
        # the last event to process.
        self._finished_routines = threading.Event()

        t = Thread(target=lambda: self._run(), daemon=True)
        t.start()

    def set_tempo(self, tempo):
        self._ref_beats = self.elapsed_beats()
        self._ref_time = time.time()
        self._tempo = tempo

    def elapsed_beats(self):
        return (time.time() - self._ref_time) * self._tempo + self._ref_beats

    def beats(self):
        return self._beats

    def beats2seconds(self, beats):
        return ((beats - self._ref_beats) / self._tempo) + self._ref_time

    def time(self):
        return self.beats2seconds(self.beats())

    def _get_next_event(self):
        if not self._routines.empty():
            return self._routines.get()
        else:
            None

    def _add_event(self, beats, event):
        self._routines.put(ScheduledEvent(beats, event))

    def _run(self):
        print("TempoClock._run")
        next_event = None

        while True:
            if not next_event:
                next_event = self._get_next_event()

            if next_event and self.elapsed_beats() > next_event.scheduled_time:
                self._beats = next_event.scheduled_time
                try:
                    yielded_time = next(next_event.event)
                    self._add_event(self._beats + yielded_time, next_event.event)
                except StopIteration:
                    if self._routines.empty():
                        self._finished_routines.set()
                    pass
                next_event = None
            else:
                self._beats = self.elapsed_beats()

    def play(self, routine, quant=None):
        when = self.elapsed_beats()
        if quant:
            when = math.ceil(when / quant) * quant
        self._add_event(when, routine)
        self._finished_routines.clear()

    def sched_abs(self, routine, when):
        self._add_event(when, routine)
        self._finished_routines.clear()

    def wait(self):
        self._finished_routines.wait()
