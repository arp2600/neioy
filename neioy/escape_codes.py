def _create_code(code_func):

    class Code:

        def __init__(self, *args):
            self.args = args

        def __str__(self):
            return code_func(*self.args)

    return Code


def enable_bracketed_paste():
    return "\x1b[?2004h"


EnableBracketedPaste = _create_code(enable_bracketed_paste)


def _move_cursor(direction_code, amount):
    if amount <= 0:
        raise Exception()

    if amount == 1:
        return f'\x1b[{direction_code}'
    else:
        return f'\x1b[{amount}{direction_code}'


def move_cursor_left(amount=1):
    return _move_cursor('D', amount)


MoveCursorLeft = _create_code(move_cursor_left)


def move_cursor_right(amount=1):
    return _move_cursor('C', amount)


MoveCursorRight = _create_code(move_cursor_right)


def move_cursor_up(amount=1):
    return _move_cursor('A', amount)


MoveCursorUp = _create_code(move_cursor_up)


def move_cursor_down(amount=1):
    return _move_cursor('B', amount)


MoveCursorDown = _create_code(move_cursor_down)


def erase_from_cursor_to_end_of_line():
    return '\x1b[0K'


EraseFromCursorToEndOfLine = _create_code(erase_from_cursor_to_end_of_line)


def erase_line():
    return '\x1b[2K'


EraseLine = _create_code(erase_line)


def move_cursor_to_column(column):
    assert column >= 0
    return f'\x1b[{column}G'


MoveCursorToColumn = _create_code(move_cursor_to_column)


def move_cursor_to(row, column):
    return f'\x1b[{row};{column}H'


MoveCursorTo = _create_code(move_cursor_to)


def request_cursor_position():
    return '\x1b[6n'


RequestCursorPosition = _create_code(request_cursor_position)
