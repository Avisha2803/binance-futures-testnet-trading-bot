"""
Order placement logic, sitting between the CLI layer and the raw API client.

Builds correctly-shaped request payloads for MARKET, LIMIT and STOP_LIMIT
(bonus) orders, and normalizes the response into a small summary dict that
the CLI can print consistently.
"""

import logging

from .client import BinanceFuturesClient, BinanceAPIError, BinanceNetworkError

logger = logging.getLogger("trading_bot")


class OrderManager:
    def __init__(self, client: BinanceFuturesClient):
        self.client = client

    def build_request(self, symbol: str, side: str, order_type: str,
                       quantity: float, price: float = None,
                       stop_price: float = None) -> dict:
        """Build the exact params dict that will be sent to Binance."""
        request = {
            "symbol": symbol,
            "side": side,
            "type": "STOP" if order_type == "STOP_LIMIT" else order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            request["price"] = price
            request["timeInForce"] = "GTC"  # Good-Til-Canceled, standard default
        elif order_type == "STOP_LIMIT":
            # Binance Futures represents a stop-limit as type=STOP with both
            # price (limit price) and stopPrice (trigger price).
            request["price"] = price
            request["stopPrice"] = stop_price
            request["timeInForce"] = "GTC"

        return request

    def place_order(self, symbol: str, side: str, order_type: str,
                     quantity: float, price: float = None,
                     stop_price: float = None) -> dict:
        request = self.build_request(symbol, side, order_type, quantity, price, stop_price)

        logger.info(
            "Placing order | symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s",
            symbol, side, order_type, quantity, price, stop_price,
        )

        try:
            response = self.client.place_order(**request)
        except BinanceAPIError as exc:
            logger.error("Order REJECTED by API: %s", exc)
            raise
        except BinanceNetworkError as exc:
            logger.error("Order FAILED due to network issue: %s", exc)
            raise

        logger.info(
            "Order ACCEPTED | orderId=%s status=%s",
            response.get("orderId"), response.get("status"),
        )

        return self._summarize(response)

    @staticmethod
    def _summarize(response: dict) -> dict:
        """Pull out the fields the assignment asks us to display."""
        return {
            "orderId": response.get("orderId"),
            "symbol": response.get("symbol"),
            "status": response.get("status"),
            "side": response.get("side"),
            "type": response.get("type"),
            "origQty": response.get("origQty"),
            "executedQty": response.get("executedQty"),
            "avgPrice": response.get("avgPrice"),
            "price": response.get("price"),
            "raw": response,
        }
