"""Import-time environment for the test suite.

`sneaker_bot.setting` builds a Bot object at import time, and aiogram validates
the token format, so the handler tests need a syntactically valid fake token.
Nothing here talks to Telegram.
"""

import os

import pytest

os.environ.setdefault("SECRET_TOKEN_BOT", "123456789:" + "A" * 35)


@pytest.fixture(autouse=True)
def reset_search_cooldown():
    """Every test starts with no cooldown applied to any user."""
    from sneaker_bot.services import cooldown

    cooldown.reset()
    yield
    cooldown.reset()
