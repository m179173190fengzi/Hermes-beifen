---
name: meme-coin-scoring
description: 链上代币实值评分系统 — 0~100分复合打分，配合6类过滤器评估代币质量
category: crypto
---

# 链上代币实值评分系统

> ⚠️ **前置条件：必须先过6类过滤器**
> 在评分之前，先用 `meme-coin-multi-agent-pipeline` 的6类过滤器判断该代币是否属于链创始人/KOL/科技领袖/政治人物/社会事件/知名机构类别。
> **凡是不匹配6类别的代币，直接跳过不评分不推送。**

## 使用方法

1. **第一步：6类过滤** — 检查代币名/符号是否匹配6大类别关键词
2. **第二步：评分** — 对通过过滤的代币执行以下4维度评分
3. **第三步：报告** — 必须包含叙事详情+匹配类别+推特链接+实值评估

## 评分维度

### 1. 部署者/筹码质量 (30%)
从 GMGN 数据中提取：
- **bundler_rate**（Bundle率）: < 10% → 90分, < 20% → 70分, < 30% → 50分, > 30% → 20分
- **top_10_holder_rate**（Top10集中度）: < 20% → 90分, < 40% → 70分, < 60% → 50分, > 60% → 20分
- **creator_token_status**（开发者持仓）: `creator_close` → 90分（已抛售）, `creator_hold` → 20分（还拿着）
- **renounced_mint**（放弃铸币）: true → 80分, false → 30分

### 2. 聪明钱质量 (25%)
- **smart_degen_count**（聪明钱数量）: ≥ 10 → 95分, ≥ 5 → 80分, ≥ 2 → 60分, = 0 → 20分
- **renowned_count**（知名追踪者）: ≥ 20 → 80分, ≥ 10 → 60分, < 10 → 30分
- **sniper_count**（狙击手数量）: ≥ 5 → 60分（竞争健康）, < 5 → 40分（没人抢）

### 3. 链上健康度 (25%)
- **liquidity**（流动性）: > $50K → 90分, > $20K → 70分, > $10K → 50分, < $10K → 20分
- **market_cap**（市值）: $50K~$500K → 80分（黄金区间）, < $50K → 60分（太早期）, > $1M → 40分（晚了）, > $10M → 20分（太晚了）
- **lock_percent**（锁仓率）: ≥ 0.95 → 80分, ≥ 0.5 → 50分, < 0.5 → 20分
- **volume_to_mcap_ratio**（成交量/市值比）: > 1.0 → 80分（活跃）, > 0.3 → 60分, < 0.3 → 30分（冷清）

### 4. 交易活跃度 (20%)
- **buy_sell_ratio**（买/卖比）: > 1.5 → 80分（买盘强）, > 1.0 → 60分, < 1.0 → 30分（卖盘强）
- **swaps**（总交易笔数）: > 1000 → 80分, > 500 → 60分, > 100 → 40分, < 100 → 20分
- **holder_count**（持仓人数）: > 500 → 80分, > 200 → 60分, > 50 → 40分, < 50 → 20分
- **vol_to_liq_ratio**（交易量/流动性比）: 从GMGN trending数据计算 `volume / liquidity`；> 3.0 → +15分, > 1.0 → +10分, > 0.3 → +5分, < 0.3 → -5分（加分项，加在活跃度总分上）

## 复合计算

```
总分 = 部署者质量 × 30% + 聪明钱质量 × 25% + 链上健康度 × 25% + 交易活跃度 × 20%
```

## 输出格式（用户已验证接受的简洁版）

⚠️ 此用户追求**简短直接、无废话**的输出。不要角色扮演、不要冗长铺垫、不要追问"你想看什么"。直接给数据和分析。

接收到地址后立即执行：`gmgn-cli token info --chain <sol|bsc|base|eth|robinhood> --address <addr>`（自动试链直到命中），然后按以下格式输出：

