# Binance Futures Testnet Trading Bot

A small, structured Python CLI application for placing **MARKET**, **LIMIT**,
and (bonus) **STOP_LIMIT** orders on **Binance USDT-M Futures Testnet** —
a free paper-trading environment. No paid API, service, or library is used
anywhere in this project; the only third-party dependency is `requests`.

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Signed REST client for Binance Futures Testnet
│   ├── orders.py          # Builds order payloads, calls client, normalizes response
│   ├── validators.py      # CLI input validation
│   └── logging_config.py  # Rotating file + console logging setup
├── tests/
│   ├── test_validators.py
│   └── test_orders.py     # Uses mocked client — no network required
├── cli.py                 # CLI entry point (argparse)
├── demo_mock_run.py        # Optional: generates example logs w/o network (see below)
├── sample_logs/            # Example log output from demo_mock_run.py
├── logs/                   # Real logs land here at runtime (trading_bot.log)
├── requirements.txt
└── README.md
```

## 1. Setup

### 1.1 Binance Futures Testnet ("Demo Trading") account (free)

> **Note:** Binance retired the old standalone `testnet.binancefuture.com`
> website in August 2025 and folded this functionality into **Demo Trading**
> on the regular Binance account. The steps below reflect the current flow.

1. Go to https://demo.binance.com/futures and log in with your normal
   Binance account (or on binance.com: **More → Demo Trading**). No KYC or
   real funds are required for Demo Trading.
2. While inside Demo Trading, click your **Account icon (top right) →
   API Management**, then **Create API** and name it. This generates a
   demo-only **API Key** and **API Secret**, separate from any live
   trading key on your account. Copy the secret immediately — it's shown
   only once.
3. Demo Trading auto-allocates virtual USDT to your futures demo account
   so you can place orders straight away (resettable from **Assets**).

### 1.2 Local environment

```bash
# clone / unzip the project, then:
cd trading_bot
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1.3 Provide your credentials

Preferred (keeps keys out of shell history):

```bash
export BINANCE_TESTNET_API_KEY="your_key_here"
export BINANCE_TESTNET_API_SECRET="your_secret_here"
```

Or pass them per-command with `--api-key` / `--api-secret` (shown below).

## 2. Running it

### Validate input only, no API call (`--dry-run`)

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
```

### Place a MARKET order

```bash
python cli.py \
  --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
python cli.py \
  --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000
```

### Place a STOP_LIMIT order (bonus order type)

```bash
python cli.py \
  --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 \
  --price 60000 --stop-price 60500
```

Every run prints:
- an **order request summary** (symbol, side, type, quantity, price)
- the **order response** (orderId, status, executedQty, avgPrice)
- a clear **success / failure** message

...and appends detailed request/response/error logs to `logs/trading_bot.log`.

### Passing keys inline instead of via env vars

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET \
  --symbol ETHUSDT --side BUY --type MARKET --quantity 0.1
```

## 3. Running the tests

Unit tests use a mocked API client, so they run instantly with no network
or credentials needed:

```bash
python -m unittest discover -s tests -v
```

## 4. About the log files in this submission

`logs/trading_bot.log` contains genuine request/response log entries from
real orders placed against Binance's Futures Demo Trading API
(`https://demo-fapi.binance.com`):

- **MARKET orders** — `BUY ETHUSDT 0.02` (orderId `13372588832`) and
  `BUY BTCUSDT 0.01` (orderId `21832872939`), both accepted by the API
  with `status: NEW` and confirmed `Filled` in the Demo Trading Order
  History with real average fill prices.
- **LIMIT order** — `SELL ETHUSDT 0.02 @ 2000` (orderId `13372793823`),
  accepted with `status: NEW` (placed above market price so it doesn't
  execute immediately — Binance still confirms acceptance and returns a
  real `orderId`, which is what the deliverable requires).

Each entry logs the full flow at DEBUG level: the signed request sent to
`/fapi/v1/order`, Binance's raw JSON response, and the bot's own
"Order ACCEPTED" / "Order REJECTED" summary line, e.g.:

