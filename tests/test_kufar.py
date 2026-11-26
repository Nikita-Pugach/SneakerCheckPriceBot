"""Kufar JSON parsing: footwear only, priced only, condition and city kept."""

from sneaker_bot.parsers.kufar_parser import format_price, parse_ads

PAYLOAD = {
    "ads": [
        {"subject": "Кроссовки Nike Air Max", "price_byn": 25000, "ad_link": "https://kufar/item/1"},
        {"subject": "Худи NIKE", "price_byn": 12000, "ad_link": "https://kufar/item/2"},
        {"subject": "Кеды Adidas", "price_byn": 0, "ad_link": "https://kufar/item/3"},
        {"subject": "Ботинки ECCO", "price_byn": 9950, "ad_link": "https://kufar/item/4"},
        {"subject": "Кроссовки", "price_byn": None, "ad_link": "https://kufar/item/5"},
        {"subject": "Кроссовки без ссылки", "price_byn": 1000, "ad_link": ""},
    ]
}

DETAILED = {
    "ads": [
        {
            "subject": "Кроссовки Nike Air Max 90",
            "price_byn": 25000,
            "ad_link": "https://kufar/item/9",
            "ad_parameters": [
                {"p": "condition", "vl": "Б/у"},
                {"p": "region", "vl": "Минск"},
                {"p": "men_shoes_size", "vl": ["42"]},
            ],
        }
    ]
}


def test_only_footwear_with_a_price_survives():
    items = parse_ads(PAYLOAD, limit=10)
    assert [item["title"] for item in items] == [
        "Кроссовки Nike Air Max",
        "Ботинки ECCO",
    ]
    assert items[0]["price"] == "250 BYN"
    assert items[0]["url"] == "https://kufar/item/1"


def test_condition_and_region_are_extracted():
    items = parse_ads(DETAILED, limit=5)
    assert items[0]["condition"] == "Б/у"
    assert items[0]["region"] == "Минск"


def test_missing_parameters_give_empty_strings():
    items = parse_ads(PAYLOAD, limit=10)
    assert items[0]["condition"] == ""
    assert items[0]["region"] == ""


def test_limit_is_respected():
    assert len(parse_ads(PAYLOAD, limit=1)) == 1


def test_empty_payload():
    assert parse_ads({}, limit=5) == []


def test_price_formatting():
    # Kufar reports kopecks: 25000 == 250 BYN
    assert format_price(25000) == "250 BYN"
    assert format_price(9950) == "99.50 BYN"
    assert format_price(0) == ""
    assert format_price(None) == ""
    assert format_price("unknown") == ""
