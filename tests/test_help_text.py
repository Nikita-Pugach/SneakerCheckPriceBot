"""The /help text: short enough for one message and actually useful."""

from sneaker_bot.handlers.help_command import HELP_TEXT
from sneaker_bot.menu.head_menu import REPO_URL


def test_help_fits_into_one_telegram_message():
    assert len(HELP_TEXT) < 4096


def test_help_explains_both_ways_to_search():
    lowered = HELP_TEXT.lower()
    assert "кнопками" in lowered
    assert "напишите" in lowered


def test_help_names_the_shops():
    for shop in ("bunt.by", "sneakers.by", "kufar.by"):
        assert shop in HELP_TEXT


def test_help_links_the_repository():
    assert REPO_URL in HELP_TEXT


def test_help_mentions_the_commands():
    assert "/start" in HELP_TEXT
    assert "/help" in HELP_TEXT
