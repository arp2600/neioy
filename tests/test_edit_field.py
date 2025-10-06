from neioy.interpreter import EditField
from icecream import ic
import sys
import re
import time


class VirtualTerminal:

    def __init__(self):
        self._lines = [[]]
        self.row = 0
        self.column = 0
        self._raw_input = []
        print()

    def raw_input(self):
        return ''.join(self._raw_input)

    def write(self, chars):
        self._raw_input.append(chars)
        sys.stdout.write(chars)
        chars = list(chars)
        while chars:
            char = chars.pop(0)
            if char == '\x1b':
                self._handle_escape(chars)
            elif char == '\n':
                self.row += 1
                while len(self._lines) <= self.row:
                    self._lines.append([])
                self.column = 0
            else:
                line = self._lines[self.row]
                # pad line with spaces if not long enough
                while len(line) <= self.column:
                    line.append(' ')
                line[self.column] = char
                self.column += 1

    def _handle_escape(self, chars):
        if chars and chars[0] == '[':
            chars.pop(0)
            if m := re.match(r'(\d*)([ABCD])', ''.join(chars)):
                count = m.group(1)
                direction_code = m.group(2)
                for i in range(len(m.group(0))):
                    chars.pop(0)
                if direction_code == 'D':
                    if count:
                        self.column = max(0, self.column - int(count))
                    else:
                        self.column = max(0, self.column - 1)
                elif direction_code == 'B':
                    if count:
                        self.row += int(count)
                    else:
                        self.row += 1
                    while len(self._lines) <= self.row:
                        self._lines.append([])
                else:
                    raise Exception(''.join(chars).encode('utf-8'))
        else:
            raise Exception(''.join(chars).encode('utf-8'))

    def flush(self):
        sys.stdout.flush()

    def get_string(self):
        line_strings = [''.join(line) for line in self._lines]
        return '\n'.join(line_strings)


def test_hello_world():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'hello world':
        edit_field.insert(char)

    print()
    assert vterm.get_string() == '>>> hello world'
    assert vterm.column == 15
    assert str(edit_field) == 'hello world'


def test_hello_world_out_of_order():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'world':
        edit_field.insert(char)
    assert vterm.column == 9

    edit_field.move_cursor_left(5)
    assert vterm.column == 4

    for char in 'hello ':
        edit_field.insert(char)
    assert vterm.column == 10

    print()
    assert vterm.get_string() == '>>> hello world'
    assert str(edit_field) == 'hello world'


def test_backspace():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'hello foo':
        edit_field.insert(char)
    assert vterm.column == 13

    for i in range(3):
        edit_field.backspace()
    assert vterm.column == 10

    for char in 'world':
        edit_field.insert(char)
    assert vterm.column == 15

    print()
    assert vterm.get_string() == '>>> hello world'
    assert str(edit_field) == 'hello world'


def test_newline():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'hello':
        edit_field.insert(char)
    assert vterm.column == 9

    edit_field.newline()
    assert vterm.column == 4
    assert vterm.row == 1

    for char in 'world':
        edit_field.insert(char)
    assert vterm.column == 9

    print()
    assert vterm.get_string() == '>>> hello\n... world'
    assert (str(edit_field)) == 'hello\nworld'


# def test_control_chars():
#     print()
#     # for v in ['hello', '\x1b[D', '\n', '\x1b[A', '\x1b[B']:
#     for v in ['hello', '\x1b[3D', '\n', 'wor', '\x1b[A', '\x1b[B']:
#         sys.stdout.write(v)
#         sys.stdout.flush()
#         time.sleep(1)
