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
        self.edit_field = EditField(ostream=self.vterm)

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

    def check(self, expected, column, row=0):
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
        editor.check('hello world', 15)

    def test_move_left(self, editor):
        editor.move_cursor_left(5)
        editor.insert('to ')

        editor.check('hello to world', 13)

    def test_backspace(self, editor):
        editor.backspace(3)
        editor.check('hello world', 10)

    def test_newline(self, editor):
        editor.newline()
        editor.check('hello \nworld', 4, 1)

    def test_move_cursor_up(self, editor):
        editor.move_cursor_up()
        editor.insert('c')

        editor.check('chello \nworld', 5, 0)

    def test_move_cursor_down(self, editor):
        editor.move_cursor_down()
        editor.insert('here n')
        editor.check('chello \nwhere norld', 11, 1)

    def test_move_cursor_right(self, editor):
        editor.move_cursor_right(2)
        editor.insert('k wo')
        editor.check('chello \nwhere nork wold', 17, 1)


def test_move_cursor_down_to_empty_line(editor):
    for chars in ['hello', 'world']:
        editor.insert(chars)
        editor.newline()
    editor.move_cursor_up()
    assert editor.vterm.row == 1
    editor.move_cursor_down()
    assert editor.vterm.row == 2
    editor.insert('foo')
    editor.check('hello\nworld\nfoo', 7, 2)


def test_left_right_wrapping(editor):
    editor.insert('hello\nworld')
    editor.move_cursor_left(6)
    assert editor.vterm.row == 0
    assert editor.vterm.column == 9
    editor.insert('foo')
    editor.move_cursor_right()
    editor.insert('bar')
    editor.check('hellofoo\nbarworld', 7, 1)
