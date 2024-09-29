import time
import queue
from dataclasses import dataclass, field
from typing import Any
from threading import Thread
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
        return 0

    def _get_next_event(self):
        if not self._routines.empty():
            return self._routines.get()
        else:
            None

    def _run(self):
        next_event = None

        while True:
            if not next_event:
                next_event = self._get_next_event()

            if next_event and self.elapsed_beats() > next_event.scheduled_time:
                self._beats = next_event.scheduled_time
                try:
                    yielded_time = next(next_event.event)
                    self._routines.put(
                        ScheduledEvent(self._beats + yielded_time, next_event.event)
                    )
                except StopIteration:
                    pass
                next_event = None
            else:
                self._beats = self.elapsed_beats()

    def play(self, routine, quant=None):
        when = self.elapsed_beats()
        if quant:
            when = math.ceil(when / quant) * quant
        self._routines.put(ScheduledEvent(when, routine))
