# OKX Agent Identity Registration — XLayer Fix

When using `onchainos agent create --role user --name "..."` on XLayer, the error:

```
transaction simulation failed: origin error
```

Usually means the wallet has **zero balance on XLayer** (even though XLayer is gas-free, a simulation check may fail with no balance).

## Fix

1. Deposit at least minimal funds to XLayer chain (USDT or OKB):
   - Use the XLayer address from `onchainos wallet addresses`
   - Deposit from OKX exchange or other wallet via XLayer chain
   - Even $1 USDC is enough

2. If funds are on BSC/ETH but no native token for gas:
   - BSC needs BNB for gas → deposit small BNB (~$0.3 worth)
   - Can then use `onchainos wallet send` to bridge to XLayer or use OKX bridge

3. Verify balance before retrying:
   ```bash
   onchainos wallet balance --chain xlayer
   ```

## Alternative: Direct XLayer Deposit

Simplest: go to OKX exchange and withdraw directly to XLayer chain:
- Chain: XLayer (OKB Chain)
- Address: `0x...` (from `onchainos wallet addresses` → `xlayer` section)
- Token: USDT or OKB
- Amount: minimal ($1-2 enough)

## BSC Gas Workaround (Native Token Needed)

If USDC is stuck on BSC with no BNB for gas:
- **Gas cost** for USDC transfer on BSC: ~0.00007 BNB ≈ $0.04 (at $565/BNB)
- Deposit just 0.001 BNB (~$0.56) to the BSC address — enough for 10+ transfers
- BSC address is the same EVM address: `0x...`
- After BNB arrives, use `wallet send` to transfer USDC or use the OKX DEX bridge
- **Cross-chain bridge from BSC to XLayer:** Meson (bridgeId 223) supports both chains. Use `onchainos cross-chain execute --from-chain bsc --to-chain xlayer` with appropriate token addresses.

## OpenRouter Fake Key Warning

The user was sold an OpenRouter API key (`sk-or-v1-...`) that appeared valid during API testing (338 models available) but was later deemed unreliable/scam. If a user reports similar:
- Test connectivity first with a simple `/v1/models` API call
- If the user says it's a scam, revert config to DeepSeek immediately
- Clean up the key from `.env` to avoid confusion
