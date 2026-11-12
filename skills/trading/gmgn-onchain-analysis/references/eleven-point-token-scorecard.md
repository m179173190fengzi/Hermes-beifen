# 11项打狗评分卡（用户原始方法论 + 数据源分工）

用户**本人定义**的过筛清单。每项"是"=1 分、"否"=0 分，**满分 11**。与 0-100 复合分、
AlphaTrader 六维分**并存**：复合分做深度评估，本卡做日报/监控的快速定级。

实测沿用门槛：**<6 分不进优质标的榜**；与 75 分制并用时构成双门槛（75分≥60 **且** 11项≥6）。

| # | 检查项 | 用户指定的数据源 |
|---|--------|------------------|
| 1 | 流动性池 > $30K | DexScreener |
| 2 | 流动性已锁定或销毁 | DexScreener |
| 3 | 铸币权限已关闭 | RugCheck |
| 4 | 冻结权限已关闭 | RugCheck |
| 5 | 前 10 钱包持币 < 20% | Bubblemaps |
| 6 | 钱包之间无关联、分布干净 | Bubblemaps |
| 7 | Dev 之前没发币然后抛弃 | GMGN |
| 8 | 社交账户 > 1 周历史 | TweetScout |
| 9 | 粉丝真实、无机器人刷量 | TweetScout |
| 10 | 持有者数过去 24h 增加 | DexScreener |
| 11 | 日成交量 ≥ 流动性 1/2 | DexScreener |
| 12 | **别问别人，问自己** | 不用工具，最后自我裁定 |

## 三条使用规则（不要自行改写）

1. **第 12 条不是评分项** —— 收尾原则：11 项工具打分之后必须自己下判断，不能把工具输出当结论。满分 **11**，不是 12。
2. **工具拿不到的项标"存疑"，不要默认记 0。** 报告里"存疑"与"否"必须可区分——默认 0 会把新盘系统性判死（新盘的社交历史、24h 持币增长天然拿不到数据）。
3. **外部工具可整体替换成 GMGN**：只有 GMGN 可用时 11 项全都能从 `token info` + `token security` 取到，
   逐项字段映射见本技能 SKILL.md 的「11项评分 GMGN 全量字段映射」条目，不必强依赖 DexScreener/RugCheck/TweetScout。

## 链特例（③④ 项最容易判错）

- **Solana**：`renounced_mint` / `renounced_freeze_account` 直接对应 ③ / ④。
- **EVM（BSC/Base/RH）**：无 freeze 概念 → **④ 计过**；无 `renounced_mint` → **③ 用 `is_renounced`（owner renounced）替代**。
- **BSC 第 5 项先剔除池合约**：`token holders` 的 Top1 常是 launchpad bonding-curve 池
  （`addr_type: 2` + `exchange: "flap"`，`buy_tx=0 sell_tx=0`）。实测某盘原始 Top1 占 **77.2%**，
  而 GMGN 自己的 `stat.top_10_holder_rate` 只报 **14.5%**（已剔除池子）——算 ⑤ 一律以
  `top_10_holder_rate` 为准，本地计算时显式排除 `addr_type == 2`，否则好盘会被误判成极端控盘。

## 合约安全接口（③④ 的可用实现，均无需 API key）

**GoPlus —— 新盘也能查，EVM 首选**：
```bash
# chainId: 56=BSC, 1=ETH, 8453=Base
HTTPS_PROXY=http://127.0.0.1:7890 curl -s --max-time 25 \
  "https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses=<CA>"
```
返回 `result["<CA>"]["<小写地址>"]` 下的扁平字段（`"1"`/`"0"` 字符串）：

| 字段 | 读法 |
|------|------|
| `is_honeypot` / `cannot_sell_all` / `cannot_buy` | 任一为 `1` → 直接放弃 |
| `hidden_owner` / `can_take_back_ownership` / `owner_change_balance` / `transfer_pausable` | 为 `1` → 放弃（后门/可暂停交易） |
| `is_blacklisted` / `is_whitelisted` | 为 `1` → 警告 |
| `is_mintable` | `1` → ③ 未关闭 |
| `owner_address` | `0x000…0` → 已弃权（③ 计过） |
| `buy_tax` / `sell_tax` | > 0.05 警告，> 0.10 放弃 |
| `creator_percent` | > 0.05 警告 |
| `is_open_source` | `1` = 已开源 |
| `holder_count` / `lp_holder_count` | 持币与 LP 持有者数 |
| `dex[]` | 每个池的 `name`/`liquidity`/`pair`（① 项另一来源） |

**honeypot.is —— 只对已建索引的老盘有效**：
```bash
HTTPS_PROXY=http://127.0.0.1:7890 curl -s --max-time 25 \
  "https://api.honeypot.is/v2/IsHoneypot?address=<CA>&chainID=56"
```
成熟币（实测 CAKE）返回完整模拟：`honeypotResult.isHoneypot` / `simulationResult.buyTax|sellTax` /
`summary.risk|riskLevel` / `holderAnalysis`。
⚠️ **新盘返回 `{"code":404,"error":"pair not found"}`**（pair 未被索引）——实测刚发行的 meme 币命中此情况。
**判据：新盘/刚毕业盘一律走 GoPlus，不要因 honeypot.is 报 404 就以为"无法检查"或判该币有问题。**

**DexScreener —— ①②⑪ 的原始来源，⑩ 拿不到**：
```bash
HTTPS_PROXY=http://127.0.0.1:7890 curl -s "https://api.dexscreener.com/latest/dex/tokens/<CA>"
```
取 `liquidity.usd`（①）、`volume`（⑪ 与 LP 比）。DexScreener 提供不了 24h 持币者增量 →
**⑩ 一律从 GMGN 的 `holder_count` 趋势 / 买卖笔数对比取**，或标"存疑"。
