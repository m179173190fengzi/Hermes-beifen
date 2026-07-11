# OKX Futures Config for FreqTrade

## Config JSON (`config-okx.json`)

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
        "key": "YOUR_API_KEY",
        "secret": "YOUR_SECRET_KEY",
        "password": "YOUR_API_PASSPHRASE",
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
        "order_book_top": 1
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
        "password": "CHANGE_ME",
        "jwt_secret_key": "Your32PlusCharSecretKeyHere!!"
    },
    "telegram": {
        "enabled": false,
        "token": "",
        "chat_id": ""
    }
}
```

## Key differences from spot config

| Setting | Spot | Futures |
|---------|------|---------|
| `trading_mode` | `"spot"` | `"futures"` |
| `margin_mode` | (not used) | `"isolated"` or `"cross"` |
| Pair format | `"BTC/USDT"` | `"BTC/USDT:USDT"` |
| `can_short` in strategy | N/A | `True` |

## Important notes

- OKX requires **Passphrase** (API password) — set when creating API key on OKX
- Always start with `dry_run: true` and test for at least a week
- Isolated margin (`isolated`) limits risk per-position vs cross margin
- Strategy must set `can_short = True` for futures trading
