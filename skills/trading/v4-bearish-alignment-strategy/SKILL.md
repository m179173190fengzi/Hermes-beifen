---
name: v4-bearish-alignment-strategy
description: "V4 交易策略 — 6均线(SMA20/60/120+EMA20/60/120) + 看大做小。⚠️ 4H最优，1m-15m短周期已验证亏损，勿用于日线/周线回测"
version: 8.0.0
author: Hermes Agent + CryptoFengzi
tags: [freqtrade, trading, strategy, futures, okx, multi-timeframe]
---

# V4 交易策略

## ⚠️ 安全铁律

**绝对不能拿真实资金开单！** 任何交易操作都必须经过用户明确确认才能执行。所有Freqtrade策略只能跑dry_run模拟模式。

---

## 🚫 硬性约束（必须遵守）

| 规则 | 说明 |
|------|------|
| **6条均线不能改** | SMA20/60/120 + EMA20/60/120。任何周期、任何场景都不能改成其他参数。预热时间长不是理由，用户不听这个。违反会被骂 |
| **看大做小** | 从大到小逐级搜索找入场，不是同一张图 |
| **熊市只做空** | 开启bear_market_mode=True，屏蔽所有做多信号 |
| **样本默认BTC** | 用户给走势参考默认是BTC/USDT:USDT，先确认品种再分析 |
| **用户纠正时** | 停下来，原文重读，不要脑补，不要猜错一个方向继续猜另一个 |
| **灵活运用** | 用户说「以此类推」= 把当前逻辑推广到所有类似场景 |
| **均线在K线上方** | 做空时均线必须在K线上方（压制），不是K线在均线中间穿梭 |

---

## 🎯 看大做小 — 正确理解

**从大到小逐级搜索：**

```
15m: 6条均线空头排列 + K线在均线下方 → 方向看空
  ↓ 但是还没到入场时机
10m/5m: 有没有流畅下跌？还没？ 
  ↓ 继续往下
 3m/1m: K线被均线压制 + 流畅下跌 + 不反弹突破 → 🟢 开空
```

**关键点：**
- **看大（方向确认）：** 大周期的6条均线是否排列整齐压制K线
- **做小（入场时机）：** 到小周期看K线是否流畅下跌且不反弹突破MA20/EMA20
- 两个级别不固定绑定，从大到小找到信号为止

**参考样本：** BTC 1m 2026-06-27 19:15~19:43（北京），从60340跌到60171，教科书式流畅下跌

---

## 🎛️ V4做空条件（完整版）

| 条件 | 说明 | 级别 |
|:----|:------|:----:|
| 1. 均线依次排列 | SMA20 < SMA60 < SMA120, EMA20 < EMA60 < EMA120, EMA20 < SMA20 | 大周期 |
| 2. K线在均线下方 | 收盘价低于所有6条均线 | 大周期 |
| 3. K线被均线压制 | K线被均线压着，不反弹突破 | 小周期 |
| 4. 流畅下跌 | 连续N根K线创新低（默认3根） | 小周期 |
| 5. 不反弹 | K线最高价没突破SMA20和EMA20 | 小周期 |

---

## 📁 文件结构

| 文件 | 内容 |
|------|------|
| SKILL.md | 本文件 |
| `references/v4-strategy-code.md` | 策略完整代码 |
| `references/v4-evolution.md` | 版本演进历史 |
| `references/btc-reference-sample.md` | BTC 1m参考样本 |
| `references/backtest_results.md` | 各版本回测数据 |
| `references/session-corrections.md` | ✅ **必读！** 用户纠正记录 |
| `references/atk-cli-integration.md` | ✅ OKX ATK CLI实时检测V4信号 |
| `scripts/v4-check-signals.py` | ✅ 自包含策略脚本（skill内独立运行，不依赖外部文件） |

**必读：** 每次加载此skill前先读 `references/session-corrections.md`。

---

## 🐛 关键陷阱

| 坑 | 正确做法 |
|----|----------|
| merge_informative_pair的列名后缀 | 用 `dataframe.get(f"trend_short_{dtf}", False)` 读 |
| bool类型冲突 | populate_indicators用`v4_short`/`v4_long`做bool列，populate_entry_trend里才赋enter_short |
| 预热不够导致0信号 | 1m SMA120需要2小时预热，15m SMA120需要30小时 |
| 策略代码路径 | `~/ft_userdata/user_data/strategies/v4.py`，类名 `V4Strategy` |
| 用户默认给BTC数据 | 用户说走势参考时默认是BTC，确认前不要自己查ETH |
| 改参数前先确认 | 用户没说改参数的时候不要自作主张改 |
| **ATK CLI下单用错模式** | 有 --demo 参数的是模拟盘，不加的是实盘。**实盘要重新OAuth授权**并勾选实盘权限。授权时选错模式要重新跑 `okx auth login --manual --site global` |
| **合约张数计算** | BTC-USDT-SWAP每张=0.01 BTC。张数 = (保证金×杠杆) / (BTC价格×0.01)。市价单有限额，超限报错 51202，需要减张数重试 |