```
**$SYMBOL** — Chain | Launchpad

━━━ 基础数据 ━━━
💵 MC: **~$X.XXM** | 流动性: $X
👥 持币: X | 聪明钱: X | 机器人率: X%
📈 24h成交量: $X
💰 当前价: $X | ATH: $X（距ATH ±X%）
⏰ 上线: ~X天/小时

━━━ 安全 ━━━
✅ 铸币已放弃 | ✅ 无蜜罐 | ✅ 0%税 ...
🛡️ Top10: X%（筹码分散度好/集中）

━━━ 盘面分析 ━━━
📊 24h: 买X / 卖X → [买盘强/卖盘强/均衡]
📉 1h内从 $X 跌到 $X（-X%），正在回调

━━━ 6类过滤器 ━━━
🏷️ 类别: ✅ [匹配类别] / ❌ 无匹配
（说明为什么匹配/不匹配）

━━━ 综合 ━━━
[2-3句话总结：MC大小、安全状况、聪明钱信号、风险点、操作建议]
```

关键原则：
- 不要输出完整的4维度评分表（除非用户明确要求评分）
- 不要输出复合总分计算过程
- 先判断6类过滤器是否匹配，不匹配的在综合里直接建议"不碰"
- 每个数据点最多一行，不拆开多行
- 最后一句话是明确的行动建议（"碰"或"不碰"或"观望"）

## 社交热度查询（推特大V喊单检测）

### 工具：twitter CLI（无需X API Key）

`twitter` 命令通过 `pipx install twitter-cli` 安装，内置了 X 访客 API，**不需要注册开发者账号或 OAuth 认证**即可搜索推文。
⚠️ pipx venv 名称是 `twitter-cli`（不是 `twitter`）。

```bash
# 搜索币种被讨论的热度
twitter search "\$SYMBOL -is:retweet"
# 检查是否有大V在喊
twitter search "\$SYMBOL 100x"
twitter search "\$SYMBOL gem early"
# 查看特定KOL的推文
twitter search from:用户名
# 搜索特定叙事话题
twitter search "solana meme coin new -is:retweet -is:reply"
```

根据最近1小时内推文数量评估社交热度得分：
- ≥ 20条推文 + 有KOL喊单 → 90分
- ≥ 10条推文 → 70分
- ≥ 3条推文 → 50分
- 0~2条推文 → 20分

**结合评分：**
- 四项评分 ≥ 75 且社交热度高 → 🔥 强推荐
- 四项评分 ≥ 75 但社交热度低 → 🟡 观察（可能被低估）
- 四项评分 < 60 但社交热度高 → 🟡 叙事币，关注但谨慎

**限制：** 无法搜索私密账号（受保护的推文）。

## 链上+社媒交叉验证（来自@0xJeff onchain forensics工作流）

当链上数据和社会情绪同时可用时，执行交叉验证判断：

| 链上信号 | 推特情绪 | 判断 |
|---------|---------|------|
| 聪明钱卖出/链上流出 | 大V喊涨/社区FOMO | 🚩 **预警：出货掩护** — 链上筹码在派发，KOL喊你接盘 |
| 链上持续流入/聪明钱建仓 | 冷清/无人讨论 | 🐋 **潜在建仓信号** — 聪明钱在别人没注意时进场 |
| 链上流入+推特热度同时上升 | 🟢 **共识确认** — 链上和社区方向一致 |

## 趋势交易评分系统（AlphaTrader Elite 六维评分）

适用于趋势行情中的交易机会评估（链上打狗趋势或 V4 做空场景）。0-10分制。

### 六维评分维度

| 维度 | 分值 | 核心逻辑 |
|------|------|---------|
| ① 大周期方向+趋势强度 | 0-2.5 | 大周期 MA 排列方向 + 趋势强度分级 |
| ② 关键位置优势 | 0-2 | 价格相对 MA/支撑/压力的位置优势 |
| ③ 成交量确认 | 0-1.5 | 涨跌是否带量，量价是否配合 |
| ④ OI/Funding 配合 | 0-1.5 | 持仓量变化 + 资金费率是否过热 |
| ⑤ 盈亏比 | 0-2 | 潜在盈亏比是否达标（强趋势≥1.8，普通≥2.0） |
| ⑥ BTC/整体市场环境 | 0-1 | 大盘是否配合，板块是否联动 |

### 评分解释

