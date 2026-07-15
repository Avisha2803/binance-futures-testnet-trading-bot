import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.orders import OrderManager
from bot.client import BinanceAPIError, BinanceNetworkError


class TestOrderManager(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.manager = OrderManager(self.mock_client)

    def test_build_request_market(self):
        req = self.manager.build_request("BTCUSDT", "BUY", "MARKET", 0.01)
        self.assertEqual(req, {
            "symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.01,
        })

    def test_build_request_limit(self):
        req = self.manager.build_request("BTCUSDT", "SELL", "LIMIT", 0.01, price=65000)
        self.assertEqual(req["type"], "LIMIT")
        self.assertEqual(req["price"], 65000)
        self.assertEqual(req["timeInForce"], "GTC")

    def test_build_request_stop_limit(self):
        req = self.manager.build_request(
            "BTCUSDT", "SELL", "STOP_LIMIT", 0.01, price=60000, stop_price=60500
        )
        self.assertEqual(req["type"], "STOP")
        self.assertEqual(req["price"], 60000)
        self.assertEqual(req["stopPrice"], 60500)

    def test_place_order_success_returns_summary(self):
        self.mock_client.place_order.return_value = {
            "orderId": 123456,
            "symbol": "BTCUSDT",
            "status": "FILLED",
            "side": "BUY",
            "type": "MARKET",
            "origQty": "0.01",
            "executedQty": "0.01",
            "avgPrice": "65000.10",
            "price": "0",
        }
        result = self.manager.place_order("BTCUSDT", "BUY", "MARKET", 0.01)
        self.assertEqual(result["orderId"], 123456)
        self.assertEqual(result["status"], "FILLED")
        self.assertEqual(result["executedQty"], "0.01")

    def test_place_order_propagates_api_error(self):
        self.mock_client.place_order.side_effect = BinanceAPIError("Insufficient margin")
        with self.assertRaises(BinanceAPIError):
            self.manager.place_order("BTCUSDT", "BUY", "MARKET", 0.01)

    def test_place_order_propagates_network_error(self):
        self.mock_client.place_order.side_effect = BinanceNetworkError("timeout")
        with self.assertRaises(BinanceNetworkError):
            self.manager.place_order("BTCUSDT", "BUY", "MARKET", 0.01)


if __name__ == "__main__":
    unittest.main()
