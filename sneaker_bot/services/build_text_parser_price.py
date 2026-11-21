def build_result_text(fb: dict, fs: dict, extra: dict | None = None) -> str:
    parts = []
    shops = [
        ("bunt.by", fb, {"muzhskie": "Мужские", "zhenskie": "Женские"}),
        ("sneakers.by", fs, {"мужские": "Мужские", "женские": "Женские"})
    ]

    found_anywhere = False  # флаг: найден ли хоть один товар с ценой

    for shop_name, data_dict, caps in shops:
        shop_parts = []
        for key, title in caps.items():
            items = data_dict.get(key, [])
            # фильтруем товары с нормальной ценой
            filtered = [(t, price, url) for t, price, url in items if price not in ["—", "–", "ошибка"]]
            if not filtered:
                continue

            found_anywhere = True
            shop_parts.append(f"<b>{title}</b>")
            for idx, (t, price, url) in enumerate(filtered, start=1):
                shop_parts.append(
                    f"{idx}. {t}\n"
                    f"   Цена: <code>{price}</code>\n"
                    f"   <a href=\"{url}\">Ссылка</a>"
                )
            shop_parts.append("")

        if shop_parts:
            parts.append(f"<b>Магазин:</b> {shop_name}")
            parts.append("")
            parts.extend(shop_parts)
            parts.append("")

    # Stores that already return priced items keep a simpler layout.
    for shop_name, items in (extra or {}).items():
        if not items:
            continue
        found_anywhere = True
        parts.append(f"<b>Магазин:</b> {shop_name}")
        parts.append("")
        for idx, (title, price, url) in enumerate(items, start=1):
            parts.append(
                f"{idx}. {title}\n"
                f"   Цена: <code>{price}</code>\n"
                f"   <a href=\"{url}\">Ссылка</a>"
            )
        parts.append("")

    if not found_anywhere:
        return "Товар не найден ни в одном магазине."

    return "\n".join(parts).strip()
