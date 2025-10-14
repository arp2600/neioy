import re
import inspect
from icecream import ic


def _snake_to_camel_case(name):
    return ''.join(x.capitalize() for x in name.split('_'))


def _self_parameter():
    return inspect.Parameter('self',
                             kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)


def _escape_code(str_func):
    name = _snake_to_camel_case(str_func.__name__)

    sig = inspect.signature(str_func)

    init_params = [_self_parameter()]
    init_params.extend(sig.parameters.values())
    init_sig = str(inspect.Signature(init_params))

    indent = ' ' * 8
    assignments = [f'{indent}self.{x} = {x}' for x in sig.parameters.keys()]
    if assignments:
        assignments = '\n'.join(assignments)
    else:
        assignments = f'{indent}pass'

    str_args = [f'self.{x}' for x in sig.parameters.keys()]
    str_args = ', '.join(str_args)

    repr_args = [f'{x}={{self.{x}}}' for x in sig.parameters.keys()]
    repr_args = ', '.join(repr_args)

    exec_str = f"""
class {name}:
    def __init__{init_sig}:
{assignments}

    def __str__(self):
        return {str_func.__name__}({str_args})

    def __repr__(self):
        return f"{name}({repr_args})"
"""

    exec_locals = {}
    exec(exec_str, locals=exec_locals)
    globals()[f'{name}'] = exec_locals[f'{name}']
    return str_func


@_escape_code
def enable_bracketed_paste():
    """Write to stdout to enable bracketed paste for this application"""
    return "\x1b[?2004h"


@_escape_code
def disable_bracketed_paste():
    """Write to stdout to enable bracketed paste for this application"""
    return "\x1b[?2004l"


@_escape_code
def bracketed_paste_start():
    """When read from stdin this marks the start of a bracketed paste input"""
    return "\x1b[200~"


@_escape_code
def bracketed_paste_end():
    """When read from stdin this marks the end of a bracketed paste input"""
    return "\x1b[201~"


def _move_cursor(direction_code, amount):
    if amount <= 0:
        raise Exception()

    if amount == 1:
        return f'\x1b[{direction_code}'
    else:
        return f'\x1b[{amount}{direction_code}'


@_escape_code
def move_cursor_left(amount=1):
    return _move_cursor('D', amount)


@_escape_code
def move_cursor_right(amount=1):
    return _move_cursor('C', amount)


@_escape_code
def move_cursor_up(amount=1):
    return _move_cursor('A', amount)


@_escape_code
def move_cursor_down(amount=1):
    return _move_cursor('B', amount)


@_escape_code
def erase_from_cursor_to_end_of_line():
    return '\x1b[0K'


@_escape_code
def erase_line():
    return '\x1b[2K'


@_escape_code
def move_cursor_to_column(column):
    assert column >= 0
    return f'\x1b[{column}G'


@_escape_code
def move_cursor_to(row, column):
    return f'\x1b[{row};{column}H'


@_escape_code
def request_cursor_position():
    return '\x1b[6n'


@_escape_code
def reported_cursor_position(row, column):
    return f'\x1b[{row};{column}R'


def _parse_int(chars, start):
    int_str = chars[start]
    i = start + 1
    while i < len(chars) and ('0' <= chars[i] <= '9'):
        int_str += chars[i]
        i += 1
    return int(chars[start:i]), i


def _unrecognized_sequence_exception(chars):
    return Exception('unrecognised sequence {chars.encode("utf-8")}')


def _parse_csi_with_two_values(chars, i, value_1):
    assert '0' <= chars[i] <= '9'
    value_2, i = _parse_int(chars, i)

    match chars[i]:
        case 'H':
            return MoveCursorTo(row=value_1, column=value_2)
        case 'R':
            return ReportedCursorPosition(row=value_1, column=value_2)
        case _:
            raise _unrecognized_sequence_exception(chars)


def _parse_csi_with_value(chars, i):
    value_1, i = _parse_int(chars, i)

    match value_1, chars[i]:
        case _, 'A':
            return MoveCursorUp(amount=value_1)
        case _, 'B':
            return MoveCursorDown(amount=value_1)
        case _, 'C':
            return MoveCursorRight(amount=value_1)
        case _, 'D':
            return MoveCursorLeft(amount=value_1)
        case _, 'G':
            return MoveCursorToColumn(column=value_1)
        case 6, 'n':
            return RequestCursorPosition()
        case 0, 'K':
            return EraseFromCursorToEndOfLine()
        case 2, 'K':
            return EraseLine()
        case 200, '~':
            return BracketedPasteStart()
        case 201, '~':
            return BracketedPasteEnd()
        case _, ';':
            return _parse_csi_with_two_values(chars, i + 1, value_1)
        case _:
            raise _unrecognized_sequence_exception(chars)


def _parse_bracketed_paste_command(chars, i):
    value, i = _parse_int(chars, i)
    match value, chars[i]:
        case 2004, 'h':
            return EnableBracketedPaste()
        case 2004, 'l':
            return DisableBracketedPaste()
        case _:
            raise _unrecognized_sequence_exception(chars)


def _parse_csi_command(chars):
    i = 2
    match chars[i]:
        case 'A':
            return MoveCursorUp()
        case 'B':
            return MoveCursorDown()
        case 'C':
            return MoveCursorRight()
        case 'D':
            return MoveCursorLeft()
        case '?':
            return _parse_bracketed_paste_command(chars, i + 1)
        case _ if chars[i].isdigit():
            return _parse_csi_with_value(chars, i)
        case _:
            raise _unrecognized_sequence_exception(chars)


def parse_escape_code(chars):
    try:
        assert chars[0] == '\x1b'

        if chars[1] == '[':
            return _parse_csi_command(chars)
        else:
            raise _unrecognized_sequence_exception(chars)

    except IndexError:
        return None  # incomplete sequence
