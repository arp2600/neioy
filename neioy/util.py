def midicps(note):
    return 2 ** ((note - 69) / 12) * 440


def amp_comp(root, freq, exp=0.333):
    return (root / freq) ** exp


# Used for keeping track of the beat when adding randomness
# to the time between beats.
# The below example will print the current beat every beat,
# but be delayed by a random time up to 0.1 beats:
#
#   def basic():
#     beat_tracker = BeatTracker(tempo_clock)
#     while True:
#       print(tempo_clock.beats())
#       yield (beat_tracker + 1) + random.random() * 0.1
#
class BeatTracker:
    def __init__(self, clock):
        self._clock = clock
        self._beat = clock.beats()

    # Adds `beats` to the current logical beat and returns
    # the required yield time.
    def __add__(self, beats):
        self._beat += beats
        return self._beat - self._clock.beats()
