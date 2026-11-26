"""Search history stored in SQLite."""

import sqlite3

import pytest

from sneaker_bot.services import history


@pytest.fixture()
def db(tmp_path):
    path = str(tmp_path / "test.db")
    history.init(path)
    return path


def test_empty_history(db):
    assert history.recent(1, path=db) == []


def test_saved_search_appears_newest_first(db):
    history.save_search(1, "nike air max", found=3, min_price=210, path=db)
    history.save_search(1, "adidas samba", found=2, min_price=180, path=db)

    entries = history.recent(1, path=db)
    assert [entry["query"] for entry in entries] == ["adidas samba", "nike air max"]
    assert entries[0]["found"] == 2
    assert entries[0]["min_price"] == 180


def test_history_is_per_user(db):
    history.save_search(1, "nike", path=db)
    history.save_search(2, "adidas", path=db)

    assert len(history.recent(1, path=db)) == 1
    assert history.recent(2, path=db)[0]["query"] == "adidas"


def test_limit_is_respected(db):
    for index in range(12):
        history.save_search(1, f"query {index}", path=db)

    assert len(history.recent(1, limit=8, path=db)) == 8


def test_previous_min_returns_the_last_known_price(db):
    history.save_search(1, "nike", found=4, min_price=300, path=db)
    history.save_search(1, "nike", found=3, min_price=250, path=db)

    assert history.previous_min(1, "nike", path=db) == 250


def test_previous_min_ignores_other_queries_and_users(db):
    history.save_search(1, "nike", min_price=300, path=db)
    history.save_search(2, "nike", min_price=100, path=db)

    assert history.previous_min(1, "adidas", path=db) is None
    assert history.previous_min(1, "nike", path=db) == 300


def test_searches_without_prices_do_not_break_previous_min(db):
    history.save_search(1, "nike", found=0, min_price=None, path=db)
    assert history.previous_min(1, "nike", path=db) is None


def test_clear_removes_only_this_user(db):
    history.save_search(1, "nike", path=db)
    history.save_search(2, "nike", path=db)

    assert history.clear(1, path=db) == 1
    assert history.recent(1, path=db) == []
    assert len(history.recent(2, path=db)) == 1


def test_by_id_returns_the_entry(db):
    search_id = history.save_search(1, "nike air max", found=5, min_price=210, path=db)
    entry = history.by_id(search_id, path=db)
    assert entry["query"] == "nike air max"
    assert entry["user_id"] == 1


def test_by_id_of_a_missing_entry(  db):
    assert history.by_id(999, path=db) is None


def test_label_contains_date_query_and_price(db):
    history.save_search(1, "nike air max", found=6, min_price=210, path=db)
    entry = history.recent(1, path=db)[0]
    text = history.label(entry)

    assert "nike air max" in text
    assert "6 шт" in text
    assert "от 210 BYN" in text


def test_label_for_an_empty_search(db):
    history.save_search(1, "zzz", found=0, min_price=None, path=db)
    text = history.label(history.recent(1, path=db)[0])

    assert "ничего не найдено" in text
