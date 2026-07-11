# OKX Futures Config Reference

Full `config-okx.json` for FreqTrade OKX isolated futures trading with proxy.

## Complete Config Template

```json
{
    "max_open_trades": 3,
    "stake_currency": "USDT",
    "stake_amount": "unlimited",
    "tradable_balance_ratio": 0.99,
    "dry_run": true,
    "dry_run_wallet": 1000,
    "timeframe": "5m",
    "fiat_display_currency": "USD",
    "trading_mode": "futures",
    "margin_mode": "isolated",
    "exchange": {
        "name": "okx",
        "key": "你的OKX_API_KEY",
        "secret": "你的OKX_SECRET_KEY",
        "password": "你的OKX_API密码(Passphrase)",
        "ccxt_config": {
            "httpProxy": "http://127.0.0.1:7890"
        },
        "pair_whitelist": [
            "BTC/USDT:USDT",
            "ETH/USDT:USDT"
        ]
    },
    "pairlists": [
        {"method": "StaticPairList"}
    ],
    "entry_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1,
        "check_depth_of_market": {
            "enabled": false,
            "bids_to_ask_delta": 1
        }
    },
    "exit_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1
    },
    "bot_name": "okx_futures_bot",
    "initial_state": "stopped",
    "force_entry_enable": true,
    "internals": {
        "process_throttle_secs": 5
    },
    "api_server": {
        "enabled": true,
        "listen_ip_address": "127.0.0.1",
        "listen_port": 8080,
        "username": "admin",
        "password": "请修改密码"
    },
    "telegram": {
        "enabled": false,
        "token": "",
        "chat_id": ""
    }
}
```

## Key Fields Explained

| Field | Value | Note |
|-------|-------|------|
| `trading_mode` | `"futures"` | Enables futures trading on OKX |
| `margin_mode` | `"isolated"` | Isolated margin (risk per position). Use `"cross"` for cross-margin. |
| `exchange.name` | `"okx"` | OKX exchange identifier |
| `exchange.password` | Passphrase | OKX requires API passphrase (created when generating API key) |
| `ccxt_config.httpProxy` | proxy URL | Required if behind GFW |
| `dry_run` | `true` | Start in dry-run mode; set `false` for live trading |
| `pair_whitelist` | pairs with `:USDT` suffix | Futures pairs use `BASE/QUOTE:SETTLEMENT` format, e.g. `BTC/USDT:USDT` |

## Getting OKX API Credentials

1. Go to https://www.okx.com/account/my-api
2. Create API key with **Trade** permission
3. Set a **Passphrase** (this is `password` in config)
4. IP-restrict to your server IP for security
5. Copy the **API Key** (`key`) and **Secret Key** (`secret`)

## OKX Pair Naming (Futures vs Spot)

- Spot: `BTC/USDT`
- Futures (USDT-margined): `BTC/USDT:USDT`
- Futures (USD-margined): `BTC/USD:BTC`
