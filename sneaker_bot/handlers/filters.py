"""Filter buttons under the results: price cap, new/used, and "show more"."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from sneaker_bot.menu.results_menu import PAGE_SIZE, results_menu
from sneaker_bot.services.offers import Offer, apply_filters, render
from sneaker_bot.sub_checker import is_sub

router = Router()
logger = logging.getLogger(__name__)

MAX_MESSAGE = 3900


def _trim(text: str) -> str:
    """Telegram rejects anything over 4096 characters; keep a safe margin."""
    return text if len(text) <= MAX_MESSAGE else text[: MAX_MESSAGE - 1] + "…"


def _visible_state(results: dict) -> tuple[float | None, str | None, int]:
    max_price = results.get("max_price")
    condition = results.get("condition")
    shown = results.get("shown") or PAGE_SIZE
    return max_price, condition, shown


async def _rerender(
    query: CallbackQuery,
    state: FSMContext,
    max_price: float | None,
    condition: str | None,
    shown: int,
) -> None:
    data = await state.get_data()
    results = data.get("results") or {}
    offers = [Offer.from_dict(item) for item in results.get("offers", [])]

    total = len(apply_filters(offers, max_price=max_price, condition=condition))
    text = render(
        offers,
        max_price=max_price,
        condition=condition,
        previous_min=results.get("previous_min"),
        limit=shown,
    )
    keyboard = results_menu(
        max_price=max_price,
        condition=condition,
        has_more=shown < total,
    )

    try:
        await query.message.edit_text(
            _trim(text), reply_markup=keyboard, disable_web_page_preview=True
        )
    except TelegramBadRequest as exc:
        # Usually "message is not modified" when the same filter is pressed twice.
        logger.debug("could not edit the results message: %s", exc)

    results.update(max_price=max_price, condition=condition, shown=shown)
    await state.update_data(results=results)


@router.callback_query(F.data.startswith("flt:"))
@is_sub
async def filter_results(query: CallbackQuery, state: FSMContext) -> None:
    parts = (query.data or "").split(":")
    if len(parts) < 2:
        await query.answer()
        return

    kind = parts[1]
    value = parts[2] if len(parts) > 2 else ""

    data = await state.get_data()
    results = data.get("results") or {}
    if not results:
        await query.answer("Сначала запустите поиск", show_alert=True)
        return

    max_price, condition, shown = _visible_state(results)

    if kind == "price":
        try:
            max_price = None if value == "0" else float(value)
        except ValueError:
            await query.answer()
            return
        shown = PAGE_SIZE
    elif kind == "cond":
        condition = None if value == "any" else value
        shown = PAGE_SIZE
    elif kind == "reset":
        max_price, condition, shown = None, None, PAGE_SIZE
    elif kind == "more":
        shown += PAGE_SIZE
    else:
        await query.answer()
        return

    await query.answer()
    await _rerender(query, state, max_price, condition, shown)
