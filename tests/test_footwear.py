"""The bot searches sneakers, not backpacks."""

import pytest

from sneaker_bot.services.products import is_footwear


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Кроссовки Nike Zoom Vomero Roam FV2295-201", True),
        ("Nike Air Max 90", True),
        ("Nike Brasilia 9.5", True),
        ("Adidas Superstar", True),
        ("Рюкзак Nike Brasilia 9.5 Big Backpack", False),
        ("Nike Heritage Eugene Backpack", False),
        ("Nike Club Cap", False),
        ("Носки Nike Everyday", False),
        ("Nike Dri-FIT Shorts", False),
        ("Кепка Nike Heritage86", False),
        ("Сумка Nike Brasilia", False),
        ("Nike T-Shirt", False),
    ],
)
def test_is_footwear(title, expected):
    assert is_footwear(title) is expected
