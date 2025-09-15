import supriya
import time
import queue
from dataclasses import dataclass, field
from typing import Any
from threading import Thread
import threading
import math
import sys
import traceback
from contextlib import contextmanager


@dataclass(order=True)
class _ScheduledEvent:
    scheduled_time: int
    event: Any = field(compare=False)


@contextmanager
def _dummy_context(clock):
    yield None


def _create_server_context(server):

    @contextmanager
    def _server_context(clock):
        with server.at(seconds=clock.time() + 0.1):
            yield None

    return _server_context


class TempoClock:

    def __init__(self, tempo=2.0, context=_dummy_context):
        self._tempo = tempo
        self._ref_time = time.time()
        self._ref_beats = 0
        self._beats = 0

        self._dont_yield = False
        self._dont_yield_reason = None

        self._routines = queue.PriorityQueue()
        # flag for when all routines have been processed.
        # we can't use `self._routines.empty()` because even
        # if `self._routines` is empty, there might still be
        # the last event to process.
        self._finished_routines = threading.Event()

        self.set_context(context)

        self._stop_thread = threading.Event()
        self._thread = Thread(target=lambda: self._run(), daemon=True)
        self._thread.start()

    def set_context(self, context):
        if isinstance(context, supriya.Server):
            self.context = _create_server_context(context)
        else:
            self.context = context

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

    def sleep(self, duration):
        now = self.beats()
        while self.beats() - now < duration:
            pass

    def _get_next_event(self):
        if not self._routines.empty():
            return self._routines.get()
        else:
            None

    def _add_event(self, beats, event):
        self._routines.put(_ScheduledEvent(beats, event))
        self._finished_routines.clear()

    def _process_event(self, event):
        try:
            yielded_time = next(event.event)
        except StopIteration:
            pass
        except Exception as e:
            # Print the exception that happened in the routine but we don't want
            # the clock to stop running.
            traceback.print_exception(e)
        else:
            if self._dont_yield:
                raise Exception(self._dont_yield_reason)
            self._add_event(self._beats + yielded_time, event.event)

    def _run(self):
        next_event = None

        while not self._stop_thread.is_set():
            if not next_event:
                next_event = self._get_next_event()

            # collect events which should be processed
            to_process = []
            if next_event and self.elapsed_beats() > next_event.scheduled_time:
                when = next_event.scheduled_time
                to_process.append(next_event)
                next_event = self._get_next_event()

                # because the context could be making a timestamped bundle, we don't just
                # want to collect all the event where
                # `self.elapsed_beats() > next_event.scheduled_time`, we want to collect
                # all the event with EXACTLY the same scheduled_time as the first event.
                while next_event and next_event.scheduled_time == when:
                    to_process.append(next_event)
                    next_event = self._get_next_event()

            if to_process:
                # process the collected events
                with self.context(self):
                    for event in to_process:
                        self._beats = event.scheduled_time
                        self._process_event(event)

                if next_event is None and self._routines.empty():
                    self._finished_routines.set()
            else:
                # advance self._beats
                self._beats = self.elapsed_beats()

    # There are situations where yielding can cause
    # confusing and difficult to debug behaviour, such as
    # from withing a `server.bind` context.
    @contextmanager
    def block_yield(self, reason):
        self._dont_yield = True
        self._dont_yield_reason = reason
        yield None
        self._dont_yield = False
        self._dont_yield_reason = None

    def play(self, routine, quant=None):
        if callable(routine):
            routine = routine()

        when = self.beats()
        if quant:
            when = math.ceil(when / quant) * quant
        self._add_event(when, routine)

    def sched_abs(self, routine, when):
        self._add_event(when, routine)

    def sched(self, routine, delta):
        self.sched_abs(routine, self.beats() + delta)

    def wait(self):
        self._finished_routines.wait()

    def stop(self):
        self._stop_thread.set()
        self._thread.join()
