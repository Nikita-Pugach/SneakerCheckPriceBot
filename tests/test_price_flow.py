"""The guided search as a conversation: brand -> model -> size -> query.

Handlers are called directly with fake aiogram objects, so the whole path runs
without a bot token, a network or a dispatcher. The decorator skips its
subscription check for these objects because they are not real Message
instances, which is exactly what keeps the test offline.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from sneaker_bot.handlers import know_button
from sneaker_bot.handlers.know_button import KnowPriceSG


class FakeState:
    """Minimal FSMContext: just enough for handlers to run."""

    def __init__(self) -> None:
        self.data: dict = {}
        self.state = None

    async def get_data(self) -> dict:
        return dict(self.data)

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)

    async def set_state(self, state) -> None:
        self.state = state

    async def clear(self) -> None:
        self.data.clear()
        self.state = None


def make_message(text: str, user_id: int = 1, chat_id: int = 2) -> MagicMock:
    message = MagicMock()
    message.text = text
    message.from_user = MagicMock(id=user_id)
    message.chat = MagicMock(id=chat_id)
    sent = MagicMock()
    sent.chat.id = chat_id
    sent.message_id = 100
    message.answer = AsyncMock(return_value=sent)
    message.delete = AsyncMock()
    message.bot = AsyncMock()
    return message


async def _walk_the_flow() -> None:
    state = FakeState()
    search = AsyncMock()

    with patch.object(know_button, "process_price_search", search):
        await know_button.brand_text(make_message("Nike"), state)
        assert state.state == KnowPriceSG.waiting_for_model
        assert state.data["brand"] == "nike"

        await know_button.model_text(make_message("Air Max"), state)
        assert state.state == KnowPriceSG.waiting_for_size
        assert state.data["model"] == "air max"

        await know_button.size_text(make_message("42"), state)
        # the search itself runs as a background task
        await asyncio.sleep(0.05)

    search.assert_awaited_once()
    user_id, _ctx, _state, query = search.await_args.args
    assert user_id == 1
    assert query == "nike air max 42"


def test_guided_flow_builds_the_query():
    asyncio.run(_walk_the_flow())


async def _skip_size() -> None:
    state = FakeState()
    search = AsyncMock()

    with patch.object(know_button, "process_price_search", search):
        await know_button.brand_text(make_message("adidas"), state)
        await know_button.model_text(make_message("посмотреть все"), state)
        await know_button.size_text(make_message("нет"), state)
        await asyncio.sleep(0.05)

    assert search.await_args.args[3] == "adidas"


def test_show_all_and_no_size_are_skipped():
    asyncio.run(_skip_size())
