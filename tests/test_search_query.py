"""build_query turns the three FSM answers into a search string."""

import pytest

from sneaker_bot.services.search_query import build_query


@pytest.mark.parametrize(
    "brand, model, size, expected",
    [
        ("nike", "", "", "nike"),
        ("nike", "air max", "", "nike air max"),
        ("nike", "air max", "42", "nike air max 42"),
        ("nike", "", "42", "nike 42"),
        # "show everything" stores an empty model, "no" means size does not matter
        ("nike", "", "нет", "nike"),
        ("nike", "air max", "нет", "nike air max"),
        ("nike", "air max", "НЕТ", "nike air max"),
        ("  nike  ", "  air max  ", "  42  ", "nike air max 42"),
        ("", "", "", ""),
    ],
)
def test_build_query(brand, model, size, expected):
    assert build_query(brand, model, size) == expected
