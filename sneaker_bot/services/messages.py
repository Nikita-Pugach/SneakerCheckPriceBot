"""One place that knows which messages the bot owns, so it can clean them up."""

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)


async def track(state: FSMContext, message) -> None:
    """Remember a message the bot sent, so purge() can delete it later."""
    await track_ref(state, message.chat.id, message.message_id)


async def track_ref(state: FSMContext, chat_id: int, message_id: int) -> None:
    data = await state.get_data()
    sent = data.get("sent", [])
    sent.append({"chat_id": chat_id, "message_id": message_id})
    await state.update_data(sent=sent)


async def purge(state: FSMContext, bot) -> int:
    """Delete every tracked message and forget the tracking state.

    Missing messages are normal (the user may have deleted them), so they are
    logged at debug level; anything else is a warning, never a silent pass.
    """
    data = await state.get_data()
    sent = data.get("sent", [])
    deleted = 0

    for ref in sent:
        try:
            await bot.delete_message(chat_id=ref["chat_id"], message_id=ref["message_id"])
            deleted += 1
        except TelegramBadRequest as exc:
            logger.debug("message %s already gone: %s", ref.get("message_id"), exc)
        except Exception as exc:
            logger.warning("failed to delete message %s: %s", ref.get("message_id"), exc)

    await state.update_data(sent=[], prompt_refs=[], msg_refs=[], sticker_info=None)
    return deleted
