import tty
import sys
import termios
import os

from interpreter import EditField


class Interpreter:

    def __init__(self):
        self._setup_tty()

        self._chars = ''
        self._reset_input_buffer()

        self._run_generator = self._run()

    def _setup_tty(self):
        # Set cbreak and save the previous tty attributes to reset the program after exit.
        self._tty_attrs = tty.setcbreak(sys.stdin.fileno())

        # Disabling ISIG allows us to handle ctrl-c.
        tty_attrs = termios.tcgetattr(sys.stdin.fileno())
        tty_attrs[3] &= ~termios.ISIG
        tty_attrs = termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW,
                                      tty_attrs)

    def _reset_input_buffer(self):
        self._editor = EditField()

    def _handle_csi(self):
        sequence = ''
        while True:
            char = yield from self._get_char()
            sequence += char
            if 0x40 <= ord(char) <= 0x7E:
                break

        if sequence == 'A':
            self._editor.move_cursor_up()
        elif sequence == 'B':
            self._editor.move_cursor_down()
        elif sequence == 'C':
            self._editor.move_cursor_right()
        elif sequence == 'D':
            self._editor.move_cursor_left()
        else:
            print(sequence.encode('utf-8'))

    def _handle_escape_sequence(self):
        char = yield from self._get_char()
        if char == '[':
            yield from self._handle_csi()
        elif char == '\x1b':
            print(f'\n{str(self._editor).encode("utf-8")}\n')
        else:
            raise Exception(
                f'unhandled escape sequence {char.encode("utf-8")}')

    def _get_char(self):
        while not self._chars:
            # Read from stdin without blocking
            os.set_blocking(sys.stdin.fileno(), False)
            self._chars = sys.stdin.read(100)
            os.set_blocking(sys.stdin.fileno(), True)

            if self._chars:
                break
            else:
                sys.stdout.flush()
                yield

        x = self._chars[0]
        self._chars = self._chars[1:]
        return x

    def _handle_ctrl_c(self):
        sys.stdout.write('\nKeyboardInterrupt\n')
        self._reset_input_buffer()

    def _run(self):
        while True:
            char = yield from self._get_char()

            if char == '\x1b':
                yield from self._handle_escape_sequence()
            elif char == '\x03':  # ctrl-c
                self._handle_ctrl_c()
            elif ord(char) == 0x7f:
                self._editor.backspace()
            elif char == '\t':
                for _ in range(4):
                    self._editor.insert(' ')
            elif char == '\n':
                if str(self._editor) == 'exit':
                    print('\nExiting...')
                    self._reset_term()
                    exit(0)
                self._editor.newline()
            else:
                self._editor.insert(char)

    def _reset_term(self):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH,
                          self._tty_attrs)

    def update(self):
        next(self._run_generator)


def main():
    import time

    x = Interpreter()
    while True:
        try:
            x.update()
        except SystemExit as e:
            break
        time.sleep(1 / 30)


if __name__ == '__main__':
    main()
