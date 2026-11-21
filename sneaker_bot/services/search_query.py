"""Turning the three FSM answers into one search query."""


def build_query(brand: str = "", model: str = "", size: str = "") -> str:
    """Join the non-empty parts of the guided search into a query string.

    "Посмотреть все" is stored as an empty model, and "нет" means the size does
    not matter, so both are skipped instead of being searched for.
    """
    parts = [brand.strip(), model.strip()]
    if size.strip() and size.strip().lower() not in {"нет", "no"}:
        parts.append(size.strip())
    return " ".join(part for part in parts if part)
