from neioy.interpreter import EditField
from icecream import ic
import sys
import re


class TestTerm:

    def __init__(self):
        self._lines = [[]]
        self._line = 0
        self._column = 0
        print()

    def write(self, chars):
        sys.stdout.write(chars)
        chars = list(chars)
        while chars:
            char = chars.pop(0)
            if char == '\x1b':
                self._handle_escape(chars)
            else:
                line = self._lines[self._line]
                # pad line with spaces if not long enough
                while len(line) <= self._column:
                    line.append(' ')
                line[self._column] = char
                self._column += 1

    def _handle_escape(self, chars):
        if chars and chars[0] == '[':
            chars.pop(0)
            if m := re.match('(\d*)([ABCD])', ''.join(chars)):
                count = m.group(1)
                direction_code = m.group(2)
                for i in range(len(m.group(0))):
                    chars.pop(0)
                if direction_code == 'D':
                    self._column = max(0, self._column - int(count))
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
    test_term = TestTerm()
    edit_field = EditField(ostream=test_term)
    for char in 'hello world':
        edit_field.insert(char)

    print()
    assert test_term.get_string() == '>>> hello world'


def test_hello_world_out_of_order():
    test_term = TestTerm()
    edit_field = EditField(ostream=test_term)
    for char in 'world':
        edit_field.insert(char)
    edit_field.move_cursor_left(5)
    for char in 'hello ':
        edit_field.insert(char)

    print()
    assert test_term.get_string() == '>>> hello world'
