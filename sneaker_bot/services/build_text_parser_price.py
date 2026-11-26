"""Render the search results as one Telegram message (legacy dict interface).

The shops return different shapes, so this module only flattens them into
`Offer` objects; filtering and formatting live in `services.offers`.
"""

from sneaker_bot.services.offers import CONDITION_NEW, Offer, render


def build_result_text(fb: dict, fs: dict, extra: dict | None = None) -> str:
    offers: list[Offer] = []

    shops = [
        ("bunt.by", fb, {"muzhskie": "Мужские", "zhenskie": "Женские"}),
        ("sneakers.by", fs, {"мужские": "Мужские", "женские": "Женские"}),
    ]
    for shop_name, data_dict, caps in shops:
        for key, category in caps.items():
            for title, price, url in data_dict.get(key, []):
                offers.append(
                    Offer(
                        shop=shop_name,
                        title=title,
                        price=price,
                        url=url,
                        category=category,
                        condition=CONDITION_NEW,
                    )
                )

    for shop_name, items in (extra or {}).items():
        for item in items:
            if len(item) == 3:
                title, price, url = item
                offers.append(Offer(shop=shop_name, title=title, price=price, url=url))
            else:
                title, price, url, condition, region = item
                offers.append(
                    Offer(
                        shop=shop_name,
                        title=title,
                        price=price,
                        url=url,
                        condition=condition,
                        region=region,
                    )
                )

    return render(offers)
