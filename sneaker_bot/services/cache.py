"""A small in-memory cache for search results, so repeat queries are free."""

import time

TTL_SECONDS = 600
MAX_ENTRIES = 64

_store: dict[str, tuple[float, list[dict]]] = {}


def _key(query: str) -> str:
    return " ".join((query or "").lower().split())


def _purge(now: float) -> None:
    stale = [key for key, (stamp, _) in _store.items() if now - stamp > TTL_SECONDS]
    for key in stale:
        _store.pop(key, None)
    while len(_store) > MAX_ENTRIES:
        oldest = min(_store.items(), key=lambda item: item[1][0])[0]
        _store.pop(oldest, None)


def get(query: str, now: float | None = None) -> list[dict] | None:
    """Fresh offers for this query, or None when the cache has nothing usable."""
    current = time.monotonic() if now is None else now
    _purge(current)
    entry = _store.get(_key(query))
    if not entry:
        return None
    stamp, offers = entry
    if current - stamp > TTL_SECONDS:
        _store.pop(_key(query), None)
        return None
    return [dict(offer) for offer in offers]


def put(query: str, offers: list[dict], now: float | None = None) -> None:
    current = time.monotonic() if now is None else now
    _store[_key(query)] = (current, [dict(offer) for offer in offers])
    _purge(current)


def clear() -> None:
    """Drop everything; tests use this between cases."""
    _store.clear()
