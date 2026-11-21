"""Import-time environment for the test suite.

`sneaker_bot.setting` builds a Bot object at import time, and aiogram validates
the token format, so the handler tests need a syntactically valid fake token.
Nothing here talks to Telegram.
"""

import os

os.environ.setdefault("SECRET_TOKEN_BOT", "123456789:" + "A" * 35)
