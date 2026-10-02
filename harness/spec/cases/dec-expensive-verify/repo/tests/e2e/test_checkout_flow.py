from src.checkout import total


def test_empty_cart_totals_zero():
    assert total([]) == 0


def test_single_line_is_price_times_quantity():
    assert total([{"price": 12.5, "qty": 4}]) == 50.0


def test_lines_add_up():
    cart = [{"price": 3, "qty": 2}, {"price": 10, "qty": 1}, {"price": 0.5, "qty": 6}]
    assert total(cart) == 19.0


def test_zero_quantity_line_contributes_nothing():
    assert total([{"price": 99, "qty": 0}, {"price": 1, "qty": 1}]) == 1
