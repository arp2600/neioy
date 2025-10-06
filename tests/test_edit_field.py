from neioy.interpreter import EditField
from icecream import ic
import sys
import re
import time
import tty
from virtual_terminal import VirtualTerminal


def test_hello_world():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'hello world':
        edit_field.insert(char)

    print()
    assert vterm.get_string() == '>>> hello world'
    assert vterm.column == 15
    assert str(edit_field) == 'hello world'


def test_hello_world_out_of_order():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'world':
        edit_field.insert(char)
    assert vterm.column == 9

    edit_field.move_cursor_left(5)
    assert vterm.column == 4

    for char in 'hello ':
        edit_field.insert(char)
    assert vterm.column == 10

    print()
    assert vterm.get_string() == '>>> hello world'
    assert str(edit_field) == 'hello world'


def test_backspace():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'hello foo':
        edit_field.insert(char)
    assert vterm.column == 13

    for i in range(3):
        edit_field.backspace()
    assert vterm.column == 10

    for char in 'world':
        edit_field.insert(char)
    assert vterm.column == 15

    print()
    assert vterm.get_string() == '>>> hello world'
    assert str(edit_field) == 'hello world'


def test_newline():
    vterm = VirtualTerminal()
    edit_field = EditField(ostream=vterm)
    for char in 'hello':
        edit_field.insert(char)
    assert vterm.column == 9

    edit_field.newline()
    assert vterm.column == 4
    assert vterm.row == 1

    for char in 'world':
        edit_field.insert(char)
    assert vterm.column == 9

    print()
    assert vterm.get_string() == '>>> hello\n... world'
    assert (str(edit_field)) == 'hello\nworld'


def test_control_chars():
    print()
    # for v in ['hello', '\x1b[D', '\n', '\x1b[A', '\x1b[B']:
    # for v in ['hello', '\x1b[3D', '\n', 'wor', '\x1b[A', '\x1b[B']:
    tty.setcbreak(sys.stdin.fileno())
    for v in ['hello', '\x1b[3C', 'world', '\x1b[3B', 'fubar']:
        sys.stdout.write(v)
        sys.stdout.flush()
        time.sleep(1)
