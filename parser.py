import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wb')


def get_url(article):
    return f'https://www.wildberries.ru/catalog/{str(article)}/detail.aspx'


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


def get_brand_and_name(soup):
    brand_and_name = soup.select_one('div.brand-and-name').text.strip()
    if not brand_and_name:
        logger.error('no brand_and_name block')
    return brand_and_name


def get_price(soup):
    price = soup.select_one('div.inner-price')
    if not price:
        return
    final_price = price.select_one('div.final-price-block').text
    final_price = int(''.join(final_price.split()).replace('₽', ''))
    return final_price


def get_sizes(soup):
    block_sizes = soup.select('div.size-list.j-size-list label')
    if not block_sizes:
        logger.error('no block_sizes')
        return
    sizes = []
    for block_size in block_sizes:
        s = str(block_size.select('span'))
        s_value = s.replace('[<span>', '').replace('</span>]', '')
        # на случай если размеры у товара не предусмотрены
        if s_value == '0':
            return
        flag = True
        if 'disabled' in str(block_size):
            flag = False
        sizes.append((s_value, flag))
    return sizes
