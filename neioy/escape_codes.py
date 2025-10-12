import re


def _escape_code(str_func):

    def wrap_init(init_func, params):

        def wrapper(self, **kwargs):
            init_func(self)
            for arg, value in params.items():
                if arg in kwargs:
                    value = kwargs[arg]
                setattr(self, arg, value)

        return wrapper

    def wrap_str_func(str_func, params):

        def str_wrapper(self):
            kwargs = {arg: getattr(self, arg) for arg in params.keys()}
            return str_func(**kwargs)

        return str_wrapper

    def wrapper(cls):
        params = {i: v for i, v in vars(cls).items() if not i.startswith('__')}
        cls.__init__ = wrap_init(cls.__init__, params)
        cls.__str__ = wrap_str_func(str_func, params)
        return cls

    return wrapper


def enable_bracketed_paste():
    return "\x1b[?2004h"


@_escape_code(enable_bracketed_paste)
class EnableBracketedPaste:
    pass


def _move_cursor(direction_code, amount):
    if amount <= 0:
        raise Exception()

    if amount == 1:
        return f'\x1b[{direction_code}'
    else:
        return f'\x1b[{amount}{direction_code}'


def move_cursor_left(amount=1):
    return _move_cursor('D', amount)


@_escape_code(move_cursor_left)
class MoveCursorLeft:
    amount = 1


def move_cursor_right(amount=1):
    return _move_cursor('C', amount)


@_escape_code(move_cursor_right)
class MoveCursorRight:
    amount = 1


def move_cursor_up(amount=1):
    return _move_cursor('A', amount)


@_escape_code(move_cursor_up)
class MoveCursorUp:
    amount = 1


def move_cursor_down(amount=1):
    return _move_cursor('B', amount)


@_escape_code(move_cursor_down)
class MoveCursorDown:
    amount = 1


def erase_from_cursor_to_end_of_line():
    return '\x1b[0K'


@_escape_code(erase_from_cursor_to_end_of_line)
class EraseFromCursorToEndOfLine:
    pass


def erase_line():
    return '\x1b[2K'


@_escape_code(erase_line)
class EraseLine:
    pass


def move_cursor_to_column(column):
    assert column >= 0
    return f'\x1b[{column}G'


@_escape_code(move_cursor_to_column)
class MoveCursorToColumn:
    column = 1


def move_cursor_to(row, column):
    return f'\x1b[{row};{column}H'


@_escape_code(move_cursor_to)
class MoveCursorTo:
    column = 1
    row = 1


def request_cursor_position():
    return '\x1b[6n'


@_escape_code(request_cursor_position)
class RequestCursorPosition:
    pass


def parse_escape_code(chars):
    assert chars[0] == '\x1b'
    if m := re.match(r'\[(?P<amount>\d+)?(?P<code>[a-zA-Z])', chars[1:]):

        def get_amount(default):
            if m.group('amount'):
                return int(m.group('amount'))
            else:
                return default

        amount = m.group('amount')

        match amount, m.group('code'):
            case _, 'A':
                return MoveCursorUp(amount=get_amount(1))
            case _, 'B':
                return MoveCursorDown(amount=get_amount(1))
            case _, 'C':
                return MoveCursorRight(amount=get_amount(1))
            case _, 'D':
                return MoveCursorLeft(amount=get_amount(1))
            case _, 'G':
                return MoveCursorToColumn(column=int(amount))
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
