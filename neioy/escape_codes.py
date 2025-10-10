class EscapeCodes:

    @staticmethod
    def enable_bracketed_paste():
        return "\x1b[?2004h"

    @staticmethod
    def _move_cursor(direction_code, amount):
        if amount <= 0:
            raise Exception()

        if amount == 1:
            return f'\x1b[{direction_code}'
        else:
            return f'\x1b[{amount}{direction_code}'

    @staticmethod
    def move_cursor_left(amount=1):
        return EscapeCodes._move_cursor('D', amount)

    @staticmethod
    def move_cursor_right(amount=1):
        return EscapeCodes._move_cursor('C', amount)

    @staticmethod
    def move_cursor_up(amount=1):
        return EscapeCodes._move_cursor('A', amount)

    @staticmethod
    def move_cursor_down(amount=1):
        return EscapeCodes._move_cursor('B', amount)

    @staticmethod
    def erase_from_cursor_to_end_of_line():
        return '\x1b[0K'

    @staticmethod
    def erase_line():
        return '\x1b[2K'

    @staticmethod
    def move_to_column(column):
        assert column >= 0
        return f'\x1b[{column}G'

    @staticmethod
    def move_cursor_to(row, column):
        return f'\x1b[{row};{column}H'

    @staticmethod
    def request_cursor_position():
        return '\x1b[6n'
