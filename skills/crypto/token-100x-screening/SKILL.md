---
name: token-100x-screening
description: 用户钦定的"找100倍币"11项二值评分系统（满分11分，<6分不进榜），含数据源映射(DexScreener/RugCheck/Bubblemaps/GMGN/TweetScout)与EIP-1167地址识别。已集成进链上日报cron(fa0df7d27b24)。与meme-coin-scoring(0~100复合分)互补：本技能是快速二值清单，meme-coin-scoring是加权深评。
category: crypto
---

# 代币100倍筛选 — 11项评分系统

## 触发条件
- 用户要求对代币做"100倍筛选" / "11项检查" / 快速质量清单评估
- 日报 cron (fa0df7d27b24) 阶段5：对优质标的候选执行 11 项评分
- 与 `meme-coin-scoring`（0~100分复合评分）互补使用：本技能快筛，那个深评

## 11项评分（用户钦定 2026-08，满分11分）

**每项"是"=1分 / "否"=0分。`<6分不进优质标的榜`。** 输出行：`✅ 11项检查: X/11 ❌[失分项]`（全过写"全过"）。

| # | 问题 | 数据源 |
|---|------|--------|
| 1 | 流动性池 >$30K? | DexScreener (liquidity.usd) |
| 2 | 流动性已锁定/销毁? | RugCheck / GMGN locked_ratio |
| 3 | 铸币权限已关闭? | RugCheck / GMGN mint authority |
| 4 | 冻结权限已关闭? | RugCheck / GMGN freeze authority |
| 5 | Top10 持供应量 <20%? | GMGN top_10_holder_rate / Bubblemaps |
| 6 | 钱包无关联、分布干净? | GMGN bundler_rate / Bubblemaps |
| 7 | dev 无发币弃盘史? | GMGN dev.creator_open_count / creator_token_status |
| 8 | 社交账户 >1周历史? | GMGN link.twitter / TweetScout |
| 9 | 粉丝真实、无机器人刷量? | TweetScout / GMGN twitter 数据 |
| 10 | 持有者 24h 内增加? | GMGN holder 趋势 / DexScreener |
| 11 | 日交易量 ≥ 流动性/2? | DexScreener volume vs liquidity |
| 12 | **别问别人，问自己** | 主观综合判断，不依赖工具 |

## 数据获取优先级

- GMGN `gmgn-cli token info --chain <c> --address <CA> --raw` 覆盖：3/4（EVM 上 owner_renounced 常为 null → 标"存疑"）、5/6/7/8/9/10
- DexScreener：`HTTPS_PROXY=http://127.0.0.1:7890 curl -s "https://api.dexscreener.com/latest/dex/tokens/{CA}"` 覆盖 1/11
- RugCheck：`curl -s "https://api.rugcheck.xyz/v1/tokens/{CA}/report"` 覆盖 2/3/4（Solana）
- 工具拿不到的项按已有数据合理推断并标注"存疑"

## 一次性算完：用 trenches 批量打分（别再逐币调 token info）

```
gmgn-cli market trenches --chain <c> \
  --type new_creation --type near_completion --type completed \
  --limit 40 --raw
```

**一个调用就带齐 9/11 项所需字段**：LP / holder_count / volume_24h / top_10_holder_rate /
bundler_trader_amount_rate / entrapment_ratio / creator_created_count / created_timestamp /
is_honeypot / burn_status / twitter + x_user_follower / buy_tax + sell_tax。

脚本：`~/.hermes/scripts/daily_scan.py`（打分 + 硬门槛 + 同名去重，输出 ~30 行给 agent）。
**脚本算出的「11项 X/11」就是结论，不要复算**——逐币重算会得到不同数字，日报里两处互相打脸
（脚本输出里已带「以此为准,勿复算」）。

## 硬门槛必须前置（否则榜单不可用）

| 条件 | 阈值 | 原因 |
|---|---|---|
| LP | **≥ $10K** | SOL 未迁移盘 LP 天然很小（$0-28K），用 $30K 会把全部新盘杀掉 |
| Top10 | ≤ 50% | 超过即控盘 |
| 围猎盘 entrapment | ≤ 30% | 高 = 老鼠仓等出货 |
| bundle | ≤ 40% | |
| 持币 | ≥ 200 | 几百持币却 $1M MC = 假盘 |
| 24h 量 | ≥ $50K | 无量 = 没人接 |

实测淘汰率 95%+（BSC 172/180、SOL 174/180）。**无门槛时 SOL 一次吐出 102 个「过线」，加门槛后只剩 1-3 个。**
另：同名仿盘极多（同 symbol 多个 CA）→ **按 symbol 去重，只留评分最高的那个**。

## 字段陷阱（直接导致 #2/#6 判错）

- `is_honeypot` / `burn_status` 是**字符串** `"no"` / `"yes"`，不是 0/1 —— 按布尔判断会把**所有干净盘误标成蜜罐**（曾整榜误判）
- `locked_ratio=0` **不等于 LP 未锁**：PancakeSwap 永久锁定的盘也可能报 0，需交叉官方公告/协议说明
- `top_10_holder_rate` 可能为 0 或缺失（非标准合约），不能据此推断「极分散」
- `token holders` 对非标准合约返回 `{"list":[]}` 空列表而 `holder_count` 非零 → 换 GoPlus `token_security/56`，或放弃持仓分析
- `dev.creator_open_count` 对**平台批量部署地址**虚高（实测 124 / 2067 次），先判断是不是平台部署器，别直接当「连环发币」

## 实测教训

### 龙宫（BSC 0x7dad85...，2026-08）→ 4/11，不碰
- 过：#5（Top10 14.5%）/#6（bundle 0.95%）/#7（dev 已抛 creator_close）/#11（量/LP 18.9x）
- 挂：#1（LP 仅$2.3K）/#2（locked_ratio=0）/#8#9（无真实社交，仅抖音链接）/#10（买卖持平 418/405）
- **⚠️ 量/LP 比极高但 LP<$3K 不是健康信号** — 未毕业发射台（flap progress 8%）换手博弈
- KOL 带 `wash_trader` 标签 = 对倒嫌疑，不能当正面信号
- dev 已抛光（creator_close）+ 无真实社区 = 不碰

## 地址识别：先确认是钱包还是合约

GMGN 三链（eth/bsc/base）全空时，别急着报"空地址"——用 RPC POST（带代理）验证：
```bash
# 余额 / 交易数 / 是否有合约代码
curl -s -X POST https://bsc-dataseed.binance.org -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["<ADDR>","latest"],"id":1}'
```
- `eth_getCode` 返回 `0x` = EOA 钱包（真空）；返回长代码 = **合约**
- **EIP-1167 minimal proxy** 特征：代码以 `363d3d373d3d3d363d73...` 开头（clone 工厂部署），需查实现合约 `0x024f...` 段才知道是什么项目
- 场景：某 0x 地址在 BSC 有代码+1笔交易但 GMGN 无记录 → 是代理合约实例（PancakeSwap position/vault 等），不是可分析的钱包

## 相关技能
- `meme-coin-scoring` — 0~100分加权复合评分（部署者/聪明钱/健康度/活跃度），本技能的深评版
- `onchain-meme-analysis` — 全链打狗分析总流程（GMGN+DexScreener+Twitter）
- `gmgn-token` — GMGN token 命令参考