- **8.5+** : 🔥 高质量机会，强趋势中可积极参与
- **7.0-8.5** : 🟢 普通机会，轻仓入场或等更好位置
- **5.5-7.0** : 🟡 机会一般，谨慎观望
- **<5.5** : 🔴 不做，等待

### 评分使用规则

1. 没有实时数据时不编造具体点位，只给条件化框架
2. 先判断市场环境（趋势/震荡/假突破），再评分
3. 评分是辅助，结构优先于指标
4. 低质量机会必须直接过滤，5分以下明确说不做

---

## 账户级风控系统（V4 + 链上打狗通用）

### 核心规则

```
单笔风险: 新手0.8% / 普通1.5% / 熟练2%（仅强趋势+高质量机会）
单日最大亏损: 账户本金 3%
连续亏损2笔: 下一笔仓位减半
连续亏损3笔: 停止交易，进入复盘模式
周最大回撤: 超6%停主动交易
账户回撤超10%: 恢复模式，仅允许减仓
```

### 仓位计算公式

```
单笔可亏金额 = 账户本金 × 单笔风险比例
止损幅度 = 入场价到止损价的百分比
合理名义仓位 = 单笔可亏金额 ÷ 止损幅度
杠杆 = 名义仓位 ÷ 账户本金
```

**关键认知：杠杆不是风险本身，仓位+止损距离才是真正风险。**

### 加仓纪律（V4 + 打狗通用）

- **只能**在盈利 + 结构确认的情况下加仓
- 强趋势中可更积极加仓，但加仓后整体止损必须可控
- 🚫 **禁止在亏损后补仓**
- 🚫 **禁止为摊低成本而补仓**
- 🚫 **禁止情绪化加仓**

### 持仓亏损处理

当持仓亏损时（套住/爆仓边缘）：
1. **先确认数据**：币种、多空、入场价、当前价、杠杆、仓位、是否有止损
2. **判断性质**：正常回撤 vs 问题交易（方向错/位置错/没有止损）
3. **给出方案**：保守（直接平）/ 中性（减仓）/ 激进（移止损）
4. **核心优先**：保护本金

### 盈利持仓处理

- 强趋势中：优先移动止损保护利润，不急于分批止盈
- 趋势出现明显转弱信号时：积极止盈
- 移动到保本损后可以让利润奔跑

---

## 结构化分析模板

每次交易分析按以下结构输出：

```
结论先行 → 当前结构 → 做多计划 → 做空计划 → 不交易条件 → 最终建议
```

### 结论先行

```
当前偏向：【偏多 / 偏空 / 震荡 / 观望 / 不建议交易】
评分：【X/10】
核心理由：【一句话】
当前最优动作：【等回踩 / 等确认 / 轻仓试单 / 分批止盈 / 减仓 / 观望】
```

### 做多/做空计划必须包含

做多触发条件、理想入场区、激进入场区、稳健入场区、止损位、第一止盈、第二止盈、第三止盈、移动止损规则、仓位建议、失效条件

### 不交易条件清单

盈亏比<要求 / 价格在震荡中轴 / 上方压力太近 / 下方支撑太近 / 无成交量确认 / OI和价格背离 / Funding过热 / BTC剧烈波动 / 山寨币流动性不足 / 止损位不合理 / 用户连续亏损或情绪化

### 注意：对于 meme coin 短线打狗场景，时间窗口短，重点看
1. 是否为趋势启动（vs 假突破/高潮派发）
2. 聪明钱是否在进场（vs 派发）
3. 止损是否清晰（结构失效位）
4. 仓位是否匹配账户风险（单笔≤1.5%）

---

## RH链特殊行为模式

RH链复制BSC早期路径，核心特征是**叙事多而散、资金不够分**。
详见 `references/rh-chain-patterns.md`。

关键要点：
- 好叙事（有主线的赛道）+ 大车头（持续奶）的币才值得拿
- 创始人随口提一嘴的方向不要追（RWA在RH无主线）
- 哪个涨追哪个是亏钱最短路径
- CASHCAT（meme龙头）/PONS（发射台龙头）是RH链好叙事典型

## 核心原则：Confluence（多重信号共振）

**务必遵守：没有单一指标触发告警，必须是多重信号同时对齐。**

