"""The ten minute cache for search results."""

import pytest

from sneaker_bot.services import cache


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


OFFERS = [{"shop": "kufar.by", "title": "Nike", "price": "200 BYN", "url": "u"}]


def test_empty_cache_returns_none():
    assert cache.get("nike", now=0) is None


def test_put_then_get():
    cache.put("nike", OFFERS, now=100)
    assert cache.get("nike", now=101) == OFFERS


def test_missing_and_empty_queries_are_ignored():
    assert cache.get("adidas", now=100) is None


def test_query_normalisation():
    cache.put("Nike  Air   Max", OFFERS, now=100)
    assert cache.get("nike air max", now=101) is not None


def test_entry_expires_after_the_ttl():
    cache.put("nike", OFFERS, now=100)
    assert cache.get("nike", now=100 + cache.TTL_SECONDS + 1) is None


def test_returned_offers_are_copies():
    cache.put("nike", OFFERS, now=100)
    borrowed = cache.get("nike", now=101)
    borrowed[0]["price"] = "broken"
    assert cache.get("nike", now=102)[0]["price"] == "200 BYN"


def test_cache_is_bounded():
    for index in range(cache.MAX_ENTRIES + 10):
        cache.put(f"q{index}", OFFERS, now=100 + index)
    # Oldest entries are evicted, the newest survive.
    assert cache.get("q0", now=200) is None
    assert cache.get(f"q{cache.MAX_ENTRIES + 9}", now=200) is not None