```
2026-07-15 10:55:41 | INFO  | trading_bot | Placing order | symbol=ETHUSDT side=BUY type=MARKET qty=0.02 ...
2026-07-15 10:55:42 | DEBUG | trading_bot | RESPONSE POST /fapi/v1/order | status=200 body={"orderId":13372588832,...}
2026-07-15 10:55:42 | INFO  | trading_bot | Order ACCEPTED | orderId=13372588832 status=NEW
```

Three real API errors were also hit and handled correctly along the way —
useful evidence the error-handling path works as intended, not just the
happy path:

- `-2019 Margin is insufficient` on two early BTCUSDT attempts (10:39–10:40) —
  resolved once leverage/margin type were confirmed on that symbol's
  trading page in the Binance UI.
- `-4164 Order's notional must be no smaller than 20` on an ETHUSDT
  MARKET order sized at 0.01 (worth <$20, below Binance's exchange-wide
  minimum order value) — resolved by increasing quantity to 0.02.

**Also included:** `sample_logs/example_log_mocked_demo.log`, produced by
`python demo_mock_run.py`, a small script that exercises the same
`OrderManager`/logging code path against a stubbed HTTP response instead of
a live call. It's kept for reference to show the logging shape in isolation,
but is not needed to evaluate correctness — the real logs in
`logs/trading_bot.log` are the primary evidence for this submission.
a live call. It's kept for reference to show the logging shape in isolation,
but is not needed to evaluate correctness — the real logs in
`logs/trading_bot.log` are the primary evidence for this submission.

## 5. Error handling

- **Invalid input** (bad symbol, side, order type, non-numeric or ≤0
  quantity/price, missing price for LIMIT, missing stop-price for
  STOP_LIMIT) is caught by `bot/validators.py` and reported with a clear
  message and exit code `2`, without ever calling the API.
- **API errors** (e.g. insufficient margin, invalid symbol on Binance's
  side, bad signature) raise `BinanceAPIError` with Binance's own error
  code and message, logged and printed as `[ORDER FAILED]`.
- **Network errors** (timeouts, DNS failures, connection refused) raise
  `BinanceNetworkError` and are logged/printed distinctly from API
  errors, so the two failure modes are never confused.
- Any other unexpected exception is caught at the CLI's top level, logged
  with a full traceback (`logger.exception`), and printed as
  `[UNEXPECTED ERROR]` rather than crashing with a raw stack trace.

## 6. Assumptions

- **USDT-M Futures only** — symbols must end in `USDT` (e.g. `BTCUSDT`,
  `ETHUSDT`). Coin-margined futures and spot trading are out of scope.
- **LIMIT / STOP_LIMIT orders use `timeInForce=GTC`** (Good-Til-Canceled),
  a reasonable default since the task didn't specify one.
- **STOP_LIMIT is implemented as Binance's `STOP` order type** (limit
  price + trigger `stopPrice`), which is the closest built-in equivalent
  on Futures to a classic stop-limit order.
- **No exchange-specific quantity/price step-size (`LOT_SIZE`/`PRICE_FILTER`)
  rounding is applied** — the bot validates that quantity/price are
  positive numbers but does not auto-round to a symbol's tick size. In
  practice you should pick "round" values (e.g. `0.01`, `100.5`) or the
  Binance API will reject the order with a clear error, which the bot
  will surface to you.
- **Credentials are never logged.** Only request parameters (symbol,
  side, type, quantity, price, timestamp, etc.) and responses are logged;
  the API key/secret themselves are excluded from all log output.
- **This project only talks to `https://demo-fapi.binance.com`** (Binance's
  current Futures Demo Trading REST endpoint, formerly hosted at the now
  retired `testnet.binancefuture.com`). Nothing here is configured for, or
  intended for use against, Binance's live production API.

## 7. Bonus implemented

- **Third order type**: `STOP_LIMIT` (see section 2 and 6 above).
- Clear, validated CLI with a `--dry-run` mode for safely checking a
  command before it touches the API.
