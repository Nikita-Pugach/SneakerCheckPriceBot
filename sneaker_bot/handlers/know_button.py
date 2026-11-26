import asyncio
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from sneaker_bot.menu.back_menu import back_menu
from sneaker_bot.menu.search_menu import (
    ALL_VALUE,
    CUSTOM_MODEL_VALUE,
    SKIP_SIZE_VALUE,
    brands_keyboard,
    models_keyboard,
    sizes_keyboard,
)
from sneaker_bot.services import cooldown
from sneaker_bot.services.price_search import process_price_search
from sneaker_bot.services.search_query import build_query
from sneaker_bot.services.send_messages import send_prompt
from sneaker_bot.services.utils import delete_last_prompt_on_reply
from sneaker_bot.sub_checker import is_sub
from sneaker_bot.tasks import tasks

router = Router()
logger = logging.getLogger(__name__)

SEARCH_TIMEOUT = 150


class KnowPriceSG(StatesGroup):
    waiting_for_brand = State()
    waiting_for_model = State()
    waiting_for_size = State()


def _chat_id(ctx) -> int:
    return ctx.message.chat.id if isinstance(ctx, CallbackQuery) else ctx.chat.id


def _message_of(ctx) -> Message:
    return ctx.message if isinstance(ctx, CallbackQuery) else ctx


async def _notify(ctx, text: str) -> None:
    try:
        await _message_of(ctx).answer(text)
    except TelegramBadRequest:
        pass


async def _ack(query: CallbackQuery) -> None:
    try:
        await query.answer()
    except TelegramBadRequest:
        pass


async def _ask_model(ctx, state: FSMContext, brand: str) -> None:
    await delete_last_prompt_on_reply(state, ctx.bot, _chat_id(ctx))
    await state.update_data(brand=brand.strip().lower())
    await state.set_state(KnowPriceSG.waiting_for_model)
    await send_prompt(
        ctx,
        state,
        text=(
            "Выберите модель кнопками ниже или напишите её сами.\n"
            "«Посмотреть все» покажет весь бренд."
        ),
        reply_markup=models_keyboard(brand),
    )


async def _ask_size(ctx, state: FSMContext) -> None:
    await delete_last_prompt_on_reply(state, ctx.bot, _chat_id(ctx))
    await state.set_state(KnowPriceSG.waiting_for_size)
    await send_prompt(
        ctx,
        state,
        text="Выберите размер кнопками или напишите его. «Не важно» — без размера.",
        reply_markup=sizes_keyboard(),
    )


async def _start_search(ctx, state: FSMContext, user_id: int) -> None:
    data = await state.get_data()
    query = build_query(
        data.get("brand", ""), data.get("model", ""), data.get("size", "")
    )

    left = cooldown.remaining(user_id)
    if left:
        await _notify(
            ctx,
            f"⏳ Не так быстро: следующий поиск можно запустить через {left} с.",
        )
        return

    await delete_last_prompt_on_reply(state, ctx.bot, _chat_id(ctx))
    await state.clear()
    launch_search(ctx, state, user_id, query)


def launch_search(ctx, state: FSMContext, user_id: int, query: str) -> None:
    """Cancel the previous search and start a new one.

    The cooldown is marked here, so every entry point (guided search, history
    replay) is throttled by the same clock.
    """
    cooldown.mark(user_id)

    if previous := tasks.get(user_id):
        previous.cancel()

    async def run_search() -> None:
        # A task created with create_task keeps its exception in the event loop,
        # which used to leave the user staring at the "searching" message.
        try:
            await asyncio.wait_for(
                process_price_search(user_id, ctx, state, query), timeout=SEARCH_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning("price search timed out for user %s", user_id)
            await _notify(ctx, "Поиск занял слишком много времени. Попробуйте ещё раз.")
        except Exception:
            logger.exception("price search crashed for user %s", user_id)
            await _notify(ctx, "Не удалось выполнить поиск. Попробуйте позже.")

    tasks[user_id] = asyncio.create_task(run_search())


# ------------------------------------------------------------------ entry point
@router.callback_query(lambda c: c.data == "know_button")
@is_sub
async def search_know_button(query: CallbackQuery, state: FSMContext):
    try:
        await query.answer(cache_time=2)
    except TelegramBadRequest:
        pass

    user_id = query.from_user.id
    if previous := tasks.get(user_id):
        previous.cancel()

    await state.clear()
    await state.set_state(KnowPriceSG.waiting_for_brand)

    await send_prompt(
        query,
        state,
        text="Выберите бренд кнопками ниже или напишите свой:",
        reply_markup=brands_keyboard(),
    )

    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass


# ------------------------------------------------------------------------ brand
@router.callback_query(KnowPriceSG.waiting_for_brand, F.data.startswith("brand:"))
@is_sub
async def brand_button(query: CallbackQuery, state: FSMContext):
    await _ack(query)
    await _ask_model(query, state, query.data.split(":", 1)[1])


@router.message(KnowPriceSG.waiting_for_brand)
@is_sub
async def brand_text(message: Message, state: FSMContext):
    brand = (message.text or "").strip()
    if not brand:
        return
    await _ask_model(message, state, brand)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


# ------------------------------------------------------------------------ model
@router.callback_query(KnowPriceSG.waiting_for_model, F.data.startswith("model:"))
@is_sub
async def model_button(query: CallbackQuery, state: FSMContext):
    await _ack(query)
    value = query.data.split(":", 1)[1]

    if value == CUSTOM_MODEL_VALUE:
        await delete_last_prompt_on_reply(state, query.bot, _chat_id(query))
        await send_prompt(
            query, state, text="Напишите модель кроссовок:", reply_markup=back_menu
        )
        return

    await state.update_data(model="" if value == ALL_VALUE else value)
    await _ask_size(query, state)


@router.message(KnowPriceSG.waiting_for_model)
@is_sub
async def model_text(message: Message, state: FSMContext):
    model = (message.text or "").strip().lower()
    if not model:
        return
    await state.update_data(model="" if model == "посмотреть все" else model)
    await _ask_size(message, state)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


# ------------------------------------------------------------------------- size
@router.callback_query(KnowPriceSG.waiting_for_size, F.data.startswith("size:"))
@is_sub
async def size_button(query: CallbackQuery, state: FSMContext):
    await _ack(query)
    value = query.data.split(":", 1)[1]
    await state.update_data(size="нет" if value == SKIP_SIZE_VALUE else value)
    await _start_search(query, state, query.from_user.id)


@router.message(KnowPriceSG.waiting_for_size)
@is_sub
async def size_text(message: Message, state: FSMContext):
    size = (message.text or "").strip().lower()
    if not size:
        return
    await state.update_data(size=size)
    await _start_search(message, state, message.from_user.id)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
