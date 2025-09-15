from icecream import ic

class Routine:

    def __init__(self, gen):
        self._gen = gen
        self._playing = False

    def play(self, clock, *args, **kwargs):
        self._playing = True

        def wrapper():
            for i in self._gen:
                yield i
                if self._playing is False:
                    return

            self._playing = False

        clock.play(wrapper(), *args, **kwargs)

        return self

    def pause(self):
        self._playing = False

    def wait(self):
        while self._playing:
            pass


def routine(func):
    def wrapper(*args, **kwargs):
        return Routine(func(*args, **kwargs))

    return wrapper
