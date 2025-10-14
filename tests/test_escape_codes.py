import neioy.escape_codes as ec
from neioy.escape_codes import parse_escape_code
from icecream import ic
import pytest


@pytest.mark.parametrize("code_str, code_class", [
    ('\x1b[D', ec.MoveCursorLeft),
    ('\x1b[3D', ec.MoveCursorLeft),
    ('\x1b[12D', ec.MoveCursorLeft),
    ('\x1b[C', ec.MoveCursorRight),
    ('\x1b[8C', ec.MoveCursorRight),
    ('\x1b[45C', ec.MoveCursorRight),
    ('\x1b[B', ec.MoveCursorDown),
    ('\x1b[5B', ec.MoveCursorDown),
    ('\x1b[67B', ec.MoveCursorDown),
    ('\x1b[A', ec.MoveCursorUp),
    ('\x1b[7A', ec.MoveCursorUp),
    ('\x1b[23A', ec.MoveCursorUp),
    ('\x1b[9G', ec.MoveCursorToColumn),
    ('\x1b[13G', ec.MoveCursorToColumn),
    ('\x1b[2;5H', ec.MoveCursorTo),
    ('\x1b[23;54H', ec.MoveCursorTo),
    ('\x1b[?2004h', ec.EnableBracketedPaste),
    ('\x1b[?2004l', ec.DisableBracketedPaste),
    ('\x1b[200~', ec.BracketedPasteStart),
    ('\x1b[201~', ec.BracketedPasteEnd),
    ('\x1b[0K', ec.EraseFromCursorToEndOfLine),
    ('\x1b[2K', ec.EraseLine),
    ('\x1b[6n', ec.RequestCursorPosition),
    ('\x1b[12;34R', ec.ReportedCursorPosition),
])
def test_parsing_code(code_str, code_class):
    # parse each stage of the partial code before parsing the full code
    for i in range(len(code_str)):
        code = parse_escape_code(code_str[:i])
        assert code == None

    code = parse_escape_code(code_str)
    assert isinstance(code, code_class)
    assert str(code) == code_str
