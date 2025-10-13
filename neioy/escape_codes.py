import re
import inspect


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

    exec_str = f"""
class {name}:
    def __init__{init_sig}:
{assignments}

    def __str__(self):
        return {str_func.__name__}({str_args})
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


def parse_escape_code(chars):
    assert chars[0] == '\x1b'
    if m := re.match(r'\[(?P<code>[a-zA-Z])', chars[1:]):
        match m.group('code'):
            case 'A':
                return MoveCursorUp()
            case 'B':
                return MoveCursorDown()
            case 'C':
                return MoveCursorRight()
            case 'D':
                return MoveCursorLeft()
            case 'G':
                return MoveCursorToColumn()
            case _:
                raise Exception()
    elif m := re.match(r'\[(?P<amount>\d+)(?P<code>[a-zA-Z])', chars[1:]):
        amount = int(m.group('amount'))
        match amount, m.group('code'):
            case _, 'A':
                return MoveCursorUp(amount=amount)
            case _, 'B':
                return MoveCursorDown(amount=amount)
            case _, 'C':
                return MoveCursorRight(amount=amount)
            case _, 'D':
                return MoveCursorLeft(amount=amount)
            case _, 'G':
                return MoveCursorToColumn(column=amount)
            case 0, 'K':
                return EraseFromCursorToEndOfLine()
            case 2, 'K':
                return EraseLine()
            case _:
                raise Exception()
    elif m := re.match(r'\[(?P<row>\d+);(?P<column>\d+)H', chars[1:]):
        row = int(m.group('row'))
        column = int(m.group('column'))
        return MoveCursorTo(column=column, row=row)
    elif chars == '\x1b[?2004h':
        return EnableBracketedPaste()
    elif 'a' <= chars[-1] <= 'z':
        raise Exception(f'unrecognized escape code "{chars}"')
    elif 'A' <= chars[-1] <= 'Z':
        raise Exception(f'unrecognized escape code "{chars}"')
    else:
        return None
