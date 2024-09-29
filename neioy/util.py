def midicps(note):
    return 2 ** ((note - 69) / 12) * 440
