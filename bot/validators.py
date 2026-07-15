"""
Input validation helpers for the trading bot CLI.

Raising ValueError with a clear message on invalid input; the CLI layer
catches these and prints a friendly error instead of a stack trace.
"""

import re

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}

# Loose symbol check: 2-15 char base asset + literal USDT suffix (USDT-M futures pairs).
SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,15}USDT$")


def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValueError("Symbol is required (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if not SYMBOL_RE.match(symbol):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Expected a USDT-margined pair like 'BTCUSDT' or 'ETHUSDT'."
        )
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValueError("Side is required (BUY or SELL).")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValueError("Order type is required (MARKET, LIMIT, or STOP_LIMIT).")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be a number, got '{quantity}'.")
    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than 0, got {quantity}.")
    return quantity


def validate_price(price, order_type: str):
    """Price is required for LIMIT and STOP_LIMIT orders, ignored for MARKET."""
    if order_type == "MARKET":
        return None
    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Price must be a number, got '{price}'.")
    if price <= 0:
        raise ValueError(f"Price must be greater than 0, got {price}.")
    return price


def validate_stop_price(stop_price, order_type: str):
    """Stop price is required only for STOP_LIMIT orders."""
    if order_type != "STOP_LIMIT":
        return None
    if stop_price is None:
        raise ValueError("Stop price (--stop-price) is required for STOP_LIMIT orders.")
    try:
        stop_price = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Stop price must be a number, got '{stop_price}'.")
    if stop_price <= 0:
        raise ValueError(f"Stop price must be greater than 0, got {stop_price}.")
    return stop_price
