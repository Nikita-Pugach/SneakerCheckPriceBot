"""Price parsing helpers shared by the result formatter and the summary."""

import re

_NUMBER = re.compile(r"(\d[\d\s\u00a0]*)(?:[.,](\d{1,2}))?")


def parse_price(price: str) -> float | None:
    """Return the numeric value of a price string, or None when it has none.

    Handles "2999 BYN", "1 234,50 BYN" and the "—"/"ошибка" placeholders the
    parsers use for a missing price.
    """
    if not price:
        return None
    match = _NUMBER.search(price)
    if not match:
        return None
    whole = re.sub(r"\D", "", match.group(1))
    if not whole:
        return None
    fraction = match.group(2) or "0"
    try:
        return float(f"{whole}.{fraction}")
    except ValueError:  # pragma: no cover - guarded by the regex
        return None


def format_amount(value: float) -> str:
    """Render a number the way the shops do: no trailing .0, space thousands."""
    if float(value).is_integer():
        number = f"{int(value):,}".replace(",", " ")
    else:
        number = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{number} BYN"


def plural(count: int, one: str, few: str, many: str) -> str:
    """Russian plural form for a count."""
    if count % 10 == 1 and count % 100 != 11:
        return one
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return few
    return many
