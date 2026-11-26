"""Turning a free-form message into a search query."""

MIN_LENGTH = 3
MAX_LENGTH = 60


def clean_query(text: str | None) -> str | None:
    """Normalise a typed message, or return None when it is not a query.

    Commands ("/start") and one-letter noise are ignored: the caller deletes
    the message either way, it just does not suggest a search.
    """
    if not text:
        return None
    collapsed = " ".join(text.split())
    if not collapsed or collapsed.startswith("/"):
        return None
    if not MIN_LENGTH <= len(collapsed) <= MAX_LENGTH:
        return None
    return collapsed
