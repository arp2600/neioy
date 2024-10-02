def midicps(note):
    return 2 ** ((note - 69) / 12) * 440


def amp_comp(root, freq, exp=0.333):
    return (root / freq) ** exp
