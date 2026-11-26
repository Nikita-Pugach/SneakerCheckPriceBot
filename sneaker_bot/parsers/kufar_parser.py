"""Kufar search through their public JSON API, no HTML parsing involved."""

import logging

import aiohttp

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.kufar.by/search-api/v2/search/rendered-paginated"
FOOTWEAR_HINTS = (
    "кроссовк",
    "кед",
    "обувь",
    "ботинк",
    "мокасин",
    "слипон",
    "сандал",
    "босонож",
)


def format_price(value) -> str:
    """Kufar reports prices in kopecks; 0 means the seller did not set one."""
    if not value:
        return ""
    try:
        number = float(value) / 100
    except (TypeError, ValueError):
        return ""
    if number <= 0:
        return ""
    if number.is_integer():
        return f"{int(number)} BYN"
    return f"{number:.2f} BYN"


def _condition_and_region(ad: dict) -> tuple[str, str]:
    """Kufar keeps everything in ad_parameters; condition and city are useful."""
    condition = ""
    region = ""
    for param in ad.get("ad_parameters") or []:
        key = str(param.get("p") or "").lower()
        value = param.get("vl")
        if not isinstance(value, str):
            continue
        if key == "condition" and not condition:
            condition = value
        elif key == "region" and not region:
            region = value
    return condition, region


def parse_ads(payload: dict, limit: int) -> list[dict]:
    """Turn an API response into offers: footwear, with a price."""
    items: list[dict] = []
    for ad in payload.get("ads", []):
        title = (ad.get("subject") or "").strip()
        url = (ad.get("ad_link") or "").strip()
        price = format_price(ad.get("price_byn"))
        if not title or not url or not price:
            continue
        if not any(hint in title.lower() for hint in FOOTWEAR_HINTS):
            continue
        condition, region = _condition_and_region(ad)
        items.append(
            {
                "title": title,
                "price": price,
                "url": url,
                "condition": condition,
                "region": region,
            }
        )
        if len(items) >= limit:
            break
    return items


async def search(
    session: aiohttp.ClientSession, query: str, limit: int = 5
) -> list[dict]:
    params = {"query": query or "", "size": max(limit * 4, 20)}
    try:
        async with session.get(SEARCH_URL, params=params, timeout=20) as response:
            if response.status != 200:
                logger.warning("kufar returned HTTP %s", response.status)
                return []
            payload = await response.json(content_type=None)
    except Exception as exc:
        logger.warning("kufar search failed: %s", exc)
        return []

    return parse_ads(payload, limit)
