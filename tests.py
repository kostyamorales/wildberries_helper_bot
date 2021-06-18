from unittest import TestCase
from validators import *
import parser


class ValidatorsTestCase(TestCase):

    def test_validate_article(self):
        self.assertEqual(validate_article('7777'), '7777')  # нет в наличии
        self.assertEqual(validate_article('29242231'), '29242231')  # в наличии
        self.assertEqual(validate_article('123'), None)  # артикул не существует
        self.assertEqual(validate_article('?'), None)  # спец символы

    def test_validate_on_sale(self):
        # получаем уже проверенные артикулы после validate_article_tp
        self.assertEqual(validate_item_price('7777'), None)  # нет в наличии
        self.assertEqual(validate_item_price('29242231'), 1077)  # в наличии

    def test_validate_price(self):
        self.assertEqual(validate_price(1000, '900'), True)

    def test_validate_size(self):
        sizes = parser.get_sizes('29477635')
        self.assertEqual(validate_size('xs', sizes), 'xs')
        self.assertEqual(validate_size('3xl', sizes), None)
        self.assertEqual(validate_size('1', sizes), None)

