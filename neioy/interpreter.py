import sys
import os
import tty
import termios
import time
import subprocess
import io
from tempfile import NamedTemporaryFile
from codeop import CommandCompiler
from itertools import islice
from dataclasses import dataclass
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

    def iter_lines(self):

        def lines_iter():
            start = 0
            end = self._end_of_line_index(start)
            yield ''.join(self._text[start:end + 1])
            while end != len(self._text):
                start = end + 1
                end = self._end_of_line_index(start)
                yield ''.join(self._text[start:end + 1])

        return lines_iter()

    def get_line(self, row=None):
        start = 0
        end = self._end_of_line_index(start)
        for _ in range(row):
            start = end + 1
            end = self._end_of_line_index(start)
        return ''.join(self._text[start:end + 1])

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
            return self._text.pop(self._cursor)
        except IndexError:
            pass

    def __str__(self):
        return ''.join(self._text)


class EscapeCodes:

    @staticmethod
    def enable_bracketed_paste():
        return "\x1b[?2004h"

    @staticmethod
    def _move_cursor(direction_code, amount):
        if amount <= 0:
            raise Exception()

        if amount == 1:
            return f'\x1b[{direction_code}'
        else:
            return f'\x1b[{amount}{direction_code}'

    @staticmethod
    def move_cursor_left(amount=1):
        return EscapeCodes._move_cursor('D', amount)

    @staticmethod
    def move_cursor_right(amount=1):
        return EscapeCodes._move_cursor('C', amount)

    @staticmethod
    def move_cursor_up(amount=1):
        return EscapeCodes._move_cursor('A', amount)

    @staticmethod
    def move_cursor_down(amount=1):
        return EscapeCodes._move_cursor('B', amount)

    @staticmethod
    def erase_from_cursor_to_end_of_line():
        return '\x1b[0K'

    @staticmethod
    def erase_line():
        return '\x1b[2K'

    @staticmethod
    def move_to_column(column):
        assert column >= 0
        return f'\x1b[{column}G'

    @staticmethod
    def move_cursor_to(row, column):
        return f'\x1b[{row};{column}H'

    @staticmethod
    def request_cursor_position():
        return '\x1b[6n'


class Term:

    def __init__(self, istream, ostream):
        self._istream = istream
        self._ostream = ostream
        self._init_screen_dimensions()
        # self._lines = [[' ' for _ in range(self.screen_width)] for _ in range(self.screen_height)]

    def _init_screen_dimensions(self):
        # save the current position
        self._update_cursor_position()
        saved_position = (self.row, self.column)

        # Move the cursor far left and down, it will only
        # move as far as the screen dimensions allow.
        self.move_cursor_to(9999, 9999)

        self._update_cursor_position()
        self.screen_height = self.row
        self.screen_width = self.column

        # restore the cursor position
        self.move_cursor_to(*saved_position)

    def _update_cursor_position(self):
        self._ostream.write(EscapeCodes.request_cursor_position())
        self._ostream.flush()
        assert self._istream.read(2) == '\x1b['
        row = ''
        while True:
            char = self._istream.read(1)
            if '0' <= char <= '9':
                row += char
            elif char == ';':
                break
            else:
                raise Exception()
        column = ''
        while True:
            char = self._istream.read(1)
            if '0' <= char <= '9':
                column += char
            elif char == 'R':
                break
            else:
                raise Exception()
        self.row = int(row)
        self.column = int(column)

    def write(self, chars):
        for char in chars:
            # self._lines[self.row][self.column] = char
            if char == '\n':
                self.column = 0
                self.row += 1
            else:
                self.column += 1

        self._ostream.write(chars)

    def flush(self):
        self._ostream.flush()

    def move_cursor_left(self, amount=1):
        assert amount > 0
        assert amount <= self.column
        self._ostream.write(EscapeCodes.move_cursor_left(amount))
        self.column -= amount

    def move_cursor_right(self, amount=1):
        assert amount > 0
        self._ostream.write(
            EscapeCodes.move_cursor_right(amount, self._ostream))
        self.column += amount

    def move_cursor_up(self, amount=1):
        assert amount > 0
        assert amount <= self.row
        self._ostream.write(EscapeCodes.move_cursor_up(amount, self._ostream))
        self.row -= amount

    def move_cursor_down(self, amount=1):
        assert amount > 0
        self._ostream.write(EscapeCodes.move_cursor_down(
            amount, self._ostream))
        self.row += amount

    def move_to_column(self, column):
        assert column >= 0
        self._ostream.write(EscapeCodes.move_to_column(column))

    def erase_line(self):
        self._ostream.write(EscapeCodes.erase_line())

    def move_cursor_to(self, row=None, column=None):
        if row is not None:
            self.row = row
        if column is not None:
            self.column = column
        self._ostream.write(EscapeCodes.move_cursor_to(self.row, self.column))

    # def __str__(self):
    #     return ''.join([''.join(line) for line in self._lines])


