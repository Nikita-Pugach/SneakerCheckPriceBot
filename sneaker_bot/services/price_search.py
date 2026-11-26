"""Price search scenario: scrape the stores, build the message, answer."""

import asyncio
import logging
import random
from html import escape
from typing import Union
from urllib.parse import urljoin

import aiohttp
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from bs4 import BeautifulSoup

from sneaker_bot.menu.know_menu import know_menu
from sneaker_bot.menu.results_menu import results_menu
from sneaker_bot.parsers.kufar_parser import search as kufar_search
from sneaker_bot.parsers.price_parser import (
    BASE,
    CATALOGS,
    FAIL_STICKERS,
    HEADERS,
    MAX_PAGES_BUNT,
    MAX_PAGES_SNEAK,
    PAGE_DELAY,
    PER_CAT,
    PRICE_CONCURRENCY,
    SNEAKERS,
    SUCCESS_STICKERS,
    extract_price,
    fetch_html,
    find_title_and_link,
)
from sneaker_bot.services import history
from sneaker_bot.services.messages import track
from sneaker_bot.services.offers import CONDITION_NEW, Offer, render, value_of
from sneaker_bot.services.products import is_footwear, is_new
from sneaker_bot.services.send_messages import record_and_send
from sneaker_bot.tasks import tasks

logger = logging.getLogger(__name__)

PRODUCT_CARD_SELECTOR = (
    "div[class*='product'], li[class*='product'], article[class*='product']"
)
ANY_CARD_SELECTOR = "div, li, article"


async def _price_of(session: aiohttp.ClientSession, item: tuple[str, str]) -> tuple[str, str, str]:
    """Fetch a product page and return (title, price, url)."""
    title, url = item
    try:
        response = await session.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(await response.text(), "lxml")
        price = extract_price(soup)
        if price and price not in {"—", "ошибка"} and " " not in price:
            # Both stores are Belarusian and often print the bare number.
            price = f"{price} BYN"
        return title, price or "—", url
    except Exception as exc:  # a dead product link must not kill the whole search
        logger.warning("price fetch failed for %s: %s", url, exc)
        return title, "ошибка", url


def _cards(soup: BeautifulSoup) -> list:
    cards = soup.select(PRODUCT_CARD_SELECTOR)
    return cards or soup.select(ANY_CARD_SELECTOR)


def _offers_from_shop(shop: str, priced: dict, categories: dict[str, str]) -> list[Offer]:
    """Turn the per-gender dict into offers; shop items are always new."""
    offers: list[Offer] = []
    for key, items in priced.items():
        category = categories.get(key, "")
        for title, price, url in items:
            offers.append(
                Offer(
                    shop=shop,
                    title=title,
                    price=price,
                    url=url,
                    category=category,
                    condition=CONDITION_NEW,
                )
            )
    return offers


def _offers_from_kufar(items: list[dict]) -> list[Offer]:
    return [
        Offer(
            shop="kufar.by",
            title=item.get("title", ""),
            price=item.get("price", ""),
            url=item.get("url", ""),
            condition=item.get("condition", ""),
            region=item.get("region", ""),
        )
        for item in items
    ]


