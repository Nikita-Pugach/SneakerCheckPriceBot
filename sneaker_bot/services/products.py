"""Product identity and relevance: what counts as the same item, what is a shoe."""

import re

# Accessories come back with almost any brand query; the bot is called Sneaker.
_LATIN_NOT_FOOTWEAR = re.compile(
    r"\b(backpack|bag|cap|hat|socks|shorts|jacket|hoodie|t-shirt|tee|ball|bottle)\b",
    re.IGNORECASE,
)
_CYRILLIC_NOT_FOOTWEAR = (
    "рюкзак",
    "сумк",
    "кепк",
    "бейсболк",
    "шапк",
    "носк",
    "шорт",
    "куртк",
    "кофт",
    "худи",
    "футболк",
    "мяч",
    "бутылк",
    "термос",
)


def is_footwear(title: str) -> bool:
    """False for backpacks, bags, caps and other accessories."""
    if _LATIN_NOT_FOOTWEAR.search(title):
        return False
    lowered = title.lower()
    return not any(word in lowered for word in _CYRILLIC_NOT_FOOTWEAR)


def product_keys(title: str, url: str) -> tuple[str, str]:
    """Normalised keys used to spot repeats of the same product."""
    clean_url = url.split("?")[0].rstrip("/").lower()
    clean_title = " ".join(title.lower().split())
    return clean_url, clean_title


def is_new(seen: set[str], title: str, url: str) -> bool:
    """Remember the product and report whether it had not been seen before."""
    url_key, title_key = product_keys(title, url)
    if url_key in seen or title_key in seen:
        return False
    seen.add(url_key)
    seen.add(title_key)
    return True
