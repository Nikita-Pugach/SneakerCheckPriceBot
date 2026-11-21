"""extract_price walks a list of CSS selectors, so each shape gets a test."""

from bs4 import BeautifulSoup

from sneaker_bot.parsers.price_parser import extract_price


def parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def test_span_with_price_class():
    html = '<div><span class="price">1 299,00 BYN</span></div>'
    assert extract_price(parse(html)) == "1 299.00 BYN"


def test_meta_itemprop_price():
    html = '<html><head><meta itemprop="price" content="4999.00"></head><body></body></html>'
    assert extract_price(parse(html)) == "4999.00"


def test_data_price_attribute():
    assert extract_price(parse('<div data-price="3499"></div>')) == "3499"


def test_falls_back_to_page_text():
    html = "<html><body><p>Кроссовки Nike</p><p>4599.00 BYN</p></body></html>"
    assert extract_price(parse(html)) == "4599.00 BYN"


def test_page_without_a_price_returns_dash():
    html = "<html><body><p>Нет в наличии</p></body></html>"
    assert extract_price(parse(html)) == "—"