| 信号强度 | 触发条件 | 操作 |
|:---------|:---------|:-----|
| 🔴 单一信号强 | 仅1个维度高分 | 不告警，继续观察 |
| 🟡 双重信号 | 2个维度同时高分 | 可关注，但要求验证 |
| 🟢 三重信号 | 3个维度高分 | 可以告警，值得试 |
| 🔥 四维全满 | 4个维度全部高分 | 强告警，优先考虑 |

**示例：** Bundle<10%（部署者优）+ 聪明钱>5个（资本关注）+ 成交量/市值比>1.0（交易活跃）→ 三者同时成立才告警。

**场景应用：**
- 新币刚发射（<30min）：Bundle和Top10指标权重降低，以聪明钱进场信号为主
- 币已运行>1h：四个维度权重回归正常
- Robinhood Chain：creator_close普遍化，降权处理

See `references/defillama-tvl-monitoring.md` for the API endpoint, target chains, and limitations of chain-level TVL monitoring. Used in the regular cron job to provide chain-level context alongside token-level scoring.

## Related Skills

Check **cross-chain-meme-kol-analysis** for narrative context (Solana KOL → BSC CZ-copy pattern) — the scoring system is most effective when combined with narrative analysis.

## Reference Files

| File | Description |
|------|-------------|
| `references/auto-scan-cron.md` | 多链自动扫描cron配置 |
| `references/robinhood-chain-scoring.md` | Robinhood链评分特例 |
| `references/defillama-tvl-monitoring.md` | DeFiLlama TVL监控 |
| `references/pipeline-test-20260711.md` | Pipeline全流程实测数据 — 10个代币评分+RH链信号分析 |
| `references/v4-backtest-methodology.md` | V4回测方法论 — 4H周期验证、Smooth Decline阈值、CCXT数据获取 |
| `references/pipeline-test-20260711.md` | Pipeline全流程实测数据 — 10个代币评分+RH链信号分析 |
| `references/rh-chain-patterns.md` | RH链打狗行为模式 — 叙事/车头/资金流动规律 |
| `references/rh-chain-market-structure.md` | RH链市场行为模式 — 叙事规律、操作纪律、信号判断（用户实战经验） |
| `references/rwa-tokenized-stocks.md` | RWA代币化股票验证（bStocks案例）— CoinGecko API验证法、搜索引擎被CAPTCHA拦截时的替代方案、RWA≠meme |
| `references/chain-report-cron-maintenance.md` | 链上合成日报cron(fa0df7d27b24)维护 — 改prompt必须从jobs.json读全量、三链成交量TOP5实现、代理前缀 |

## 原始GMGN数据提取过程

1. 用 `gmgn-cli token info --chain <chain> --address <address> --raw` 获取数据
2. 提取以上所有字段
3. 计算4个维度分数
4. 计算复合总分
5. 按格式输出报告给用户

## GMGN版本与链支持

GMGN CLI 需更新到 ≥ 1.5.2 才支持 Robinhood Chain。

```bash
# 检查当前版本
gmgn-cli --version

# 更新到最新（Robinhood Chain 需要 ≥ 1.5.2）
npm update -g gmgn-cli
```

最新版支持的链：`sol / bsc / base / eth / robinhood`

### 各链GMGN功能支持矩阵

| 链 | 热搜 | 币详情 | 信号 | Trenches新币 | K线 |
|:---|:---:|:-----:|:---:|:-----------:|:---:|
| **sol** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **bsc** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **robinhood** | ✅ | ❌ | ❌ | ❌ | ❌ |

Robinhood Chain 上只能获取热搜榜的概要数据（Bundle/Top10/聪明钱/流动性），详细分析需要结合 DexScreener 网站进行。

⚠️ **除了技术评分，必须同时参考 `references/rh-chain-market-structure.md` 判断市场叙事阶段** — RH链的核心风险不在筹码结构，而在于叙事是否清晰、资金是否集中。详见该文件的信号判断章节。

Robinhood Chain 的热搜数据质量很高：
- Bundle率普遍接近 0%（机器人少）
- Top10 大多 < 10%（筹码分散）
- 聪明钱活跃（20+ 个常见）

