import sys
import os
import tty
import termios
import time
import subprocess
import io
from tempfile import NamedTemporaryFile
from codeop import CommandCompiler
from icecream import ic
try:
    from post_window import post
except ModuleNotFoundError:

    def post(*args, **kwargs):
        pass


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

    def get_line(self):
        start = self._start_of_line_index(self._cursor - 1)
        end = self._end_of_line_index(self._cursor)
        return ''.join(self._text[start:end])

    def insert(self, char):
        self._text.insert(self._cursor, char)
        self._cursor += 1

    def _rindex(self, value, start=None, stop=-1):
        if start is None:
            start = len(self._text) - 1

        for i in range(start, stop, -1):
            ic(i)
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

    def get_column(self):
        return self.get_row_and_column()[1]

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
    def enable_bracketed_paste(ostream=sys.stdout):
        ostream.write("\x1b[?2004h")
        ostream.flush()

    @staticmethod
    def _move_cursor(direction_code, amount, ostream):
        if amount == 1:
            ostream.write(f'\x1b[{direction_code}')
        else:
            ostream.write(f'\x1b[{amount}{direction_code}')

    @staticmethod
    def move_cursor_left(amount=1, ostream=sys.stdout):
        Terminal._move_cursor('D', amount, ostream)

    @staticmethod
    def move_cursor_right(amount=1, ostream=sys.stdout):
        Terminal._move_cursor('C', amount, ostream)

    @staticmethod
    def move_cursor_up(amount=1, ostream=sys.stdout):
        Terminal._move_cursor('A', amount, ostream)

    @staticmethod
    def move_cursor_down(amount=1, ostream=sys.stdout):
        Terminal._move_cursor('B', amount, ostream)

    @staticmethod
    def erase_from_cursor_to_end_of_line(ostream=sys.stdout):
        ostream.write('\x1b[0K')


class EditField:

    def __init__(self, ps1='>>> ', ps2='... ', ostream=sys.stdout):
        self.ps1 = ps1
        self.ps2 = ps2
        self._prompts = [ps1]
        self._text = TextEditor()
        self._ostream = ostream

        self._row = 0
        self._column = 0

        self._write_prompt(self.ps1)
        self._flush()

    def _write_prompt(self, prompt):
        self._prompts.append(prompt)
        self._column += len(prompt)
        self._ostream.write(prompt)

    def _flush(self):
        self._ostream.flush()

    def _move_cursor_left(self, amount):
        Terminal.move_cursor_left(amount, self._ostream)
        self._column -= amount

    def _redraw_line(self):
        save_column = self._column
        self._move_cursor_left(self._column)

        prompt = self._prompts[self._row]
        self._write_prompt(prompt)

        line = self._text.get_line()
        self._ostream.write(line)
        self._column + len(line)

        self._move_cursor_left(self._column - save_column)

        self._ostream.flush()

    def insert(self, char):
        self._text.insert(char)
        self._column += 1
        self._redraw_line()


def _get_test_lines(lines):
    for i, line in enumerate(lines):
        if line == 'START OF TEST\n':
            start = i + 1
            break
    else:
        raise Exception("Couldn't find the start of the test")

    for i, line in enumerate(lines[start:]):
        if line == 'END OF TEST\n':
            end = i + start
            break
    else:
        raise Exception("Couldn't find the end of the test")

    return lines[start:end]


def _get_test_output(test_func):
    with NamedTemporaryFile(mode='wt', delete_on_close=False) as f:
        edit_field = EditField(ostream=f)
        test_func(edit_field)
        f.write('\n')
        f.close()
        subprocess.run(['tmux', '-c', f'./tmux_process.sh {f.name}'],
                       check=True)

        with open(f.name, 'rt') as f:
            return ''.join(_get_test_lines(f.readlines()))


def test_hello_world():
    def test_func(edit_field):
        for char in 'hello world':
            edit_field.insert(char)

    result = _get_test_output(test_func)
    print(result)
    assert result == '>>> hello world\n'


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
        self._locals = locals

        self._prompt(self.ps1)

        self._chars = ''
        self._reset_input_buffer()

        self._compile = CommandCompiler()

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

    def _handle_newline(self):
        if self._bracketed_paste:
            self._prompt(self.ps2)
        else:
            self._try_run_source()

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
            elif char == '\n':
                self._handle_newline()
            else:
                self._handle_character(char)

    def _prompt(self, prompt_str):
        sys.stdout.write(prompt_str)
        sys.stdout.flush()

    def _reset_term(self):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH,
                          self._tty_attrs)

    def _try_run_source(self):
        source = str(self._input)
        lines = source.splitlines()

        if len(lines) > 1 and not source.endswith('\n'):
            self._input.insert('\n')
            sys.stdout.write('\n')
            self._prompt(self.ps2)
            return

        post(f'{source.encode("utf-8")}')

        try:
            symbol = 'single'
            if source.find('\n') != len(source) - 1:
                symbol = 'exec'

            code = self._compile(source, symbol=symbol)
            if code is None:
                self._input.insert('\n')
                sys.stdout.write('\n')
                self._prompt(self.ps2)
                return
        except (OverflowError, SyntaxError, ValueError):
            sys.stdout.write(f'\nsyntax error\n')
            self._reset_input_buffer()
            self._prompt(self.ps1)
            return

        sys.stdout.write('\n')
        try:
            exec(code, self._locals)
        except SystemExit as e:
            self._reset_term()
            raise e

        self._reset_input_buffer()
        self._prompt(self.ps1)

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
