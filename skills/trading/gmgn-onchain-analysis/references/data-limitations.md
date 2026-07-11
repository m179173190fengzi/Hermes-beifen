# GMGN / Crypto Data Limitations

## CME Futures Data

**GMGN does NOT provide CME (Chicago Mercantile Exchange) futures data.** GMGN is an on-chain data platform — it tracks token smart contracts, wallet activity, DEX prices, and blockchain transactions. It has no access to traditional finance markets.

If the user asks about CME futures data (e.g. "CME比特币期货"), the correct response is:
- "GMGN 是链上数据分析平台，不包含CME期货数据"
- The user will accept this explanation

**Alternative data sources for CME futures:**
- TradingView (web-based, no API needed for manual checks)
- CoinGlass (coinglass.com) — shows CME open interest and funding rates
- The Block's data dashboard

## Xiaomi BE3600 OpenWrt Status

The Xiaomi BE3600 (Qualcomm IPQ5312/IPQ5018) is NOT listed in ImmortalWrt firmware-selector, but **it CAN be flashed** with custom firmware from Chinese developers. The user has confirmed this from their own research.

Available options (Chinese forums):
- QSDK-based custom firmware (Qualcomm's SDK, not upstream OpenWrt) — actively developed
- Xiaomi GPL source code releases — Chinese devs build from these
- Modified firmware shared on koolshare.cn / right.com.cn

**How to check:**
1. ImmortalWrt firmware-selector → search model name or `xiaomi,ra69`
2. If not found → DOES NOT MEAN unsupported. Chinese devs use custom kernels not upstreamed yet.
3. Check koolshare.cn / right.com.cn for BE3600 threads
4. Router firmware is often shared via Baidu Pan / Lanzou links on Chinese forums

**Xiaomi/Redmi routers that ARE in ImmortalWrt firmware-selector (recommended for guaranteed support):**
- Redmi AX6 (RA76) — IPQ8071A, 512MB RAM, ¥150 used, wifi6
- Xiaomi AX3600 — IPQ8071A, 512MB RAM, ¥150-200 used
- Xiaomi AX3000T (RA81) — MT7981B, 256MB RAM, ¥80 new
- Redmi AC2100 (RM2100) — MT7621A, 128MB RAM, ¥50-80 used (most community support)
- Xiaomi Router 3G (R3G) — MT7621A, 256MB RAM, ¥30-50 used (classic budget pick)
- Xiaomi Router 4A Gigabit Edition (R4A) — MT7621A, 128MB RAM, ¥40-60 used

**Key learning:** When a user says a specific router model "可以刷" (can be flashed), trust their local knowledge over the official firmware database. Chinese router modding community moves faster than upstream OpenWrt.
