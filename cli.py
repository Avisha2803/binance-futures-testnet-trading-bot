#!/usr/bin/env python3
"""
CLI entry point for the Binance USDT-M Futures Testnet trading bot.

Examples
--------
Market order:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

Limit order:
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000

Stop-limit order (bonus):
    python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 \\
        --price 60000 --stop-price 60500

Credentials can be passed via --api-key/--api-secret, or (preferred) via the
BINANCE_TESTNET_API_KEY / BINANCE_TESTNET_API_SECRET environment variables.
"""

import argparse
import os
import sys

from bot.client import BinanceFuturesClient, BinanceAPIError, BinanceNetworkError
from bot.orders import OrderManager
from bot.logging_config import setup_logger
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

TESTNET_BASE_URL = "https://demo-fapi.binance.com"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET / LIMIT / STOP_LIMIT orders on Binance USDT-M Futures Testnet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument("--type", dest="order_type", required=True,
                         help="MARKET, LIMIT, or STOP_LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", default=None, help="Required for LIMIT / STOP_LIMIT orders")
    parser.add_argument("--stop-price", dest="stop_price", default=None,
                         help="Required for STOP_LIMIT orders (trigger price)")
    parser.add_argument("--api-key", default=os.getenv("BINANCE_TESTNET_API_KEY"),
                         help="Binance Testnet API key (or set BINANCE_TESTNET_API_KEY env var)")
    parser.add_argument("--api-secret", default=os.getenv("BINANCE_TESTNET_API_SECRET"),
                         help="Binance Testnet API secret (or set BINANCE_TESTNET_API_SECRET env var)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Validate and print the request without calling the API")
    return parser


def main(argv=None) -> int:
    logger = setup_logger()
    parser = build_parser()
    args = parser.parse_args(argv)

    # ---- Validate input -------------------------------------------------
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        logger.error("Input validation failed: %s", exc)
        print(f"\n[INVALID INPUT] {exc}\n")
        return 2

    print("\n=== Order Request Summary ===")
    print(f"  Symbol      : {symbol}")
    print(f"  Side        : {side}")
    print(f"  Type        : {order_type}")
    print(f"  Quantity    : {quantity}")
    if price is not None:
        print(f"  Price       : {price}")
    if stop_price is not None:
        print(f"  Stop Price  : {stop_price}")
    print("==============================\n")

    if args.dry_run:
        print("[DRY RUN] Request validated successfully. No order was sent.\n")
        return 0

    if not args.api_key or not args.api_secret:
        msg = ("Missing API credentials. Pass --api-key/--api-secret or set "
               "BINANCE_TESTNET_API_KEY / BINANCE_TESTNET_API_SECRET.")
        logger.error(msg)
        print(f"[CONFIG ERROR] {msg}")
        return 2

    # ---- Call the API -----------------------------------------------------
    try:
        client = BinanceFuturesClient(args.api_key, args.api_secret, base_url=TESTNET_BASE_URL)
        manager = OrderManager(client)
        result = manager.place_order(
            symbol=symbol, side=side, order_type=order_type,
            quantity=quantity, price=price, stop_price=stop_price,
        )
    except BinanceAPIError as exc:
        print(f"\n[ORDER FAILED] Binance rejected the order: {exc}\n")
        return 1
    except BinanceNetworkError as exc:
        print(f"\n[ORDER FAILED] Network error reaching Binance: {exc}\n")
        return 1
    except Exception as exc:  # last-resort catch-all so the CLI never crashes ugly
        logger.exception("Unexpected error while placing order")
        print(f"\n[UNEXPECTED ERROR] {exc}\n")
        return 1

    # ---- Print response ---------------------------------------------------
    print("=== Order Response ===")
    print(f"  Order ID     : {result['orderId']}")
    print(f"  Status       : {result['status']}")
    print(f"  Symbol       : {result['symbol']}")
    print(f"  Side         : {result['side']}")
    print(f"  Type         : {result['type']}")
    print(f"  Orig Qty     : {result['origQty']}")
    print(f"  Executed Qty : {result['executedQty']}")
    print(f"  Avg Price    : {result['avgPrice']}")
    print("=======================\n")
    print("[SUCCESS] Order placed successfully.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
