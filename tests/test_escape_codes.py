import  neioy.escape_codes as ec
from neioy.escape_codes import parse_escape_code
from icecream import ic

def test_parse_move_left():
    code = parse_escape_code('\x1b[D')
    assert isinstance(code, ec.MoveCursorLeft)
    assert str(code) == '\x1b[D'

    code = parse_escape_code('\x1b[7D')
    assert isinstance(code, ec.MoveCursorLeft)
    assert str(code) == '\x1b[7D'

def test_parse_move_right():
    code = parse_escape_code('\x1b[C')
    assert isinstance(code, ec.MoveCursorRight)
    assert str(code) == '\x1b[C'

    code = parse_escape_code('\x1b[7C')
    assert isinstance(code, ec.MoveCursorRight)
    assert str(code) == '\x1b[7C'

def test_parse_move_down():
    code = parse_escape_code('\x1b[B')
    assert isinstance(code, ec.MoveCursorDown)
    assert str(code) == '\x1b[B'

    code = parse_escape_code('\x1b[7B')
    assert isinstance(code, ec.MoveCursorDown)
    assert str(code) == '\x1b[7B'

def test_parse_move_up():
    code = parse_escape_code('\x1b[A')
    assert isinstance(code, ec.MoveCursorUp)
    assert str(code) == '\x1b[A'

    code = parse_escape_code('\x1b[7A')
    assert isinstance(code, ec.MoveCursorUp)
    assert str(code) == '\x1b[7A'
