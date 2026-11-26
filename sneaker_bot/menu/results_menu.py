"""Keyboard under the search results: price cap, condition, history, more."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PRICE_CAPS = [200, 300, 500]

# How many offers one screen shows before "show more".
PAGE_SIZE = 6

CONDITION_LABELS = {"new": "🆕 Новые", "used": "👟 Б/у", "any": "Любое"}


def _mark(text: str, active: bool) -> str:
    return f"✅ {text}" if active else text


def results_menu(
    max_price: float | None = None,
    condition: str | None = None,
    has_more: bool = False,
) -> InlineKeyboardMarkup:
    """Price row, condition row, the "more" row when needed, then navigation."""
    price_row = [
        InlineKeyboardButton(
            text=_mark(f"до {cap}", max_price == cap),
            callback_data=f"flt:price:{cap}",
        )
        for cap in PRICE_CAPS
    ]
    price_row.append(
        InlineKeyboardButton(
            text=_mark("Любая", max_price is None),
            callback_data="flt:price:0",
        )
    )

    condition_row = [
        InlineKeyboardButton(
            text=_mark(CONDITION_LABELS["new"], condition == "new"),
            callback_data="flt:cond:new",
        ),
        InlineKeyboardButton(
            text=_mark(CONDITION_LABELS["used"], condition == "used"),
            callback_data="flt:cond:used",
        ),
        InlineKeyboardButton(
            text=_mark(CONDITION_LABELS["any"], condition is None),
            callback_data="flt:cond:any",
        ),
    ]

    rows = [price_row, condition_row]
    if has_more:
        rows.append(
            [InlineKeyboardButton(text="⬇️ Показать ещё", callback_data="flt:more")]
        )
    rows.append(
        [
            InlineKeyboardButton(text="🕓 История", callback_data="history_button"),
            InlineKeyboardButton(text="🏠 В меню", callback_data="back_main"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
