"""Free-form text turned into a search query."""

from sneaker_bot.services.text_query import MAX_LENGTH, MIN_LENGTH, clean_query


def test_plain_query_is_kept():
    assert clean_query("nike air max 42") == "nike air max 42"


def test_extra_spaces_are_collapsed():
    assert clean_query("  nike   air    max  ") == "nike air max"


def test_newlines_and_tabs_are_collapsed():
    assert clean_query("nike\nair\tmax") == "nike air max"


def test_commands_are_not_queries():
    assert clean_query("/start") is None
    assert clean_query("/help me") is None


def test_too_short_is_ignored():
    assert clean_query("") is None
    assert clean_query("   ") is None
    assert clean_query("a" * (MIN_LENGTH - 1)) is None


def test_too_long_is_ignored():
    assert clean_query("a" * (MAX_LENGTH + 1)) is None


def test_exact_bounds_are_accepted():
    assert clean_query("a" * MIN_LENGTH) is not None
    assert clean_query("a" * MAX_LENGTH) is not None
