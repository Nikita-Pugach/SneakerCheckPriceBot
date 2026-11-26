"""Search history: the last queries as buttons, plus replay and clearing."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from sneaker_bot.handlers.know_button import launch_search
from sneaker_bot.menu.back_menu import back_menu
from sneaker_bot.services import cooldown, history
from sneaker_bot.services.send_messages import record_and_send
from sneaker_bot.sub_checker import is_sub

router = Router()
logger = logging.getLogger(__name__)

HISTORY_LIMIT = 8


def _keyboard(entries: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=history.label(entry), callback_data=f"hist:run:{entry['id']}"
            )
        ]
        for entry in entries
    ]
    rows.append(
        [InlineKeyboardButton(text="🗑 Очистить историю", callback_data="hist:clear")]
    )
    rows.append([InlineKeyboardButton(text="🏠 В меню", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "history_button")
@is_sub
async def show_history(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    user_id = query.from_user.id
    try:
        entries = history.recent(user_id, limit=HISTORY_LIMIT)
    except Exception as exc:  # a broken database must not break the menu
        logger.warning("could not read the history: %s", exc)
        entries = []

    if not entries:
        await record_and_send(
            query,
            state,
            text="🕓 История пуста. Запустите первый поиск.",
            reply_markup=back_menu,
        )
    else:
        await record_and_send(
            query,
            state,
            text="🕓 <b>Последние поиски</b>\nНажмите на запись, чтобы повторить её.",
            reply_markup=_keyboard(entries),
        )

    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("hist:"))
@is_sub
async def history_action(query: CallbackQuery, state: FSMContext) -> None:
    parts = (query.data or "").split(":")
    action = parts[1] if len(parts) > 1 else ""
    user_id = query.from_user.id

    if action == "clear":
        try:
            removed = history.clear(user_id)
        except Exception as exc:
            logger.warning("could not clear the history: %s", exc)
            removed = 0
        await query.answer(f"Удалено записей: {removed}")
        try:
            await query.message.edit_text("🕓 История очищена.", reply_markup=back_menu)
        except TelegramBadRequest:
            pass
        return

    if action != "run" or len(parts) != 3:
        await query.answer()
        return

    try:
        entry = history.by_id(int(parts[2]))
    except Exception as exc:
        logger.warning("could not read history entry %s: %s", parts[2], exc)
        entry = None

    if not entry or entry.get("user_id") != user_id:
        await query.answer("Запись не найдена", show_alert=True)
        return

    left = cooldown.remaining(user_id)
    if left:
        await query.answer(f"Подождите {left} с", show_alert=True)
        return

    await query.answer()
    await state.clear()
    launch_search(query, state, user_id, entry["query"])
