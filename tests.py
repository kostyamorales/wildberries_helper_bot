from unittest import TestCase
from validators import *


class ValidatorsTestCase(TestCase):

    def test_validate_article(self):
        self.assertEqual(validate_article('5904890'), None)
        self.assertEqual(validate_article('9266068'), '9266068')
        self.assertEqual(validate_article('?'), None)

    def test_validate_on_sale(self):
        self.assertEqual(validate_item_price('5904890'), None)
        self.assertEqual(validate_item_price('13668138'), 1835)
        self.assertEqual(validate_item_price('?'), None)

    def test_validate_price(self):
        self.assertEqual(validate_price(1000, '900'), True)