import sys
import re


class VirtualTerminal:

    def __init__(self, echo=False):
        self._lines = [[]]
        self.row = 0
        self.column = 0
        self._raw_input = []
        self._echo = echo

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
                if direction_code == 'A':
                    if count:
                        self.row -= int(count)
                    else:
                        self.row -= 1
                    assert self.row >= 0
                elif direction_code == 'B':
                    if count:
                        self.row += int(count)
                    else:
                        self.row += 1
                    self.row = min(self.row, len(self._lines) - 1)
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
                    self.column = max(0, self.column)
                else:
                    raise Exception(''.join(chars).encode('utf-8'))
            elif chars[:2] == ['2', 'K']:
                self._lines[self.row] = [' '] * self.column
                chars.pop(0)
                chars.pop(0)
            else:
                raise Exception('unhandled esacpe sequence')
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
