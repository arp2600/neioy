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
            self.edit_field.insert(char)

    def move_cursor_left(self, amount=1):
        self.edit_field.move_cursor_left(amount)

    def backspace(self, count=1):
        for i in range(count):
            self.edit_field.backspace()

    def newline(self, count=1):
        for i in range(count):
            self.edit_field.newline()

    def check_term(self, expected, column, row=0):
        print(
        )  # useful for preserving terminal output to manually check result
        assert str(self.vterm) == expected
        assert self.vterm.column == column
        assert self.vterm.row == row

    def check_text(self, expected):
        assert str(self.edit_field) == expected


@pytest.fixture
def editor():
    return _TestHarness()


def test_hello_world(editor):
    editor.insert('hello world')
    editor.check_term('>>> hello world', 15)
    editor.check_text('hello world')


def test_move_left_and_insert(editor):
    editor.insert('world')
    assert editor.vterm.column == 9
    editor.move_cursor_left(5)
    assert editor.vterm.column == 4
    editor.insert('hello ')

    editor.check_term('>>> hello world', 10)
    editor.check_text('hello world')


def test_backspace(editor):
    editor.insert('hello foo')
    assert editor.vterm.column == 13
    editor.backspace(3)
    assert editor.vterm.column == 10
    editor.insert('world')
    editor.check_term('>>> hello world', 15)
    editor.check_text('hello world')


def test_newline(editor):
    editor.insert('hello')
    assert editor.vterm.column == 9
    editor.newline()
    assert editor.vterm.column == 4
    assert editor.vterm.row == 1

    editor.insert('world')
    editor.check_term('>>> hello\n... world', 9, 1)
    editor.check_text('hello\nworld')
