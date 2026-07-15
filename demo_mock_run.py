#!/usr/bin/env python3
"""
demo_mock_run.py
=================
This script is NOT part of the trading bot itself. It exists purely to
produce example log entries for this submission, because the environment
used to author this code does not have network access to
demo-fapi.binance.com (Binance's Futures Demo Trading API).

It monkey-patches BinanceFuturesClient.place_order() with a fake response
shaped exactly like a real Binance Futures order response, then runs the
*real* OrderManager / logging code path against it. This exercises all the
real request-building, logging, and CLI-printing logic -- only the actual
HTTP call to Binance is stubbed out.

To generate REAL logs against the live testnet, run cli.py directly with
valid API credentials instead (see README.md).
"""

from unittest.mock import patch

from bot.client import BinanceFuturesClient
from bot.orders import OrderManager
from bot.logging_config import setup_logger

logger = setup_logger()


FAKE_MARKET_RESPONSE = {
    "orderId": 3141592653,
    "symbol": "BTCUSDT",
    "status": "FILLED",
    "side": "BUY",
    "type": "MARKET",
    "origQty": "0.010",
    "executedQty": "0.010",
    "avgPrice": "64912.30",
    "price": "0",
}

FAKE_LIMIT_RESPONSE = {
    "orderId": 3141592654,
    "symbol": "ETHUSDT",
    "status": "NEW",
    "side": "SELL",
    "type": "LIMIT",
    "origQty": "0.500",
    "executedQty": "0.000",
    "avgPrice": "0.00",
    "price": "3200.00",
}


def run_demo():
    client = BinanceFuturesClient(api_key="TESTNET_DEMO_KEY", api_secret="TESTNET_DEMO_SECRET")
    manager = OrderManager(client)

    logger.info("=== DEMO: simulated MARKET order (mocked HTTP response) ===")
    with patch.object(client, "place_order", return_value=FAKE_MARKET_RESPONSE):
        result = manager.place_order(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.01)
        print("MARKET order result:", result)

    logger.info("=== DEMO: simulated LIMIT order (mocked HTTP response) ===")
    with patch.object(client, "place_order", return_value=FAKE_LIMIT_RESPONSE):
        result = manager.place_order(
            symbol="ETHUSDT", side="SELL", order_type="LIMIT", quantity=0.5, price=3200.0
        )
        print("LIMIT order result:", result)


if __name__ == "__main__":
    run_demo()
