import code
import sys
import os
import tty
import termios


class TextEditor:

    def __init__(self):
        self._text = []
        self._cursor = 0

    def _get_line(self):
        start = self._cursor
        while start > 0 and self._text[start] != '\n':
            start -= 1

        end = self._cursor
        while end < len(self._text) and self._text[end] != '\n':
            end += 1

        line = self._text[start:end]

    def get_line_after_cursor(self):
        end = self._end_of_line_index(self._cursor)
        return ''.join(self._text[self._cursor:end])

    def insert(self, char):
        self._text.insert(self._cursor, char)
        self._cursor += 1

    def _rindex(self, value, start=None, stop=-1):
        if start is None:
            start = len(self._text) - 1

        for i in range(start, stop, -1):
            if self._text[i] == value:
                return i

        raise ValueError(f"'{value}' is not in text")

    def _start_of_line_index(self, index):
        try:
            # `index` could be on the end of a line (i.e. the '\n' character) so we need
            # to start the search from `index - 1`. The result index is the end of the
            # previous line so we add 1 back to get the start of the line.
            return self._rindex('\n', start=index - 1) + 1
        except ValueError:
            return 0

    def _end_of_line_index(self, index):
        try:
            return self._text.index('\n', index)
        except ValueError:
            return len(self._text)

    def _is_eol(self, index):
        return index == len(self._text) or self._text[self._cursor] == '\n'

    def get_row_and_column(self):
        current_line_start = self._start_of_line_index(self._cursor)
        column = self._cursor - current_line_start

        row = 0
        x = current_line_start
        while x > 0:
            row += 1
            x = self._start_of_line_index(x - 1)
        return (row, column)

    def move_up(self, amount):
        if self._cursor == 0:
            return

        current_line_start = self._start_of_line_index(self._cursor)
        if current_line_start == 0:
            return  # Already on the first line.

        if self._is_eol(self._cursor):
            self._cursor = current_line_start - 1
        else:
            previous_line_start = self._start_of_line_index(
                current_line_start - 1)
            column = self._cursor - current_line_start
            if previous_line_start + column >= current_line_start:
                self._cursor = current_line_start - 1
            else:
                self._cursor = previous_line_start + column

    def move_down(self, amount):
        line_end = self._end_of_line_index(self._cursor)
        if line_end == len(self._text):
            return  # Already on the last line.

        if line_end + 1 == len(self._text):
            return  # Already on the last line, but it ends with a newline.

        next_line_start = line_end + 1
        next_line_end = self._end_of_line_index(next_line_start)

        if self._is_eol(self._cursor):
            self._cursor = next_line_end
        else:
            current_line_start = self._start_of_line_index(self._cursor)
            column = self._cursor - current_line_start
            if next_line_start + column < next_line_end:
                self._cursor = next_line_start + column
            else:
                self._cursor = next_line_end

    def move_left(self, amount):
        self._cursor = max(self._cursor - amount, 0)

    def move_right(self, amount):
        self._cursor = min(self._cursor + amount, len(self._text))

    def pop(self):
        try:
            self._text.pop(self._cursor)
        except IndexError:
            pass

    def __str__(self):
        return ''.join(self._text)


class Terminal:

    @staticmethod
    def enable_bracketed_paste():
        sys.stdout.write("\x1b[?2004h")
        sys.stdout.flush()

    @staticmethod
    def _move_cursor(direction_code, amount):
        if amount == 1:
            sys.stdout.write(f'\x1b[{direction_code}')
        else:
            sys.stdout.write(f'\x1b[{amount}{direction_code}')

    @staticmethod
    def move_cursor_left(amount=1):
        Terminal._move_cursor('D', amount)

    @staticmethod
    def move_cursor_right(amount=1):
        Terminal._move_cursor('C', amount)

    @staticmethod
    def move_cursor_up(amount=1):
        Terminal._move_cursor('A', amount)

    @staticmethod
    def move_cursor_down(amount=1):
        Terminal._move_cursor('B', amount)

    @staticmethod
    def erase_from_cursor_to_end_of_line():
        sys.stdout.write('\x1b[0K')


