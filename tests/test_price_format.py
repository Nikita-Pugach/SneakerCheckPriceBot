"""Parsing and formatting of prices ("1 234,50 BYN" and friends)."""

from sneaker_bot.services.price_format import (
    format_amount,
    parse_price,
    plural,
)


def test_plain_price_is_parsed():
    assert parse_price("2999 BYN") == 2999


def test_thousands_and_decimals_are_parsed():
    assert parse_price("1 234,50 BYN") == 1234.5
    assert parse_price("1\u00a0234 BYN") == 1234


def test_placeholders_have_no_price():
    for value in ("", None, "—", "–", "ошибка", "цена по запросу"):
        assert parse_price(value) is None


def test_whole_amounts_have_no_decimals():
    assert format_amount(250) == "250 BYN"
    assert format_amount(250.0) == "250 BYN"


def test_fractional_amounts_use_a_comma():
    assert format_amount(1234.5) == "1 234,50 BYN"


def test_large_amounts_get_space_separators():
    assert format_amount(12500) == "12 500 BYN"


def test_russian_plural_forms():
    assert plural(1, "предложение", "предложения", "предложений") == "предложение"
    assert plural(3, "предложение", "предложения", "предложений") == "предложения"
    assert plural(11, "предложение", "предложения", "предложений") == "предложений"
    assert plural(21, "предложение", "предложения", "предложений") == "предложение"
