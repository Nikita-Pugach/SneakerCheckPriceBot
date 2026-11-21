"""normalize_price keeps whatever digits and currency the page shows."""

import pytest

from sneaker_bot.parsers.price_parser import normalize_price


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", "—"),
        ("   ", "—"),
        ("нет цены", "—"),
        ("4999", "4999"),
        ("2999 BYN", "2999 BYN"),
        ("1 299,00 BYN", "1 299.00 BYN"),
        ("2990 RUB", "2990 ₽"),
        ("150 USD", "150 USD"),
        ("99 €", "99 €"),
        # trailing words after the amount are dropped, not glued to the price
        ("от 1 200,50 руб.", "1 200.50"),
    ],
)
def test_normalize_price(raw, expected):
    assert normalize_price(raw) == expected


def test_comma_becomes_a_dot():
    assert normalize_price("1299,99 BYN") == "1299.99 BYN"
