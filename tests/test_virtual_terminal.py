from virtual_terminal import VirtualTerminal
import sys
import time
import tty
import termios
import io


def show_sequence(input_string, delay=0.1):
    print('-' * 30)
    try:
        term_attrs = tty.setcbreak(sys.stdout.fileno())
    except io.UnsupportedOperation:
        raise Exception('Need to run pytest with -s (no capture)')

    for char in input_string:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    time.sleep(1.0)

    termios.tcsetattr(sys.stdout.fileno(), termios.TCSANOW, term_attrs)
    print()
    print('#' * 30)


def run_test(input_string,
             expected,
             column,
             row=1,
             terminal_height=50,
             example=None):
    if example is not None:
        show_sequence(input_string, delay=example)

    vterm = VirtualTerminal(height=terminal_height)
    vterm.write(input_string)
    assert str(vterm).rstrip() == expected
    assert vterm.column == column
    assert vterm.row == row


def test_hello_world():
    run_test('hello world', 'hello world', 12)


def test_move_left():
    run_test('hello world\x1b[D', 'hello world', 11)
    run_test('hello world\x1b[6D', 'hello world', 6)

    # left further than the screen
    # move to column 0 with the 5D and then test moving once more has no effect
    run_test('hello\x1b[5D\x1b[D', 'hello', 1)
    # a movement further than is able to be moved will put the cursor at column 0
    run_test('hello\x1b[8D', 'hello', 1)
    # moving left on the second line doesn't wrap
    run_test('hello\nworld\x1b[8D\x1b[D', 'hello\nworld', 1, 2)


def test_move_right():
    run_test('hello\x1b[Cworld', 'hello world', 12)
    run_test('hello\x1b[3Cworld', 'hello   world', 14)


def test_newline():
    # at the end of a line
    run_test('hello world\nfoo', 'hello world\nfoo', 4, 2)
    # in the middle of a line
    run_test('hello world\x1b[6D\nfoo', 'hello world\nfoo', 4, 2)


def test_move_up():
    run_test('fizz\nfoo bar\x1b[Abuzz', 'fizz   buzz\nfoo bar', 12, 1)
    # test multiple moves up
    run_test('foo\nbar\nfizz\x1b[2Abuzz', 'foo buzz\nbar\nfizz', 9, 1)


def test_move_down():
    run_test('\nfoo\x1b[Abar\x1b[Bfizz', '   bar\nfoo   fizz', 11, 2)
    # test move down multiple
    run_test('foo\nbar\nfizz\x1b[2Abuzz\x1b[2Bfin',
             'foo buzz\nbar\nfizz    fin', 12, 3)
    # test move down at bottom
    run_test('foo\x1b[Bbar', 'foobar', 7, 1, terminal_height=1)


def test_erase_line():
    run_test('foo\x1b[2Khello world', '   hello world', 15)


def test_move_to_column():
    run_test('hello world\x1b[3G', 'hello world', 3)
    run_test('hello world!!!\x1b[11G', 'hello world!!!', 11)
