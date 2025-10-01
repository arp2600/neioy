#!/usr/bin/env python3
import traceback
import threading
import tkinter as tk
import queue
import time
from icecream import ic
from functools import partial
from neioy.interpreter import Interpreter
from neioy.clocks import NonBlockingTempoClock


class FuncQueue:

    def __init__(self):
        self._func_queue = queue.Queue()

    def exec(self):
        name, func = self._func_queue.get()
        try:
            func()
        except Exception as e:
            print(f"Exception encountered when running gui_func '{name}'")
            traceback.print_exception(e)

    def empty(self):
        return self._func_queue.empty()

    def put(self, name, func, *args, **kwargs):
        self._func_queue.put((name, lambda: func(*args, **kwargs)))


def rt_thread_func(_locals, exit_main):
    rt_func_handler = FuncQueue()

    # Decorator to mark a function to be run on the realtime thread,
    # regardless of the thread it's called from.
    def rt_func(func):
        return partial(rt_func_handler.put, func.__name__, func)

    def _exit(v=0):
        """Override of `exit` for the interpreter."""
        exit_main(v)  # Call exit on the gui thread.
        raise SystemExit(v)  # Raise SystemExit to exit the interpreter.

    clock = NonBlockingTempoClock()

    # copy _locals before writing to it
    _locals = {i: v for i, v in _locals.items()}
    _locals['clock'] = clock
    _locals['rt_func'] = rt_func
    _locals['exit'] = _exit

    x = Interpreter(locals=_locals)
    while True:
        x.update()
        clock.update()
        while not rt_func_handler.empty():
            rt_func_handler.exec()


def main():
    root = tk.Tk()

    gui_func_handler = FuncQueue()

    # Decorator to mark a function to be run on the gui thread,
    # regardless of the thread it's called from.
    def gui_func(func):
        return partial(gui_func_handler.put, func.__name__, func)

    start_gui_flag = False

    @gui_func
    def start_gui():
        nonlocal start_gui_flag
        start_gui_flag = True

    @gui_func
    def _exit_gui(v=0):
        """Call `exit` on the gui thread."""
        time.sleep(0.1)
        exit(v)

    _locals = {'start_gui': start_gui, 'gui_func': gui_func, 'root': root}
    rt_thread = threading.Thread(target=rt_thread_func,
                                 kwargs={
                                     '_locals': _locals,
                                     'exit_main': _exit_gui
                                 })
    rt_thread.start()

    while not start_gui_flag:
        gui_func_handler.exec()

    def run_gui_funcs():
        while not gui_func_handler.empty():
            gui_func_handler.exec()
        root.after(1000 // 60, run_gui_funcs)

    run_gui_funcs()
    root.mainloop()

    rt_thread.join()


if __name__ == '__main__':
    main()
