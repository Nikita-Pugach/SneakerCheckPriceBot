"""Duplicate detection and the slug heuristic."""

import pytest

from sneaker_bot.parsers.price_parser import looks_like_slug
from sneaker_bot.services.products import is_new, product_keys


def test_product_keys_are_normalised():
    assert product_keys("  Рюкзак   Nike ", "https://bunt.by/p/1/?utm=1") == (
        "https://bunt.by/p/1",
        "рюкзак nike",
    )


def test_same_url_is_a_duplicate():
    seen = set()
    assert is_new(seen, "Рюкзак Nike", "https://bunt.by/p/1")
    # tracking parameters and a different title must not create a second entry
    assert not is_new(seen, "Рюкзак Nike (копия)", "https://bunt.by/p/1?utm=2")


def test_same_title_is_a_duplicate():
    seen = set()
    assert is_new(seen, "Рюкзак Nike", "https://bunt.by/p/1")
    assert not is_new(seen, "рюкзак   nike", "https://bunt.by/p/2")


def test_different_products_both_pass():
    seen = set()
    assert is_new(seen, "Nike Air Max", "https://bunt.by/p/1")
    assert is_new(seen, "Nike Vomero", "https://bunt.by/p/2")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("nike-brasilia-9-5-training-big-backpack-dm3975-010", True),
        ("Рюкзак Nike Brasilia 9.5 Big Backpack", False),
        ("Nike", False),
        ("42", False),
        ("", False),
    ],
)
def test_looks_like_slug(text, expected):
    assert looks_like_slug(text) is expected
