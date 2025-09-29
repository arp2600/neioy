from neioy.interpreter import TextEditor


def test_text_editor_insert():
    # basic test, single line of input
    sb = TextEditor()
    for char in 'hello world':
        sb.insert(char)
    assert str(sb) == 'hello world'

    # multi line string
    sb = TextEditor()
    for char in 'hello\nworld':
        sb.insert(char)
    assert str(sb) == 'hello\nworld'


def test_move_up():
    sb = TextEditor()
    for char in 'hello\nthe world':
        sb.insert(char)
    sb.move_up(1)
    for char in ' from':
        sb.insert(char)

    assert str(sb) == 'hello from\nthe world'


def test_move_up_midline():
    sb = TextEditor()
    for char in 'heo to the\nwrld':
        sb.insert(char)
    sb.move_left(3)
    sb.insert('o')
    sb.move_up(1)
    for char in 'll':
        sb.insert(char)

    assert str(sb) == 'hello to the\nworld'


def test_move_down():
    sb = TextEditor()
    for char in 'hello from\nworld':
        sb.insert(char)
    sb.move_up(1)
    sb.move_left(99)
    sb.move_down(1)
    for char in 'the ':
        sb.insert(char)

    assert str(sb) == 'hello from\nthe world'


def test_move_up_and_down_end_of_line():
    sb = TextEditor()
    for char in 'the first line\n':
        sb.insert(char)
    for char in 'this should be the longest line\n':
        sb.insert(char)
    for char in 'short line.':
        sb.insert(char)
    sb.move_up(1)
    sb.insert('.')
    sb.move_up(1)
    sb.insert('.')
    assert str(
        sb) == 'the first line.\nthis should be the longest line.\nshort line.'
    sb.insert('*')
    sb.move_down(1)
    sb.insert('*')
    sb.move_down(1)
    sb.insert('*')
    assert str(
        sb
    ) == 'the first line.*\nthis should be the longest line.*\nshort line.*'


def test_move_left_wraps():
    sb = TextEditor()
    for char in 'print(\n,2)':
        sb.insert(char)
    sb.move_left(4)
    sb.insert('1')
    assert str(sb) == 'print(1\n,2)'

    sb = TextEditor()
    for char in 'print(\n,2\n,3)':
        sb.insert(char)
    sb.move_left(7)
    sb.insert('1')
    assert str(sb) == 'print(1\n,2\n,3)'


def test_move_left_bounds():
    sb = TextEditor()
    for char in 'world':
        sb.insert(char)
    sb.move_left(99)
    for char in 'hello ':
        sb.insert(char)
    assert str(sb) == 'hello world'


def test_move_right_wraps():
    sb = TextEditor()
    for char in 'print(1\n,)':
        sb.insert(char)
    sb.move_left(5)
    sb.move_right(4)
    sb.insert('2')
    assert str(sb) == 'print(1\n,2)'


def test_move_right_bounds():
    sb = TextEditor()
    for char in 'hello ':
        sb.insert(char)
    sb.move_left(6)
    sb.move_right(99)
    for char in 'world':
        sb.insert(char)
    assert str(sb) == 'hello world'


def test_split_line():
    sb = TextEditor()
    for char in 'hello world':
        sb.insert(char)
    sb.move_left(6)
    sb.insert('\n')
    assert str(sb) == 'hello\n world'


def test_pop():
    sb = TextEditor()
    for char in "this is a big ol'world":
        sb.insert(char)
    sb.move_left(99)
    for i in range(len("this is a big ol'")):
        sb.pop()
    for char in 'hello ':
        sb.insert(char)

    assert str(sb) == 'hello world'


def test_pop_at_end_of_line():
    sb = TextEditor()
    for char in "hello\nworld":
        sb.insert(char)
    sb.move_up(1)
    sb.pop()
    sb.insert(' ')

    assert str(sb) == 'hello world'


def test_pop_at_end_of_buffer():
    sb = TextEditor()
    for char in "hello\nworld":
        sb.insert(char)
    sb.pop()  # shouldn't do anything

    assert str(sb) == 'hello\nworld'