@dataclass
class RowColumn:
    row: int = 0
    column: int = 0


class EditField:

    def __init__(self,
                 ps1='>>> ',
                 ps2='... ',
                 istream=sys.stdin,
                 ostream=sys.stdout):
        self.ps1 = ps1
        self.ps2 = ps2
        self._prompts = [ps1]
        self._text = TextEditor()
        self._term = Term(istream, ostream)
        self._term_offset = RowColumn(row=self._term.row,
                                      column=self._term.column)

        self._term.write(self.ps1)
        self._term.flush()

    def move_cursor_left(self, amount=1):
        assert amount > 0
        self._text.move_left(amount)
        self._reset_cursor_position()
        self._redraw()

    def move_cursor_right(self, amount=1):
        assert amount > 0
        self._text.move_right(amount)
        self._reset_cursor_position()
        self._redraw()

    def move_cursor_up(self, amount=1):
        assert amount > 0
        self._text.move_up(amount)
        self._reset_cursor_position()
        self._redraw()

    def move_cursor_down(self, amount=1):
        assert amount > 0
        self._text.move_down(amount)
        self._reset_cursor_position()
        self._redraw()

    def _reset_cursor_position(self):
        row, column = self._text.get_row_and_column()
        column += len(self._prompts[row])
        self._term.move_cursor_to(row + self._term_offset.row,
                                  column + self._term_offset.column)

    def _redraw_line(self, row=None):
        if row is None:
            self._term.move_cursor_to(None, self._term_offset.column)
        else:
            self._term.move_cursor_to(row + self._term_offset.row,
                                      self._term_offset.column)

        self._term.erase_line()

        if row is None:
            row, _ = self._text.get_row_and_column()

        prompt = self._prompts[row]
        self._term.write(prompt)

        line = self._text.get_line(row)
        if line.endswith('\n'):
            line = line[:-1]

        self._term.write(line)
        self._reset_cursor_position()
        self._term.flush()

    def _clear(self):
        for i in range(len(self._prompts)):
            term_line = self._term_offset.row + i
            if term_line > self._term.screen_height:
                break
            else:
                self._term.move_cursor_to(term_line, 1)
                self._term.erase_line()
        self._reset_cursor_position()

    def _redraw(self):
        # expand the edit field `window` if there are more lines to print than the number of rows allows
        if self._term_offset.row > 1:
            num_lines = len(self._prompts)
            term_lines = self._term.screen_height - (self._term_offset.row - 1)
            if term_lines < num_lines:
                self._term_offset.row -= 1

        # adjust the row offset so that the cursor always remains in the visible area
        row, column = self._text.get_row_and_column()
        if self._term_offset.row + row > self._term.screen_height:
            self._term_offset.row = self._term.screen_height - row
        elif self._term_offset.row + row < 1:
            self._term_offset.row = 1 - row

        # draw all the lines
        for i, (prompt,
                line) in enumerate(zip(self._prompts,
                                       self._text.iter_lines())):
            term_line = self._term_offset.row + i
            # skip lines that would draw off the top of the screen
            if term_line < 1:
                continue
            # break when lines would start to be drawn below the screen
            if term_line > self._term.screen_height:
                break

            self._term.move_cursor_to(term_line, self._term_offset.column)
            self._term.erase_line()
            self._term.write(prompt)
            if line.endswith('\n'):
                line = line[:-1]
            self._term.write(line)
        self._reset_cursor_position()

    def insert(self, char):
        assert 0x20 <= ord(char) <= 0x7e
        self._text.insert(char)
        # self._redraw_line()
        self._redraw()

    def backspace(self):
        self._text.move_left(1)
        char = self._text.pop()
        if char == '\n':
            self._clear()
            row, _ = self._text.get_row_and_column()
            self._prompts.pop(row + 1)

        # self._redraw_line()
        self._redraw()

    def newline(self):
        self._text.insert('\n')
        row, _ = self._text.get_row_and_column()

        # insert a new prompt for the newline
        self._prompts.insert(row, self.ps2)

        # write out enough newlines to display the rest of the lines
        # TODO this breaks given enough lines.
        # When trying to move_up past the top of the window, nothing happens and _redraw_line draws over the last line.
        # When trying to move_down past the bottom the same thing happens. We knew that already but didn't factor in actually moving down, not adding newlines.
        # self._term.write('\n' * (len(self._prompts) - row))
        # self._term.flush()
        # # Starting from the line the newline was added to, redraw every line going down.
        # for i in range(row - 1, len(self._prompts)):
        #     self._redraw_line(i)
        # self._reset_cursor_position()
        self._redraw()

    def __str__(self):
        return str(self._text)


