"""Filter buttons under the results: price cap and new/used."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from sneaker_bot.menu.results_menu import results_menu
from sneaker_bot.services.offers import Offer, render
from sneaker_bot.sub_checker import is_sub

router = Router()
logger = logging.getLogger(__name__)


async def _rerender(query: CallbackQuery, state: FSMContext, max_price, condition) -> None:
    data = await state.get_data()
    results = data.get("results") or {}
    offers = [Offer.from_dict(item) for item in results.get("offers", [])]

    text = render(
        offers,
        max_price=max_price,
        condition=condition,
        previous_min=results.get("previous_min"),
    )
    keyboard = results_menu(max_price=max_price, condition=condition)

    try:
        await query.message.edit_text(
            text, reply_markup=keyboard, disable_web_page_preview=True
        )
    except TelegramBadRequest as exc:
        # Usually "message is not modified" when the same filter is pressed twice.
        logger.debug("could not edit the results message: %s", exc)

    results["max_price"] = max_price
    results["condition"] = condition
    await state.update_data(results=results)


@router.callback_query(F.data.startswith("flt:"))
@is_sub
async def filter_results(query: CallbackQuery, state: FSMContext) -> None:
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        await query.answer()
        return

    kind, value = parts[1], parts[2]
    data = await state.get_data()
    results = data.get("results") or {}
    if not results:
        await query.answer("Сначала запустите поиск", show_alert=True)
        return

    max_price = results.get("max_price")
    condition = results.get("condition")

    if kind == "price":
        max_price = None if value == "0" else float(value)
    elif kind == "cond":
        condition = None if value == "any" else value
    elif kind == "reset":
        max_price, condition = None, None

    await query.answer()
    await _rerender(query, state, max_price, condition)
