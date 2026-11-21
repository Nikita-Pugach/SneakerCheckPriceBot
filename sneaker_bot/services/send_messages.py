import logging
from typing import Union

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from sneaker_bot.services.messages import track

logger = logging.getLogger(__name__)


async def record_and_send(
    ctx: Union[Message, CallbackQuery],
    state: FSMContext,
    text: str,
    **kwargs,
) -> Message:
    """Send a message and remember it, so purge() can remove it later."""
    if isinstance(ctx, CallbackQuery):
        try:
            # A callback can only be answered once; a second attempt is harmless
            # but raises, which used to abort the handler.
            await ctx.answer()
        except TelegramBadRequest:
            pass
        sent = await ctx.message.answer(text, **kwargs)
    else:
        sent = await ctx.answer(text, **kwargs)

    await track(state, sent)
    return sent


async def send_prompt(
    ctx: Union[Message, CallbackQuery],
    state: FSMContext,
    text: str,
    **kwargs,
) -> Message:
    """Send a prompt and remember it both as tracked and as the last prompt."""
    sent = await record_and_send(ctx, state, text, **kwargs)

    data = await state.get_data()
    prompts = data.get("prompt_refs", [])
    prompts.append({"chat_id": sent.chat.id, "message_id": sent.message_id})
    await state.update_data(prompt_refs=prompts)

    return sent
