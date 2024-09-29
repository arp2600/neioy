import time
from threading import Thread
from icecream import ic

class TempoClock:
    def __init__(self):
        self._tempo = 120 / 60
        self._ref_time = time.time()
        self._ref_beats = 0

        # t = Thread(target=lambda: self._run(), daemon=True)
        # t.start()

    def setTempo(self, tempo):
        self._ref_beats = self.elapsedBeats()
        self._ref_time = time.time()
        self._tempo = tempo


    def elapsedBeats(self):
        return (time.time() - self._ref_time) * self._tempo + self._ref_beats



tc = TempoClock()
tc.setTempo(60/60)

prev = 0

print('4 beats at 60 bpm')
for i in range(4):
    elapsedBeats = tc.elapsedBeats()
    delta = round(elapsedBeats - prev, 2)
    prev = elapsedBeats
    ic(round(elapsedBeats, 3), delta)
    time.sleep(1)

print('4 beats at 120 bpm')
tc.setTempo(120 / 60)
for i in range(4):
    elapsedBeats = tc.elapsedBeats()
    delta = round(elapsedBeats - prev, 2)
    prev = elapsedBeats
    ic(round(elapsedBeats, 3), delta)
    time.sleep(1)

print('4 beats at 240 bpm')
tc.setTempo(240 / 60)
for i in range(4):
    elapsedBeats = tc.elapsedBeats()
    delta = round(elapsedBeats - prev, 2)
    prev = elapsedBeats
    ic(round(elapsedBeats, 3), delta)
    time.sleep(1)
