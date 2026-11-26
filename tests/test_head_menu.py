"""The main menu: no placeholders, no stale personal links."""

from sneaker_bot.handlers.help_command import HELP_TEXT
from sneaker_bot.menu.head_menu import REPO_URL, head_menu


def callbacks() -> list[str]:
    return [
        button.callback_data
        for row in head_menu.inline_keyboard
        for button in row
        if button.callback_data
    ]


def urls() -> list[str]:
    return [
        button.url
        for row in head_menu.inline_keyboard
        for button in row
        if button.url
    ]


def test_menu_has_the_working_actions():
    data = callbacks()
    assert "know_button" in data
    assert "news_button" in data
    assert "history_button" in data
    assert "help_button" in data


def test_the_order_placeholder_is_gone():
    assert "order_button" not in callbacks()


def test_help_text_points_to_the_repository():
    # The menu button opens the in-bot help now, so the link lives in its text.
    assert REPO_URL in HELP_TEXT
    assert "SkForbes" not in HELP_TEXT


def test_every_row_has_at_most_two_buttons():
    assert all(len(row) <= 2 for row in head_menu.inline_keyboard)
