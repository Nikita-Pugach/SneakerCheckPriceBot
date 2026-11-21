"""Price search scenario: scrape the stores, build the message, answer."""

import asyncio
import logging
import random
from typing import Union
from urllib.parse import urljoin

import aiohttp
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from bs4 import BeautifulSoup

from sneaker_bot.menu.know_menu import know_menu
from sneaker_bot.parsers.price_parser import (
    BASE,
    CATALOGS,
    FAIL_STICKERS,
    HEADERS,
    MAX_PAGES_BUNT,
    MAX_PAGES_SNEAK,
    PER_CAT,
    SNEAKERS,
    SUCCESS_STICKERS,
    extract_price,
    fetch_html,
    find_title_and_link,
)
from sneaker_bot.services.build_text_parser_price import build_result_text
from sneaker_bot.services.products import is_new
from sneaker_bot.services.send_messages import record_and_send
from sneaker_bot.tasks import tasks

logger = logging.getLogger(__name__)

PRODUCT_CARD_SELECTOR = (
    "div[class*='product'], li[class*='product'], article[class*='product']"
)
ANY_CARD_SELECTOR = "div, li, article"


async def _save_sticker_info(state: FSMContext, sticker_msg: Message) -> None:
    await state.update_data(
        sticker_info={"chat_id": sticker_msg.chat.id, "message_id": sticker_msg.message_id}
    )


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


async def process_price_search(
    user_id: int,
    query_ctx: Union[Message, CallbackQuery],
    state: FSMContext,
    query: str,
) -> None:
    """Search both stores for `query`, send a sticker and a result message."""
    logger.info("price search started for user %s, query=%r", user_id, query)
    try:
        temporary: list[dict] = []
        loading = await record_and_send(
            query_ctx, state, text="Ищем указанную модель кроссовок и схожие модели…"
        )
        temporary.append({"chat_id": loading.chat.id, "message_id": loading.message_id})

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
                        if not is_new(seen_sneakers, title, url):
                            continue
                        raw_sneakers[kind].append((title, url))
                        if len(raw_sneakers[kind]) >= PER_CAT:
                            break

            bunt_prices = {
                key: await asyncio.gather(*[_price_of(session, item) for item in items])
                for key, items in raw_bunt.items()
            }
            sneaker_prices = {
                key: await asyncio.gather(*[_price_of(session, item) for item in items])
                for key, items in raw_sneakers.items()
            }

        text = build_result_text(bunt_prices, sneaker_prices)
        no_results = all(
            len(items) == 0
            for items in list(bunt_prices.values()) + list(sneaker_prices.values())
        )
        logger.info(
            "price search finished for user %s: %s bunt, %s sneakers, no_results=%s",
            user_id,
            sum(len(items) for items in bunt_prices.values()),
            sum(len(items) for items in sneaker_prices.values()),
            no_results,
        )

        sticker = random.choice(FAIL_STICKERS if no_results else SUCCESS_STICKERS)
        sticker_message = await query_ctx.bot.send_sticker(
            chat_id=query_ctx.from_user.id, sticker=sticker
        )
        await _save_sticker_info(state, sticker_message)

        if no_results:
            await record_and_send(
                query_ctx, state, text="Ничего не найдено 😔", reply_markup=know_menu
            )
        else:
            await record_and_send(
                query_ctx,
                state,
                text=text,
                reply_markup=know_menu,
                disable_web_page_preview=True,
            )

        for message in temporary:
            try:
                await query_ctx.bot.delete_message(
                    chat_id=message["chat_id"], message_id=message["message_id"]
                )
            except TelegramBadRequest:
                pass

    except asyncio.CancelledError:
        logger.info("price search cancelled for user %s", user_id)
        return
    finally:
        tasks.pop(user_id, None)
