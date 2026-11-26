"""Typed queries: "nike air max 42" becomes a one-tap search."""

import logging
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from sneaker_bot.handlers.know_button import launch_search
from sneaker_bot.services import cooldown
from sneaker_bot.services.utils import delete_last_prompt_on_reply
from sneaker_bot.services.send_messages import send_prompt
from sneaker_bot.services.text_query import clean_query
from sneaker_bot.sub_checker import is_sub

router = Router()
logger = logging.getLogger(__name__)


def ask_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Найти", callback_data="ask:go"),
                InlineKeyboardButton(text="🎛 Кнопками", callback_data="ask:menu"),
            ]
        ]
    )


@router.message(F.text)
async def suggest_search(message: Message, state: FSMContext) -> None:
    """Offer to search for what the user typed instead of silently deleting it."""
    query = clean_query(message.text)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if query is None:
        return

    await state.update_data(pending_query=query)
    await send_prompt(
        message,
        state,
        text=f"🔍 Искать «{escape(query)}»?",
        reply_markup=ask_keyboard(),
    )


@router.callback_query(F.data == "ask:go")
@is_sub
async def run_typed_query(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    text = (data.get("pending_query") or "").strip()
    if not text:
        await query.answer("Запрос потерялся, напишите его ещё раз", show_alert=True)
        return

    left = cooldown.remaining(query.from_user.id)
    if left:
        await query.answer(f"Подождите {left} с", show_alert=True)
        return

    await query.answer()
    await delete_last_prompt_on_reply(state, query.bot, query.message.chat.id)
    await state.update_data(pending_query=None)
    launch_search(query, state, query.from_user.id, text)


@router.callback_query(F.data == "ask:menu")
@is_sub
async def choose_buttons(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.update_data(pending_query=None)
    await delete_last_prompt_on_reply(state, query.bot, query.message.chat.id)

    # Reuse the guided flow: it sets the state and sends the brand keyboard.
    from sneaker_bot.menu.search_menu import brands_keyboard
    from sneaker_bot.handlers.know_button import KnowPriceSG

    await state.set_state(KnowPriceSG.waiting_for_brand)
    await send_prompt(
        query,
        state,
        text="Выберите бренд кнопками ниже или напишите свой:",
        reply_markup=brands_keyboard(),
    )
