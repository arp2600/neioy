import neioy.escape_codes as ec
from neioy.escape_codes import parse_escape_code
from icecream import ic


def _test_parse_code(code_str):
    # parse each stage of the partial code before parsing the full code
    for i in range(len(code_str)):
        code = parse_escape_code(code_str[:i])
        assert code == None
    return parse_escape_code(code_str)


def test_parse_move_left():
    code = _test_parse_code('\x1b[D')
    assert isinstance(code, ec.MoveCursorLeft)
    assert str(code) == '\x1b[D'

    code = _test_parse_code('\x1b[7D')
    assert isinstance(code, ec.MoveCursorLeft)
    assert str(code) == '\x1b[7D'


def test_parse_move_right():
    code = _test_parse_code('\x1b[C')
    assert isinstance(code, ec.MoveCursorRight)
    assert str(code) == '\x1b[C'

    code = _test_parse_code('\x1b[7C')
    assert isinstance(code, ec.MoveCursorRight)
    assert str(code) == '\x1b[7C'


def test_parse_move_down():
    code = _test_parse_code('\x1b[B')
    assert isinstance(code, ec.MoveCursorDown)
    assert str(code) == '\x1b[B'

    code = _test_parse_code('\x1b[7B')
    assert isinstance(code, ec.MoveCursorDown)
    assert str(code) == '\x1b[7B'


def test_parse_move_up():
    code = _test_parse_code('\x1b[A')
    assert isinstance(code, ec.MoveCursorUp)
    assert str(code) == '\x1b[A'

    code = _test_parse_code('\x1b[7A')
    assert isinstance(code, ec.MoveCursorUp)
    assert str(code) == '\x1b[7A'


def test_parse_move_cursor_to():
    code_str = '\x1b[23;54H'
    code = _test_parse_code(code_str)
    assert isinstance(code, ec.MoveCursorTo)
    assert str(code) == code_str