async def process_price_search(
    user_id: int,
    query_ctx: Union[Message, CallbackQuery],
    state: FSMContext,
    query: str,
) -> None:
    """Search both stores for `query`, send a sticker and a result message."""
    logger.info("price search started for user %s, query=%r", user_id, query)
    loading = None
    try:
        loading = await record_and_send(
            query_ctx,
            state,
            text=(
                f"🔎 Ищем: <b>{escape(query.strip() or 'все кроссовки')}</b>\n"
                "Проверяем bunt.by, sneakers.by и kufar.by — обычно 20–40 секунд."
            ),
        )

        raw_bunt: dict[str, list] = {"muzhskie": [], "zhenskie": []}
        raw_sneakers: dict[str, list] = {"женские": [], "мужские": []}
        seen_bunt: set[str] = set()
        seen_sneakers: set[str] = set()

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            # bunt.by: catalogue pages
            for catalogue_url in CATALOGS:
                if not catalogue_url or not catalogue_url.strip():
                    continue
                key = "muzhskie" if "muzh" in catalogue_url.lower() else "zhenskie"

                for page in range(1, MAX_PAGES_BUNT + 1):
                    if len(raw_bunt[key]) >= PER_CAT:
                        break
                    page_url = (
                        catalogue_url
                        if page == 1
                        else urljoin(catalogue_url, f"/page/{page}/")
                    )
                    if page > 1:
                        await asyncio.sleep(PAGE_DELAY)
                    soup = await fetch_html(session, page_url)
                    if soup is None:
                        break
                    for card in _cards(soup):
                        found = find_title_and_link(card, BASE or catalogue_url)
                        if not found:
                            continue
                        title, url = found
                        if query and query.strip() and query.lower() not in title.lower():
                            continue
                        if not is_footwear(title):
                            continue
                        if not is_new(seen_bunt, title, url):
                            continue
                        raw_bunt[key].append((title, url))
                        if len(raw_bunt[key]) >= PER_CAT:
                            break

            # sneakers.by: catalogue pages
            for kind, base in SNEAKERS.items():
                if not base or not base.strip():
                    continue
                for page in range(1, MAX_PAGES_SNEAK + 1):
                    if len(raw_sneakers[kind]) >= PER_CAT:
                        break
                    page_url = base if page == 1 else f"{base}?page={page}"
                    if page > 1:
                        await asyncio.sleep(PAGE_DELAY)
                    soup = await fetch_html(session, page_url)
                    if soup is None:
                        break
                    for card in _cards(soup):
                        found = find_title_and_link(card, BASE or base)
                        if not found:
                            continue
                        title, url = found
                        if query and query.strip() and query.lower() not in title.lower():
                            continue
                        if not is_footwear(title):
                            continue
                        if not is_new(seen_sneakers, title, url):
                            continue
                        raw_sneakers[kind].append((title, url))
                        if len(raw_sneakers[kind]) >= PER_CAT:
                            break

            # Product pages are fetched with a cap on concurrency: a polite crawl
            # instead of a hundred parallel requests at a small shop.
            semaphore = asyncio.Semaphore(PRICE_CONCURRENCY)

            async def priced(item):
                async with semaphore:
                    return await _price_of(session, item)

            bunt_prices = {
                key: await asyncio.gather(*[priced(item) for item in items])
                for key, items in raw_bunt.items()
            }
            sneaker_prices = {
                key: await asyncio.gather(*[priced(item) for item in items])
                for key, items in raw_sneakers.items()
            }

            # Kufar returns prices and the item condition in the search response.
            kufar_items = await kufar_search(session, query, PER_CAT)

        offers = _offers_from_shop(
            "bunt.by", bunt_prices, {"muzhskie": "Мужские", "zhenskie": "Женские"}
        )
        offers += _offers_from_shop(
            "sneakers.by", sneaker_prices, {"мужские": "Мужские", "женские": "Женские"}
        )
        offers += _offers_from_kufar(kufar_items)

        prices = [value for value in (value_of(offer) for offer in offers) if value is not None]
        cheapest = min(prices) if prices else None
        previous = history.previous_min(user_id, query)
        try:
            history.save_search(user_id, query, found=len(prices), min_price=cheapest)
        except Exception as exc:  # history must never break a search
            logger.warning("could not save the search to history: %s", exc)

        logger.info(
            "price search finished for user %s: %s priced offers, cheapest=%s",
            user_id,
            len(prices),
            cheapest,
        )

        sticker = random.choice(FAIL_STICKERS if not prices else SUCCESS_STICKERS)
        sticker_message = await query_ctx.bot.send_sticker(
            chat_id=query_ctx.from_user.id, sticker=sticker
        )
        await track(state, sticker_message)

        if not prices:
            await record_and_send(
                query_ctx, state, text="Ничего не найдено 😔", reply_markup=know_menu
            )
            return

        text = render(offers, previous_min=previous)
        sent = await record_and_send(
            query_ctx,
            state,
            text=text,
            reply_markup=results_menu(),
            disable_web_page_preview=True,
        )
        await state.update_data(
            results={
                "query": query,
                "offers": [offer.to_dict() for offer in offers],
                "max_price": None,
                "condition": None,
                "previous_min": previous,
            }
        )

    except asyncio.CancelledError:
        logger.info("price search cancelled for user %s", user_id)
        return
    finally:
        # The loading message must disappear even if scraping blew up halfway;
        # previously the cleanup lived after the try block and was skipped.
        if loading is not None:
            try:
                await query_ctx.bot.delete_message(
                    chat_id=loading.chat.id, message_id=loading.message_id
                )
            except TelegramBadRequest:
                pass
            except Exception as exc:
                logger.warning("could not delete the loading message: %s", exc)
        tasks.pop(user_id, None)
