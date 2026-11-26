"""A per-user pause between searches, so one person cannot hammer the shops."""

import math
import time

DEFAULT_SECONDS = 15

_last_search: dict[int, float] = {}


def remaining(user_id: int, seconds: int = DEFAULT_SECONDS, now: float | None = None) -> int:
    """Whole seconds left before this user may search again; 0 means allowed."""
    current = time.monotonic() if now is None else now
    last = _last_search.get(user_id)
    if last is None:
        return 0
    left = seconds - (current - last)
    if left <= 0:
        return 0
    return math.ceil(left)


def mark(user_id: int, now: float | None = None) -> None:
    """Remember that the user started a search right now."""
    _last_search[user_id] = time.monotonic() if now is None else now


def reset() -> None:
    """Clear the state; used by tests to start from a clean slate."""
    _last_search.clear()
