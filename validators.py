import parser
from requests.exceptions import HTTPError


def validate_article(article):
    if not article.isdigit():
        return None
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


def validate_size(value, sizes):
    size = ''
    for i in value:
        if i.isalpha():
            i = i.lower()
        size += i
    if size not in sizes:
        return None
    return size


def validate_item_id(answer, items_id):
    try:
        item_id = int(answer)
    except ValueError:
        return None
    if item_id not in items_id:
        return None
    return item_id
