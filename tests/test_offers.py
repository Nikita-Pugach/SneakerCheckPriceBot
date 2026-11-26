"""Offers: filters and rendering under them."""

from sneaker_bot.services.offers import (
    CONDITION_NEW,
    CONDITION_USED,
    FILTERED_OUT,
    NOT_FOUND,
    Offer,
    apply_filters,
    render,
)


def make(shop="kufar.by", title="Кроссовки", price="250 BYN", condition="", region=""):
    return Offer(shop=shop, title=title, price=price, url="https://x/1", condition=condition, region=region)


def test_price_cap_keeps_cheaper_offers():
    offers = [make(price="150 BYN"), make(price="300 BYN")]
    kept = apply_filters(offers, max_price=200)
    assert [offer.price for offer in kept] == ["150 BYN"]


def test_unpriced_offers_are_dropped():
    offers = [make(price="—"), make(price="ошибка"), make(price="100 BYN")]
    assert len(apply_filters(offers)) == 1


def test_condition_filter_used_only():
    offers = [
        make(title="new one", condition=CONDITION_NEW),
        make(title="used one", condition=CONDITION_USED),
    ]
    kept = apply_filters(offers, condition="used")
    assert [offer.title for offer in kept] == ["used one"]


def test_condition_filter_new_only():
    offers = [
        make(title="new one", condition=CONDITION_NEW),
        make(title="used one", condition=CONDITION_USED),
    ]
    kept = apply_filters(offers, condition="new")
    assert [offer.title for offer in kept] == ["new one"]


def test_unknown_condition_is_dropped_when_filtering():
    offers = [make(condition=""), make(condition=CONDITION_NEW)]
    assert len(apply_filters(offers, condition="new")) == 1


def test_price_and_condition_are_combined():
    offers = [
        make(price="100 BYN", condition=CONDITION_USED),
        make(price="900 BYN", condition=CONDITION_USED),
        make(price="100 BYN", condition=CONDITION_NEW),
    ]
    kept = apply_filters(offers, max_price=200, condition="used")
    assert len(kept) == 1


def test_empty_input_gives_not_found():
    assert render([]) == NOT_FOUND


def test_filters_that_remove_everything_explain_themselves():
    text = render([make(price="900 BYN")], max_price=100)
    assert text == FILTERED_OUT


def test_used_and_region_are_shown_next_to_the_title():
    offers = [make(price="200 BYN", condition=CONDITION_USED, region="Минск")]
    text = render(offers)
    assert "Кроссовки · б/у, Минск" in text


def test_new_offers_are_not_labelled():
    offers = [make(price="200 BYN", condition=CONDITION_NEW)]
    text = render(offers)
    assert "Кроссовки\n" in text


def test_price_drop_is_reported():
    offers = [make(price="180 BYN")]
    text = render(offers, previous_min=250)
    assert "📉 Подешевело на 70 BYN" in text


def test_price_growth_is_reported():
    offers = [make(price="280 BYN")]
    text = render(offers, previous_min=250)
    assert "📈 Подорожало на 30 BYN" in text


def test_same_price_has_no_delta_line():
    text = render([make(price="250 BYN")], previous_min=250)
    assert "Подешевело" not in text
    assert "Подорожало" not in text


def test_filters_keep_the_summary_of_the_visible_offers_only():
    offers = [make(price="100 BYN"), make(price="900 BYN")]
    text = render(offers, max_price=200)
    assert "Минимум: 100 BYN" in text
    assert "1 предложение" in text


def test_offers_survive_a_round_trip_through_a_dict():
    offer = make(price="250 BYN", condition=CONDITION_USED, region="Гомель")
    restored = Offer.from_dict(offer.to_dict())
    assert restored == offer
