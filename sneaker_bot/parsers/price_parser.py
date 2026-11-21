"""Scraping for the price search: configuration, price extraction, card parsing.

The scenario that uses these functions lives in `services/price_search.py`; this
module only knows how to read a page.
"""

import os
import re
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HEADERS = {"User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0")}
PER_CAT = int(os.getenv("PER_CAT", 5))
BASE = os.getenv("BASE_URL", "")
CATALOGS = [
    urljoin(BASE, os.getenv("CATALOG_MEN_PATH") or ""),
    urljoin(BASE, os.getenv("CATALOG_WOMEN_PATH") or ""),
]
SNEAKERS = {
    "женские": os.getenv("SNEAKERS_WOMEN_URL") or "",
    "мужские": os.getenv("SNEAKERS_MEN_URL") or "",
}
MAX_PAGES_BUNT = int(os.getenv("MAX_PAGES_BUNT", 1))
MAX_PAGES_SNEAK = int(os.getenv("MAX_PAGES_SNEAK", 1))

SUCCESS_STICKERS = [
    "CAACAgIAAxkBAAEQAAE2aT7hurip0DwMapzkZIF1TGG5hqUAAqIBAAIWQmsKoXd3Y5pOgyE2BA",
]
FAIL_STICKERS = [
    "CAACAgIAAxkBAAEQAAE6aT7ixzphsIWAPUf6O9gnwMdsOdIAArEBAAIWQmsK_Er0l4LrkDE2BA",
]


def normalize_price(text: str) -> str:
    """Reduce any price string to "amount [currency]", or "—" when there is none."""
    if not text:
        return "—"
    match = re.search(r"(\d[\d\s.,]+)\s*(BYN|₽|RUB|USD|€)?", text, flags=re.IGNORECASE)
    if not match:
        return "—"
    amount = match.group(1).replace(",", ".").strip()
    currency = (match.group(2) or "").upper().replace("RUB", "₽")
    return f"{amount} {currency}".strip()


def extract_price(soup: BeautifulSoup) -> str:
    """Try the usual price selectors before falling back to the page text."""
    selectors = [
        "p.price",
        "span.price",
        "div.price",
        "div.product-price",
        "span.woocommerce-Price-amount",
        "ins .woocommerce-Price-amount",
        "meta[itemprop='price']",
        "[data-price]",
        "span[class*='cost']",
        "div[class*='price']",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if not element:
            continue
        if element.name == "meta":
            return normalize_price(element.get("content", "").strip())
        if element.has_attr("data-price"):
            return normalize_price(element["data-price"])
        price = normalize_price(element.get_text(" ", strip=True))
        if price != "—":
            return price
    return normalize_price(soup.get_text(" ", strip=True))


def looks_like_slug(text: str) -> bool:
    """True for machine strings like "nike-air-max-90-dm3975-010".

    Stores often put the URL slug inside the link text, which is useless to a
    human. Treating it as "not a title" lets the next heuristic find the real one.
    """
    text = text.strip()
    return bool(text) and " " not in text and "-" in text and len(text) > 15


def find_title_and_link(card, base: str):
    """Heuristics for a product card: (title, absolute url) or None."""
    # 1) explicit links with meaningful text
    for link in card.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        if not text or len(text) < 3 or re.fullmatch(r"[\d\s\-]+", text):
            continue
        if looks_like_slug(text):
            continue
        return text, urljoin(base, link["href"])

    # 2) image alt text
    image = card.find("img", alt=True)
    if image:
        alt = image.get("alt", "").strip()
        if alt and len(alt) >= 3 and not re.fullmatch(r"[\d\s\-]+", alt):
            parent = image.find_parent("a", href=True)
            href = parent["href"] if parent else image.get("data-src") or image.get("src")
            return alt, urljoin(base, href) if href else base

    # 3) title / aria-label
    for element in card.find_all(attrs={"title": True}) + card.find_all(
        attrs={"aria-label": True}
    ):
        text = element.get("title") or element.get("aria-label")
        if text and len(text.strip()) >= 3 and not re.fullmatch(r"[\d\s\-]+", text.strip()):
            href = element.get("href") or element.get("data-href") or None
            return text.strip(), urljoin(base, href) if href else base

    # 4) headings inside the card
    for tag in ("h1", "h2", "h3", "h4", "strong"):
        heading = card.select_one(tag)
        if not heading:
            continue
        text = heading.get_text(" ", strip=True)
        if text and len(text) >= 3 and not re.fullmatch(r"[\d\s\-]+", text):
            parent = heading.find_parent()
            link = parent.find("a", href=True) if parent else None
            href = link["href"] if link else None
            return text, urljoin(base, href) if href else base

    # 5) data-* attributes
    for attribute in ("data-name", "data-title", "data-product-name"):
        if not card.has_attr(attribute):
            continue
        text = card[attribute].strip()
        if text and len(text) >= 3 and not looks_like_slug(text):
            href = card.get("data-href") or card.get("data-url") or None
            return text, urljoin(base, href) if href else base

    return None


async def fetch_html(session: aiohttp.ClientSession, url: str) -> BeautifulSoup | None:
    try:
        response = await session.get(url, timeout=20, allow_redirects=True)
        if response.status != 200:
            return None
        return BeautifulSoup(await response.text(), "lxml")
    except Exception:
        return None