class Interpreter:

    def __init__(self, locals=None):
        self.ps1 = '>>> '
        self.ps2 = '... '

        self._setup_tty()

        # Enable bracketed paste
        Terminal.enable_bracketed_paste()
        self._bracketed_paste = False

        if locals is None:
            locals = {}
        if 'exit' not in locals:
            # Override exit so we can do any shut down we need to after the interpreter has closed.
            def raise_system_exit(x=1):
                raise SystemExit(x)

            locals['exit'] = raise_system_exit

        self._interpreter = code.InteractiveInterpreter(locals=locals)
        self._prompt(self.ps1)

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
        self._input = TextEditor()

    def _handle_csi(self):
        sequence = ''
        while True:
            char = yield from self._get_char()
            sequence += char
            if 0x40 <= ord(char) <= 0x7E:
                break

        row_0, column_0 = self._input.get_row_and_column()

        if sequence == '200~':
            self._bracketed_paste = True
        elif sequence == '201~':
            self._bracketed_paste = False
        elif sequence == 'A':
            self._input.move_up(1)
        elif sequence == 'B':
            self._input.move_down(1)
        elif sequence == 'C':
            self._input.move_right(1)
        elif sequence == 'D':
            self._input.move_left(1)
        else:
            print(sequence.encode('utf-8'))

        row_1, column_1 = self._input.get_row_and_column()
        delta_row = row_1 - row_0
        delta_column = column_1 - column_0
        for _ in range(0, delta_column):
            Terminal.move_cursor_right()
        for _ in range(0, -delta_column):
            Terminal.move_cursor_left()
        for _ in range(0, delta_row):
            Terminal.move_cursor_down()
        for _ in range(0, -delta_row):
            Terminal.move_cursor_up()

    def _handle_escape_sequence(self):
        char = yield from self._get_char()
        if char == '[':
            yield from self._handle_csi()
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
        self._prompt(self.ps1)

    def _handle_backspace(self):
        self._input.move_left(1)
        self._input.pop()

        # step left and erase to the end of the line
        Terminal.move_cursor_left()
        Terminal.erase_from_cursor_to_end_of_line()
        rest = self._input.get_line_after_cursor()
        if rest:
            sys.stdout.write(rest)
            Terminal.move_cursor_left(len(rest))

    def _handle_tab(self):
        for _ in range(4):
            self._input.insert(' ')
            sys.stdout.write(' ')

    def _handle_character(self, char):
        # add a character at the cursor index
        self._input.insert(char)
        sys.stdout.write(char)

        rest = self._input.get_line_after_cursor()
        if rest:
            sys.stdout.write(rest)
            Terminal.move_cursor_left(len(rest))

    def _run(self):
        while True:
            char = yield from self._get_char()

            if char == '\x1b':
                yield from self._handle_escape_sequence()
            elif char == '\x03':  # ctrl-c
                self._handle_ctrl_c()
            elif ord(char) == 0x7f:
                self._handle_backspace()
            elif char == '\t':
                self._handle_tab()
            else:
                self._handle_character(char)

            if char == '\n':
                if self._bracketed_paste:
                    self._prompt(self.ps2)
                else:
                    self._try_run_source()

    def _prompt(self, prompt_str):
        sys.stdout.write(prompt_str)
        sys.stdout.flush()

    def _reset_term(self):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH,
                          self._tty_attrs)

    def _try_run_source(self):
        source = str(self._input)
        lines = source.splitlines()
        if len(lines) > 1 and len(lines[-1]) > 0 and lines[-1][0] in ' \t':
            self._prompt(self.ps2)
            return

        try:
            symbol = 'single'
            if source.find('\n') != len(source) - 1:
                symbol = 'exec'
            if not self._interpreter.runsource(source, symbol=symbol):
                self._reset_input_buffer()
                self._prompt(self.ps1)
            else:
                self._prompt(self.ps2)
        except SystemExit as e:
            self._reset_term()
            raise e

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
