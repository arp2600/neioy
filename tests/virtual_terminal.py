import sys
import re
from icecream import ic


class VirtualTerminal:

    def __init__(self, echo=False, height=50, width=150):
        self._height = height
        self._width = width
        self._lines = [[] for _ in range(self._height)]
        # terminals index from (1, 1)
        self.row = 1
        self.column = 1
        self._raw_input = []
        self._echo = echo
        self._istream_buffer = ''

    def raw_input(self):
        return ''.join(self._raw_input)

    def write(self, chars):
        self._raw_input.append(chars)
        if self._echo:
            sys.stdout.write(chars)
        chars = list(chars)
        while chars:
            char = chars.pop(0)
            if char == '\x1b':
                self._handle_escape(chars)
            elif char == '\n':
                self.row += 1
                self.column = 1
            else:
                line = self._lines[self.row - 1]
                # pad line with spaces if not long enough
                while len(line) <= (self.column - 1):
                    line.append(' ')
                line[self.column - 1] = char
                self.column += 1

    def read(self, count):
        assert count > 0
        assert len(self._istream_buffer) >= count

        result = self._istream_buffer[:count]
        self._istream_buffer = self._istream_buffer[count:]
        return result

    def _handle_escape(self, chars):
        if chars and chars[0] == '[':
            chars.pop(0)
            if m := re.match(r'(\d*)([ABCD])', ''.join(chars)):
                count = m.group(1)
                direction_code = m.group(2)
                for i in range(len(m.group(0))):
                    chars.pop(0)
                if direction_code == 'A':
                    if count:
                        self.row -= int(count)
                    else:
                        self.row -= 1
                    assert self.row >= 1
                elif direction_code == 'B':
                    if count:
                        self.row += int(count)
                    else:
                        self.row += 1
                    self.row = min(self.row, len(self._lines))
                elif direction_code == 'C':
                    if count:
                        self.column += int(count)
                    else:
                        self.column += 1
                elif direction_code == 'D':
                    if count:
                        self.column -= int(count)
                    else:
                        self.column -= 1
                    self.column = max(1, self.column)
                else:
                    raise Exception(''.join(chars).encode('utf-8'))
            elif m := re.match(r'(\d+)G', ''.join(chars)):
                column = m.group(1)
                self.column = max(int(column), 1)
                for i in range(len(m.group(0))):
                    chars.pop(0)
            elif chars[:2] == ['2', 'K']:
                self._lines[self.row - 1] = [' '] * (self.column - 1)
                chars.pop(0)
                chars.pop(0)
            elif chars[:2] == ['6', 'n']:
                chars.pop(0)
                chars.pop(0)
                self._istream_buffer += f'\x1b[{self.row};{self.column}R'
            elif m := re.match(r'(\d+);(\d+)H', ''.join(chars)):
                for i in range(len(m.group(0))):
                    chars.pop(0)
                self.row = max(min(int(m.group(1)), self._height), 1)
                self.column = max(min(int(m.group(2)), self._width), 1)
            else:
                raise Exception(f'unhandled esacpe sequence {chars}')
        else:
            raise Exception(''.join(chars).encode('utf-8'))

    def flush(self):
        if self._echo:
            sys.stdout.flush()

    def get_string(self):
        line_strings = [''.join(line) for line in self._lines]
        return '\n'.join(line_strings)

    def __str__(self):
        return self.get_string()
