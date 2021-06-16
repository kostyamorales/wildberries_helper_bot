import parser
from requests.exceptions import HTTPError


def validate_article(article):
    url = f'https://www.wildberries.ru/catalog/{(article)}/detail.aspx'
    try:
        parser.get_html(url)
    except HTTPError:
        return None
    return article


def validate_item_price(article):
    price = parser.get_price(article)
    if not price:
        return None
    return price


def validate_price(item_price, price):
    if not price.isdigit():
        return False
    if int(price) >= item_price:
        return False
    return True
