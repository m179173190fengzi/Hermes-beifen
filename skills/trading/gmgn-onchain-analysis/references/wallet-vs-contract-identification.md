# Wallet vs Contract Identification (0x 地址鉴定)

Field-proven 2026-08-21: user sent `0xce6c5bc0d0ce2a7835cda9113a38b8f496337777` — GMGN showed empty on all three EVM chains, but the address turned out to be an EIP-1167 minimal proxy contract on BSC, not a wallet.

## When to Use

User supplies a `0x` address (or you encounter one) and GMGN `portfolio holdings`/`stats`/`activity` return all-empty on eth/bsc/base. **Do NOT conclude "empty wallet"** — verify whether the address is even a wallet first.

## Step 1: GMGN three-chain sweep

```bash
W=0x<address>
for C in eth bsc base; do
  HTTPS_PROXY=http://127.0.0.1:7890 gmgn-cli portfolio holdings --chain $C --wallet $W --limit 20
  HTTPS_PROXY=http://127.0.0.1:7890 gmgn-cli portfolio stats --chain $C --wallet $W
done
```

All three return empty lists / zeroed stats → continue to RPC verification.

## Step 2: Public RPC verification (bypasses Etherscan/BscScan Cloudflare)

Etherscan/BscScan pages are Cloudflare-protected (browser gets "正在进行安全验证" challenge). Public RPCs work directly. Always prefix with `HTTPS_PROXY=http://127.0.0.1:7890`.

```bash
# 1. Native balance
curl -s --max-time 20 -X POST https://bsc-dataseed.binance.org -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["'$W'","latest"],"id":1}'
# 2. Transaction count (0x0 = never transacted)
curl -s --max-time 20 -X POST https://bsc-dataseed.binance.org -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["'$W'","latest"],"id":1}'
# 3. Contract code — THE decisive check
curl -s --max-time 20 -X POST https://bsc-dataseed.binance.org -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["'$W'","latest"],"id":1}'
```

### RPC endpoints (tested)

| Chain | Endpoint | Notes |
|-------|----------|-------|
| BSC | `https://bsc-dataseed.binance.org` | Reliable |
| ETH | `https://ethereum-rpc.publicnode.com` | Reliable |
| ETH | `https://cloudflare-eth.com` | Sometimes `Internal error` (-32603) — switch endpoint |
| ETH | `https://eth.llamarpc.com` | Sometimes error code 521 |

## Step 3: Interpretation

- `eth_getCode` returns non-`0x` (actual bytecode) → **it's a CONTRACT, not a wallet**.
- Bytecode starts with `0x363d3d373d3d3d363d73` → **EIP-1167 minimal proxy (clone contract)**. The 20 bytes after `73` (PUSH20) are the **implementation contract address** — query that to identify the project (PancakeSwap-style position/vault contracts, clone factory deployments).
- All-zero results (`0x0` balance, `0x0` tx count, `0x` code) → genuinely empty address (fresh wallet / typo'd address).
- ETH empty + BSC has 1 tx + has code → classic factory-deployed clone instance; report as contract, don't try to analyze it as a wallet.

## Step 4: onchainos deep-lookup (optional)

`onchainos portfolio total-value --address $W --chains "xlayer,ethereum,base,bsc"` errors with `50114 Invalid Authority` = not logged in. Fix:
```bash
onchainos wallet login <email>   # or set OKX_API_KEY / OKX_SECRET_KEY / OKX_PASSPHRASE env vars
```

## Output

Tell the user directly: "这不是钱包，是 {chain} 上的合约（EIP-1167 代理，实现合约 0x...）" — do NOT present an empty-wallet holdings table.
