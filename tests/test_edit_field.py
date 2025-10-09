from neioy.interpreter import EditField
from icecream import ic
import sys
import re
import time
import tty
import pytest
from virtual_terminal import VirtualTerminal


class _TestHarness:

    def __init__(self):
        self.vterm = VirtualTerminal()
        self.edit_field = EditField(istream=self.vterm, ostream=self.vterm)

    def insert(self, chars):
        for char in chars:
            if char == '\n':
                self.edit_field.newline()
            else:
                self.edit_field.insert(char)

    def __getattr__(self, name):
        return getattr(self.edit_field, name)

    def backspace(self, count=1):
        for i in range(count):
            self.edit_field.backspace()

    def newline(self, count=1):
        for i in range(count):
            self.edit_field.newline()

    def check(self, expected, column, row=1):
        print()
        print(str(self.vterm))

        # Add the prompt onto expected to test vterms output.
        expected_vterm = self.edit_field.ps1 + expected.replace(
            '\n', '\n' + self.edit_field.ps2)

        assert str(self.vterm) == expected_vterm
        assert self.vterm.column == column
        assert self.vterm.row == row
        assert str(self.edit_field) == expected


@pytest.fixture(scope='class')
def editor():
    return _TestHarness()


class TestMovements:
    """
    The tests are placed in a class and use a fixture with class scope. This allows each
    test to continue the output of the last test, which is useful for testing the
    movements in isolation.
    """

    def test_insert(self, editor):
        editor.insert('hello world')
        print(editor.vterm.raw_input().encode('utf-8'))
        editor.check('hello world', 16)

    def test_move_left(self, editor):
        editor.move_cursor_left(5)
        editor.insert('to ')

        editor.check('hello to world', 14)

    def test_backspace(self, editor):
        editor.backspace(3)
        editor.check('hello world', 11)

    def test_newline(self, editor):
        editor.newline()
        editor.check('hello \nworld', 5, 2)

    def test_move_cursor_up(self, editor):
        editor.move_cursor_up()
        editor.insert('c')

        editor.check('chello \nworld', 6, 1)

    def test_move_cursor_down(self, editor):
        editor.move_cursor_down()
        editor.insert('here n')
        editor.check('chello \nwhere norld', 12, 2)

    def test_move_cursor_right(self, editor):
        editor.move_cursor_right(2)
        editor.insert('k wo')
        editor.check('chello \nwhere nork wold', 18, 2)


def test_move_cursor_down_to_empty_line(editor):
    for chars in ['hello', 'world']:
        editor.insert(chars)
        editor.newline()
    editor.move_cursor_up()
    assert editor.vterm.row == 2
    editor.move_cursor_down()
    assert editor.vterm.row == 3
    editor.insert('foo')
    editor.check('hello\nworld\nfoo', 8, 3)


def test_left_right_wrapping(editor):
    editor.insert('hello\nworld')
    editor.move_cursor_left(6)
    assert editor.vterm.row == 1
    assert editor.vterm.column == 10
    editor.insert('foo')
    editor.move_cursor_right()
    editor.insert('bar')
    editor.check('hellofoo\nbarworld', 8, 2)
