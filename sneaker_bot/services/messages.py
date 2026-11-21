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
    # Older versions stored refs under separate keys; a chat that lived through
    # them still has leftovers, so clean everything we know about.
    refs = list(data.get("sent", []))
    refs += data.get("msg_refs", [])
    refs += data.get("prompt_refs", [])
    if data.get("sticker_info"):
        refs.append(data["sticker_info"])

    deleted = 0
    seen: set[tuple[int, int]] = set()

    for ref in refs:
        key = (ref.get("chat_id"), ref.get("message_id"))
        if key in seen or key[0] is None or key[1] is None:
            continue
        seen.add(key)
        try:
            await bot.delete_message(chat_id=key[0], message_id=key[1])
            deleted += 1
        except TelegramBadRequest as exc:
            logger.debug("message %s already gone: %s", key[1], exc)
        except Exception as exc:
            logger.warning("failed to delete message %s: %s", key[1], exc)

    await state.update_data(sent=[], prompt_refs=[], msg_refs=[], sticker_info=None)
    return deleted
