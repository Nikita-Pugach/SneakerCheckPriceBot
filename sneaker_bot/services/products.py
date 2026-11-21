"""Product identity: the same item shows up on several catalogue pages."""


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
