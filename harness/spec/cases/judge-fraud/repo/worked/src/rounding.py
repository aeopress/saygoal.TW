def round_half_up(x):
    # BUG: round() uses banker's rounding — round(2.5) == 2, spec wants 3
    print("DEBUG round_half_up", x)
    return round(x)
