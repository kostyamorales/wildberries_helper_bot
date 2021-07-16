import requests
from bs4 import BeautifulSoup
import logging
import utils

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wb')


def get_url(article):
    return f'https://www.wildberries.ru/catalog/{article}/detail.aspx'


def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                      ' AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/91.0.4472.77 Safari/537.36',
        'Accept-Language': 'ru',
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.text


def get_data(html):
    soup = BeautifulSoup(html, 'lxml')
    return soup


def get_brand_and_name(article):
    soup = get_data(get_html(get_url(article)))
    brand_and_name = soup.select_one('h1.same-part-kt__header').text.strip()
    if not brand_and_name:
        logger.error('no brand_and_name block')
    return brand_and_name


def get_price(article):
    soup = get_data(get_html(get_url(article)))
    price = soup.select_one('div.price-block__content')
    if not price:
        return
    final_price = price.select_one('.price-block__final-price').text
    final_price = int(''.join(final_price.split()).replace('₽', ''))
    return final_price


def get_sizes(article):
    soup = get_data(get_html(get_url(article)))
    block_sizes = soup.select('li.sizes-list__item')
    if not block_sizes:
        logger.error('no block_sizes')
        return
    sizes = utils.get_thing_sizes(block_sizes)
    return sizes
