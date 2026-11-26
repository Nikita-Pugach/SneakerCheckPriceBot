"""Offers: one shape for every shop, so filters and rendering stay in one place."""

from dataclasses import asdict, dataclass, field

from sneaker_bot.services.price_format import format_amount, parse_price, plural

NOT_FOUND = "Товар не найден ни в одном магазине."
FILTERED_OUT = "Под такие фильтры ничего не подошло. Снимите фильтр или измените цену."

CONDITION_NEW = "Новое"
CONDITION_USED = "Б/у"

_SHOP_ORDER = ["bunt.by", "sneakers.by", "kufar.by"]


@dataclass
class Offer:
    """One product found in one shop."""

    shop: str
    title: str
    price: str
    url: str
    category: str = ""
    condition: str = ""
    region: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Offer":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{key: value for key, value in data.items() if key in known})


def value_of(offer: Offer) -> float | None:
    """Numeric price, or None when the shop did not give one."""
    return parse_price(offer.price)


def _normalise_condition(condition: str | None) -> str | None:
    if not condition:
        return None
    lowered = condition.strip().lower()
    if lowered in {"new", "новое", "новый", "новая"}:
        return CONDITION_NEW
    if lowered in {"used", "б/у", "бу"}:
        return CONDITION_USED
    return condition


def apply_filters(
    offers: list[Offer],
    max_price: float | None = None,
    condition: str | None = None,
) -> list[Offer]:
    """Keep priced offers that satisfy the price cap and the condition."""
    wanted = _normalise_condition(condition)
    kept: list[Offer] = []
    for offer in offers:
        value = value_of(offer)
        if value is None:
            continue
        if max_price is not None and value > max_price:
            continue
        if wanted is not None and offer.condition != wanted:
            continue
        kept.append(offer)
    return kept


def _shop_rank(shop: str) -> tuple[int, str]:
    try:
        return _SHOP_ORDER.index(shop), ""
    except ValueError:
        return len(_SHOP_ORDER), shop


def _suffix(offer: Offer) -> str:
    parts = []
    if offer.condition == CONDITION_USED:
        parts.append("б/у")
    if offer.region:
        parts.append(offer.region)
    return f" · {', '.join(parts)}" if parts else ""


def _summary(prices: list[float]) -> str | None:
    if not prices:
        return None
    count = len(prices)
    return (
        f"💰 <b>Минимум: {format_amount(min(prices))}</b>"
        f" · среднее {format_amount(sum(prices) / count)}"
        f" · {count} {plural(count, 'предложение', 'предложения', 'предложений')}"
    )


def _delta(current: float, previous: float) -> str:
    diff = current - previous
    if abs(diff) < 1:
        return ""
    if diff < 0:
        return f"📉 Подешевело на {format_amount(abs(diff))} с прошлого раза"
    return f"📈 Подорожало на {format_amount(diff)} с прошлого раза"


def render(
    offers: list[Offer],
    max_price: float | None = None,
    condition: str | None = None,
    previous_min: float | None = None,
) -> str:
    """Build the Telegram message for the offers that pass the filters."""
    filtered = apply_filters(offers, max_price=max_price, condition=condition)
    if not filtered:
        if not offers:
            return NOT_FOUND
        if max_price is not None or condition:
            return FILTERED_OUT
        return NOT_FOUND

    prices = [value for value in (value_of(o) for o in filtered) if value is not None]

    # shop -> category -> offers, keeping the shops in a stable order.
    grouped: dict[str, dict[str, list[Offer]]] = {}
    for offer in sorted(filtered, key=lambda item: _shop_rank(item.shop)[0]):
        grouped.setdefault(offer.shop, {}).setdefault(offer.category, []).append(offer)

    parts: list[str] = []
    for shop, categories in grouped.items():
        shop_prices = [
            value for value in (value_of(o) for items in categories.values() for o in items)
            if value is not None
        ]
        shop_min = f" · от {format_amount(min(shop_prices))}" if shop_prices else ""
        parts.append(f"<b>Магазин:</b> {shop}{shop_min}")
        parts.append("")

        for category, items in categories.items():
            if category:
                parts.append(f"<b>{category}</b>")
            for idx, offer in enumerate(items, start=1):
                parts.append(
                    f"{idx}. {offer.title}{_suffix(offer)}\n"
                    f"   Цена: <code>{offer.price}</code>\n"
                    f"   <a href=\"{offer.url}\">Ссылка</a>"
                )
            parts.append("")

    header = _summary(prices)
    if previous_min is not None and prices:
        note = _delta(min(prices), previous_min)
        if note:
            header = f"{header}\n{note}" if header else note

    body = "\n".join(parts).strip()
    return f"{header}\n\n{body}" if header else body
