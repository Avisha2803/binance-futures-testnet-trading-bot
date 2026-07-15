"""
Thin wrapper around the Binance USDT-M Futures Testnet REST API.

Uses plain `requests` calls (no paid API/service is used anywhere -
Binance Futures Testnet is a free paper-trading environment) so the
signing logic is fully visible and auditable.

Docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info
Demo Trading (testnet) REST base URL: https://demo-fapi.binance.com
(Binance retired the old standalone testnet.binancefuture.com website in
August 2025 and folded this functionality into "Demo Trading" on the main
Binance account.)
"""

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot")


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx / error-coded response."""


class BinanceNetworkError(Exception):
    """Raised when the request could not reach Binance at all."""


class BinanceFuturesClient:
    """Minimal signed REST client for Binance USDT-M Futures Testnet."""

    def __init__(self, api_key: str, api_secret: str,
                 base_url: str = "https://demo-fapi.binance.com",
                 timeout: int = 10):
        if not api_key or not api_secret:
            raise ValueError("API key and secret are required.")
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # ------------------------------------------------------------------ #
    # Low-level request helpers
    # ------------------------------------------------------------------ #
    def _sign(self, params: dict) -> str:
        query = urlencode(params)
        signature = hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{query}&signature={signature}"

    def _signed_request(self, method: str, path: str, params: dict = None) -> dict:
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        params.setdefault("recvWindow", 5000)

        url = f"{self.base_url}{path}"
        signed_query = self._sign(params)
        full_url = f"{url}?{signed_query}"

        logger.debug("REQUEST %s %s | params=%s", method, path, {k: v for k, v in params.items()})

        try:
            response = self.session.request(method, full_url, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("NETWORK ERROR on %s %s: %s", method, path, exc)
            raise BinanceNetworkError(f"Network error while calling {path}: {exc}") from exc

        logger.debug("RESPONSE %s %s | status=%s body=%s", method, path, response.status_code, response.text)

        try:
            data = response.json()
        except ValueError:
            logger.error("Non-JSON response from %s %s: %s", method, path, response.text)
            raise BinanceAPIError(f"Non-JSON response from {path}: {response.text[:200]}")

        if response.status_code != 200:
            code = data.get("code")
            msg = data.get("msg", response.text)
            logger.error("API ERROR %s %s | code=%s msg=%s", method, path, code, msg)
            raise BinanceAPIError(f"Binance API error (code={code}): {msg}")

        return data

    def _public_request(self, method: str, path: str, params: dict = None) -> dict:
        params = params or {}
        url = f"{self.base_url}{path}"
        logger.debug("REQUEST %s %s | params=%s", method, path, params)
        try:
            response = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("NETWORK ERROR on %s %s: %s", method, path, exc)
            raise BinanceNetworkError(f"Network error while calling {path}: {exc}") from exc

        logger.debug("RESPONSE %s %s | status=%s body=%s", method, path, response.status_code, response.text)

        try:
            data = response.json()
        except ValueError:
            raise BinanceAPIError(f"Non-JSON response from {path}: {response.text[:200]}")

        if response.status_code != 200:
            code = data.get("code")
            msg = data.get("msg", response.text)
            logger.error("API ERROR %s %s | code=%s msg=%s", method, path, code, msg)
            raise BinanceAPIError(f"Binance API error (code={code}): {msg}")

        return data

    # ------------------------------------------------------------------ #
    # Public endpoints
    # ------------------------------------------------------------------ #
    def ping(self) -> dict:
        return self._public_request("GET", "/fapi/v1/ping")

    def get_symbol_price(self, symbol: str) -> float:
        data = self._public_request("GET", "/fapi/v1/ticker/price", {"symbol": symbol})
        return float(data["price"])

    def get_exchange_info_symbol(self, symbol: str) -> dict:
        """Return exchange info for a single symbol (used to validate it exists)."""
        data = self._public_request("GET", "/fapi/v1/exchangeInfo")
        for s in data.get("symbols", []):
            if s.get("symbol") == symbol:
                return s
        raise BinanceAPIError(f"Symbol '{symbol}' not found on Binance Futures Testnet.")

    # ------------------------------------------------------------------ #
    # Trading endpoints (signed)
    # ------------------------------------------------------------------ #
    def place_order(self, **kwargs) -> dict:
        """
        Place an order. kwargs are passed straight through as query params,
        e.g. symbol, side, type, quantity, price, timeInForce, stopPrice.
        """
        return self._signed_request("POST", "/fapi/v1/order", kwargs)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._signed_request("GET", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id})

    def get_account_balance(self) -> dict:
        return self._signed_request("GET", "/fapi/v2/balance")