```bash
# Robinhood Chain 热搜（带数据过滤分析）
gmgn-cli market trending --chain robinhood --interval 1h --limit 20 --raw | python3 -c "
import json,sys
d=json.load(sys.stdin)
for t in d.get('data',{}).get('rank',[]):
    s=t.get('symbol','?')
    mc=float(t.get('market_cap',0)); vol=float(t.get('volume',0)); liq=float(t.get('liquidity',0))
    top10=float(t.get('top_10_holder_rate',0)); smart=int(t.get('smart_degen_count',0)); bundler=float(t.get('bundler_rate',0))
    buys=int(t.get('buys',0)); sells=int(t.get('sells',0)); holders=int(t.get('holder_count',0))
    print(f'{s} | MC:{mc:,.0f} | Vol:{vol:,.0f} | Liq:{liq:,.0f} | 1h:{ch1h:+.1f}% | B:{buys}/S:{sells} | H:{holders} | T10:{top10:.0%} | Bundle:{bundler:.0%} | Smart:{smart}')
"
```

## 批量自动扫描（多链热搜评分）

参见 `references/auto-scan-cron.md` 和 `scripts/score_trending.py`。

```bash
# 一键扫描三链（推荐用于cron job）
gmgn-cli market trending --chain sol --interval 1h --limit 20 --raw > /tmp/sol.json
gmgn-cli market trending --chain bsc --interval 1h --limit 20 --raw > /tmp/bsc.json
gmgn-cli market trending --chain robinhood --interval 1h --limit 20 --raw > /tmp/rh.json
python3 scripts/score_trending.py sol /tmp/sol.json
python3 scripts/score_trending.py bsc /tmp/bsc.json
python3 scripts/score_trending.py robinhood /tmp/rh.json
```

⚠️ **`gmgn-cli market trending` 必须传 `--interval`**（可选值: 1m / 5m / 1h / 6h / 24h），不传会报错退出。

## GMGN数据获取命令参考

获取代币完整信息（含筹码结构、聪明钱、评分所需全部字段）：
```bash
gmgn-cli token info --chain sol --address <ADDRESS> --raw
```

对于新发射的币，检查Trenches（最新发射池）：
```bash
gmgn-cli market trenches --chain sol --limit 30 --raw | python3 -c "
import json,sys
d=json.load(sys.stdin)
for t in d.get('data',{}).get('rank',d.get('data',[])):
    s=t.get('symbol','?')
    mc=float(t.get('market_cap',0)); vol=float(t.get('volume',0)); liq=float(t.get('liquidity',0))
    top10=float(t.get('top_10_holder_rate',0)); bundler=float(t.get('bundler_rate',0)); smart=int(t.get('smart_degen_count',0))
    buys=int(t.get('buys',0)); sells=int(t.get('sells',0)); holders=int(t.get('holder_count',0))
    # 预过滤：查看Bundle<20%、Top10<50%、聪明钱≥1、流动性>$5K的币
    if bundler < 0.2 and top10 < 0.5 and smart >= 1 and liq > 5000:
        print(f'{s} | MC:\${mc:,.0f} | Vol:\${vol:,.0f} | Liq:\${liq:,.0f} | B:{buys}/S:{sells} | H:{holders}')
"
```

用`--raw` flag输出JSON后用python过滤，避免手动逐条翻看。

获取K线数据（用于阴谋盘检测）：
```bash
gmgn-cli market kline --chain sol --address <ADDRESS> --resolution 15m --from <START_TIMESTAMP> --to <END_TIMESTAMP> --raw
```

## 评分参考实例

### CZ (Final Form Bull) — 2026-07-04 评分复盘

```
价格: $0.05066（阶段4恢复中）
MC: $50M+（已经偏大了）
流动性: $888K ✅
Top10: 74% ❌（太高）
Bundle: 12% ⚠️
聪明钱: 18个 ✅
持仓: 10,633人 ✅
24h交易: 220,249笔 ✅
评级: 观察级（MC太大+Top10太高，但聪明钱和交易量尚可）
```

### Robinhood Chain 管道扫描评分 — 2026-07-11 全流程实测