class Interpreter:

    def __init__(self, locals=None):

        self._setup_tty()

        # Enable bracketed paste
        sys.stdout.write(EscapeCodes.enable_bracketed_paste())
        sys.stdout.flush()
        self._bracketed_paste = False

        if locals is None:
            locals = {}
        if 'exit' not in locals:
            # Override exit so we can do any shut down we need to after the interpreter has closed.
            def raise_system_exit(x=1):
                raise SystemExit(x)

            locals['exit'] = raise_system_exit
        self._locals = locals

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
        self._editor = EditField()

    def _handle_csi(self):
        sequence = ''
        while True:
            char = yield from self._get_char()
            sequence += char
            if 0x40 <= ord(char) <= 0x7E:
                break

        if sequence == '200~':
            self._bracketed_paste = True
        elif sequence == '201~':
            self._bracketed_paste = False
        elif sequence == 'A':
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

    def _handle_newline(self):
        if self._bracketed_paste:
            self._editor.newline()
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
                self._editor.backspace()
            elif char == '\t':
                for _ in range(4):
                    self._editor.insert(' ')
            elif char == '\n':
                self._handle_newline()
            else:
                self._editor.insert(char)

    def _reset_term(self):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH,
                          self._tty_attrs)

    def _try_run_source(self):
        source = str(self._editor)
        lines = source.splitlines()

        if len(lines) > 1 and not source.endswith('\n'):
            self._editor.newline()
            return

        post(f'{source.encode("utf-8")}')

        try:
            symbol = 'single'
            if source.find('\n') != len(source) - 1:
                symbol = 'exec'

            code = self._compile(source, symbol=symbol)
            if code is None:
                self._editor.newline()
                return
        except (OverflowError, SyntaxError, ValueError):
            sys.stdout.write(f'\nsyntax error\n')
            sys.stdout.write(source)
            sys.stdout.write('\n\n')
            self._reset_input_buffer()
            return

        sys.stdout.write('\n')
        try:
            exec(code, self._locals)
        except SystemExit as e:
            self._reset_term()
            raise e

        self._reset_input_buffer()

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
