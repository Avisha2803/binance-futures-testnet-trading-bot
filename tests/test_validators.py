import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)


class TestValidators(unittest.TestCase):
    def test_valid_symbol(self):
        self.assertEqual(validate_symbol("btcusdt"), "BTCUSDT")

    def test_invalid_symbol(self):
        with self.assertRaises(ValueError):
            validate_symbol("BTC")

    def test_valid_side(self):
        self.assertEqual(validate_side("buy"), "BUY")
        self.assertEqual(validate_side("SELL"), "SELL")

    def test_invalid_side(self):
        with self.assertRaises(ValueError):
            validate_side("HOLD")

    def test_valid_order_type(self):
        self.assertEqual(validate_order_type("market"), "MARKET")
        self.assertEqual(validate_order_type("limit"), "LIMIT")
        self.assertEqual(validate_order_type("stop_limit"), "STOP_LIMIT")

    def test_invalid_order_type(self):
        with self.assertRaises(ValueError):
            validate_order_type("TRAILING_STOP")

    def test_valid_quantity(self):
        self.assertEqual(validate_quantity("0.01"), 0.01)

    def test_invalid_quantity_zero(self):
        with self.assertRaises(ValueError):
            validate_quantity("0")

    def test_invalid_quantity_not_a_number(self):
        with self.assertRaises(ValueError):
            validate_quantity("abc")

    def test_price_required_for_limit(self):
        with self.assertRaises(ValueError):
            validate_price(None, "LIMIT")
        self.assertEqual(validate_price("100.5", "LIMIT"), 100.5)

    def test_price_ignored_for_market(self):
        self.assertIsNone(validate_price(None, "MARKET"))

    def test_stop_price_required_for_stop_limit(self):
        with self.assertRaises(ValueError):
            validate_stop_price(None, "STOP_LIMIT")
        self.assertEqual(validate_stop_price("99.5", "STOP_LIMIT"), 99.5)

    def test_stop_price_ignored_otherwise(self):
        self.assertIsNone(validate_stop_price(None, "LIMIT"))


if __name__ == "__main__":
    unittest.main()
