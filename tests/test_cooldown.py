"""The per-user pause between searches."""

import pytest

from sneaker_bot.services import cooldown


@pytest.fixture(autouse=True)
def clean_state():
    cooldown.reset()
    yield
    cooldown.reset()


def test_first_search_is_allowed():
    assert cooldown.remaining(1, now=100.0) == 0


def test_second_search_is_blocked_for_the_full_window():
    cooldown.mark(1, now=100.0)
    assert cooldown.remaining(1, now=100.0) == 15
    assert cooldown.remaining(1, now=105.0) == 10
    assert cooldown.remaining(1, now=114.5) == 1


def test_window_expires():
    cooldown.mark(1, now=100.0)
    assert cooldown.remaining(1, now=115.0) == 0
    assert cooldown.remaining(1, now=200.0) == 0


def test_users_are_independent():
    cooldown.mark(1, now=100.0)
    assert cooldown.remaining(1, now=101.0) > 0
    assert cooldown.remaining(2, now=101.0) == 0


def test_custom_window():
    cooldown.mark(1, now=0.0)
    assert cooldown.remaining(1, seconds=30, now=1.0) == 29
