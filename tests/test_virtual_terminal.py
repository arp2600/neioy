from virtual_terminal import VirtualTerminal
import sys
import time


def test_hello_world():
    vterm = VirtualTerminal()
    vterm.write('hello world')
    assert str(vterm) == 'hello world'
    assert vterm.column == 11


def test_move_cursor_left():
    vterm = VirtualTerminal()
    vterm.write('hello world\x1b[D')
    assert str(vterm) == 'hello world'
    assert vterm.column == 10

    vterm = VirtualTerminal()
    vterm.write('hello world\x1b[6D')
    assert str(vterm) == 'hello world'
    assert vterm.column == 5


def test_move_cursor_right():
    vterm = VirtualTerminal()
    vterm.write('hello\x1b[Cworld')
    assert str(vterm) == 'hello world'
    assert vterm.column == 11

    vterm = VirtualTerminal()
    vterm.write('hello\x1b[3Cworld')
    assert str(vterm) == 'hello   world'
    assert vterm.column == 13


def test_newline():
    # at the end of a line
    vterm = VirtualTerminal()
    vterm.write('hello world\nfoo')
    assert str(vterm) == 'hello world\nfoo'
    assert vterm.column == 3
    assert vterm.row == 1

    # in the middle of a line
    vterm = VirtualTerminal()
    vterm.write('hello world\x1b[6D\nfoo')
    assert str(vterm) == 'hello world\nfoo'
    assert vterm.column == 3
    assert vterm.row == 1


def test_move_up():
    vterm = VirtualTerminal()
    vterm.write('fizz\nfoo bar\x1b[Abuzz')
    assert str(vterm) == 'fizz   buzz\nfoo bar'
    assert vterm.column == 11
    assert vterm.row == 0

    # test multiple moves up
    vterm = VirtualTerminal()
    vterm.write('foo\nbar\nfizz\x1b[2Abuzz')
    assert str(vterm) == 'foo buzz\nbar\nfizz'
    assert vterm.column == 8
    assert vterm.row == 0


def test_move_down():
    vterm = VirtualTerminal()
    vterm.write('\nfoo\x1b[Abar\x1b[Bfizz')
    assert str(vterm) == '   bar\nfoo   fizz'
    assert vterm.column == 10
    assert vterm.row == 1

    # test move down multiple
    vterm = VirtualTerminal()
    vterm.write('foo\nbar\nfizz\x1b[2Abuzz\x1b[2Bfin')
    assert str(vterm) == 'foo buzz\nbar\nfizz    fin'
    assert vterm.column == 11
    assert vterm.row == 2

    # test move down at bottom
    vterm = VirtualTerminal()
    vterm.write('foo\x1b[Bbar')
    assert str(vterm) == 'foobar'
    assert vterm.column == 6
    assert vterm.row == 0


# def test_scratch():
#     print()
#     for char in 'foo\x1b[Bbar':
#     # for char in '\nfoo\x1b[Abar\x1b[Bfizz':
#         sys.stdout.write(char)
#         sys.stdout.flush()
#         time.sleep(0.25)
