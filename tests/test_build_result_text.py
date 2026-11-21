"""build_result_text renders the Telegram message for a price search."""

from sneaker_bot.services.build_text_parser_price import build_result_text

EMPTY_BUNT = {"muzhskie": [], "zhenskie": []}
EMPTY_SNEAKERS = {"мужские": [], "женские": []}
NOT_FOUND = "Товар не найден ни в одном магазине."


def test_nothing_found():
    assert build_result_text(EMPTY_BUNT, EMPTY_SNEAKERS) == NOT_FOUND


def test_single_item_is_rendered_with_price_and_link():
    bunt = {"muzhskie": [("Nike Air Max", "2999 BYN", "https://bunt.by/nike")], "zhenskie": []}
    text = build_result_text(bunt, EMPTY_SNEAKERS)

    assert "<b>Магазин:</b> bunt.by" in text
    assert "<b>Мужские</b>" in text
    assert "1. Nike Air Max" in text
    assert "Цена: <code>2999 BYN</code>" in text
    assert 'href="https://bunt.by/nike"' in text
    # the other shop and the other gender must not appear out of nowhere
    assert "sneakers.by" not in text
    assert "Женские" not in text


def test_items_are_numbered_per_category():
    bunt = {
        "muzhskie": [("first", "100 BYN", "u1"), ("second", "200 BYN", "u2")],
        "zhenskie": [],
    }
    text = build_result_text(bunt, EMPTY_SNEAKERS)
    assert "1. first" in text
    assert "2. second" in text


def test_items_without_a_price_are_dropped():
    bunt = {
        "muzhskie": [("Nike", "—", "u1"), ("Adidas", "–", "u2"), ("Puma", "ошибка", "u3")],
        "zhenskie": [],
    }
    assert build_result_text(bunt, EMPTY_SNEAKERS) == NOT_FOUND


def test_both_shops_can_appear():
    bunt = {"muzhskie": [("Nike", "100 BYN", "u1")], "zhenskie": []}
    sneakers = {"мужские": [("Adidas", "200 BYN", "u2")], "женские": []}
    text = build_result_text(bunt, sneakers)
    assert "<b>Магазин:</b> bunt.by" in text
    assert "<b>Магазин:</b> sneakers.by" in text
