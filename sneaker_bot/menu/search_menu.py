"""Inline keyboards for the guided search: brands, models, sizes."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

POPULAR_BRANDS = ["Nike", "Adidas", "Puma", "New Balance", "Reebok", "Asics"]

POPULAR_MODELS = {
    "nike": ["Air Max", "Air Force 1", "Dunk", "Pegasus", "Vomero"],
    "adidas": ["Superstar", "Stan Smith", "Ultraboost", "Gazelle", "Samba"],
    "puma": ["Suede", "Roma", "Clyde", "RS-X"],
    "new balance": ["574", "990", "530", "2002R"],
    "reebok": ["Club C", "Classic Leather", "Nano"],
    "asics": ["Gel-Kayano", "Gel-Nimbus", "Japan S"],
}

SHOE_SIZES = [39, 40, 41, 42, 43, 44, 45, 46]

CALLBACK_ALL = "model:__all__"
CALLBACK_SKIP_SIZE = "size:__skip__"
CALLBACK_CUSTOM_MODEL = "model:__custom__"

ALL_VALUE = "__all__"
SKIP_SIZE_VALUE = "__skip__"
CUSTOM_MODEL_VALUE = "__custom__"


def _rows(buttons: list[InlineKeyboardButton], per_row: int) -> list[list[InlineKeyboardButton]]:
    return [buttons[i : i + per_row] for i in range(0, len(buttons), per_row)]


def brands_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=brand, callback_data=f"brand:{brand.lower()}")
        for brand in POPULAR_BRANDS
    ]
    return InlineKeyboardMarkup(inline_keyboard=_rows(buttons, 2))


def models_keyboard(brand: str) -> InlineKeyboardMarkup:
    """Popular models for a brand, or just the shortcuts when the brand is unknown."""
    models = POPULAR_MODELS.get(brand.strip().lower(), [])
    buttons = [
        InlineKeyboardButton(text=model, callback_data=f"model:{model.lower()}")
        for model in models
    ]
    rows = _rows(buttons, 2)
    rows.append(
        [
            InlineKeyboardButton(text="Посмотреть все", callback_data=CALLBACK_ALL),
            InlineKeyboardButton(text="✍️ Своя модель", callback_data=CALLBACK_CUSTOM_MODEL),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sizes_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=str(size), callback_data=f"size:{size}")
        for size in SHOE_SIZES
    ]
    rows = _rows(buttons, 4)
    rows.append(
        [InlineKeyboardButton(text="Не важно", callback_data=CALLBACK_SKIP_SIZE)]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
