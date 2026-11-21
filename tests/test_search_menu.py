"""Inline keyboards: brands, models, sizes."""

from sneaker_bot.menu.search_menu import (
    CALLBACK_ALL,
    CALLBACK_CUSTOM_MODEL,
    CALLBACK_SKIP_SIZE,
    POPULAR_BRANDS,
    SHOE_SIZES,
    brands_keyboard,
    models_keyboard,
    sizes_keyboard,
)


def callbacks(keyboard) -> list[str]:
    return [button.callback_data for row in keyboard.inline_keyboard for button in row]


def test_brand_buttons_one_per_brand():
    data = callbacks(brands_keyboard())
    assert len(data) == len(POPULAR_BRANDS)
    assert "brand:nike" in data
    assert "brand:new balance" in data


def test_known_brand_offers_models_and_shortcuts():
    data = callbacks(models_keyboard("Nike"))
    assert "model:air max" in data
    assert "model:air force 1" in data
    assert CALLBACK_ALL in data
    assert CALLBACK_CUSTOM_MODEL in data


def test_unknown_brand_falls_back_to_shortcuts():
    assert callbacks(models_keyboard("Zzz")) == [CALLBACK_ALL, CALLBACK_CUSTOM_MODEL]


def test_size_keyboard_has_sizes_and_skip():
    data = callbacks(sizes_keyboard())
    assert f"size:{SHOE_SIZES[0]}" in data
    assert f"size:{SHOE_SIZES[-1]}" in data
    assert CALLBACK_SKIP_SIZE in data