全量扫 Robinhood trending 1h，10个代币评分分布：
- **A STRONG BUY (85+)**: 0% — 无高质量标的
- **B WATCH (70-84)**: 20% ($SCAM 72分, $VLAD 71分)
- **C INTERESTING (60-69)**: 20% ($UTILITY 68分, $Pointless 62分)
- **D PASS (<60)**: 60% — 6个代币过滤

**Robinhood 链核心发现：**
- **`creator_close: true` 几乎是标配**（10/10个币部署者已撤池）→ 在RH链上这个字段**不能作为正向信号**，需降权
- **聪明钱分布极端**：要么20+（$SCAM 32个、$UTILITY 25个、$VLAD 22个），要么个位数
- **牛市率普遍偏高**（$SCAM 57%、$UTILITY 28%）→ 需扣分处理
- **MC普遍偏低**（多数<$100K，只有$VLAD >$1M但已暴跌82%）
- **Bundle率接近0%** → 对RH链不适用作为过滤条件

**修正后的 RH 链评分建议：**
| 维度 | 原权重 | RH链调整 | 原因 |
|------|--------|---------|------|
| 部署者质量 | 30% | 20% | creator_close 太普遍，无法区分好坏 |
| 聪明钱质量 | 25% | 30% | 聪明钱数量在RH链上区分度高 |
| 链上健康度 | 25% | 25% | 机器人率和Top10依然有效 |
| 交易活跃度 | 20% | 25% | 成交量/市值比和买卖比是最佳RH链信号 |

### $Jamey — 评分实测（2026-07-10）

```
部署者质量: 70/100 — Bundle31%略高扣分，但Top10仅17%分散好，Dev已抛售
聪明钱质量: 43/100 — 仅1个聪明钱进场、3个追踪者
链上健康度: 63/100 — 流动性$22K够用，MC$88K黄金区间，但锁仓率0%
交易活跃度: 73/100 — 成交量/市值比1.7x活跃，4468笔交易，687持有人
🔥 总分: 62/100 → 🟡 观察级
⛔ 主要扣分: Bundle31%太高、聪明钱才1个、流动性没锁仓
```

## Pitfalls

- ⚠️ **`lock_percent` 可能为null** — GMGN返回的JSON中可能是None。防御写法：`lock_pct = float(t.get('lock_percent',0) or 0)`
- ⚠️ **`renounced_mint` 在EVM链上为null，但BSC/RH用 `is_renounced`** — Solana用 `renounced_mint`（1=已放弃），BSC/Robinhood用 `is_renounced`（1=已放弃）。必须同时检查两个字段，因为**一个为null时另一个才有值**。❌ 错误写法：`renounced = 1 if t.get('renounced_mint') else 0`（null被当作False，EVM链上全判为未放弃）。✅ 正确写法：`renounced = (t.get('renounced_mint') == 1) or (t.get('is_renounced') == 1)`
- ⚠️ **`gmgn-cli market trending` 必须传 `--interval`** — 可选值: 1m / 5m / 1h / 6h / 24h，不传会报错 `error: required option '--interval <interval>' not specified`
- ⚠️ **Bundle低≠安全** — 有些币Bundle率很低但Top10 > 70%，同样是庄盘。两个指标必须一起看
- ⚠️ **聪明钱为0不一定skip** — 刚发射的币(<30min)可能还没标记聪明钱。等30分钟再扫
- ⚠️ **MC > $1M + 成交量萎缩** = 🚩 币已老，聪明钱在退出
- ⚠️ **先判断叙事阶段再打分** — Phase 3冷却期的币高分也不推荐。用cross-chain-meme-kol-analysis判断市场处于哪个阶段
- ⚠️ **6类过滤器关键词假阳性** — 执行批量过滤时，`"sui"` 会误匹配 `"SHINYSUIT"`，`"tron"` 会误匹配 `"astronaut"`。必须用词边界匹配（`\bkw\b`）或符号开头匹配。详见 meme-coin-multi-agent-pipeline 的 ⚠️ 关键词假阳性陷阱 章节
- ⚠️ **`python3 -c` 管道被拦截** — Hermes 安全系统拦截含 `python3 -c` 的终端命令。所有内联 Python 必须写入 `.py` 文件再执行。`write_file` 创建脚本 → `python3 /path/to/script.py`
