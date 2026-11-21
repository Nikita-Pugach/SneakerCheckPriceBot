# handlers/back_head_menu_button.py
import logging

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from sneaker_bot.services.send_head_menu import send_head_menu
from sneaker_bot.services.messages import purge

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(lambda c: c.data == "back_main")
async def back_head_menu_button(query: CallbackQuery, state):
    try:
        await query.answer(cache_time=2)
    except TelegramBadRequest:
        pass

    try:
        await purge(state, query.bot)
    except Exception as exc:
        logger.warning("purge failed: %s", exc)

    sent = await send_head_menu(
        query,
        state,
        text="📩Выберите дальнейшее действие:📩"
    )

    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass

    try:
        await state.update_data(menu_msg_id=sent.message_id)
    except Exception:
        pass
