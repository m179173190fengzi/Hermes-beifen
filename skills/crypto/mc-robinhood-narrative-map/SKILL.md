---
name: mc-robinhood-narrative-map
description: Robinhood Chain 叙事图谱 - 自动识别新币属于哪个叙事层，评估潜力
---

# Robinhood Chain 叙事分析

## 职责
用户问Robinhood链上的币时，自动对照叙事图谱评估其位置和潜力。

## 三链叙事板块

### 🟠 纯Meme层（占市值~89%）
**核心逻辑：** Robinhood概念自我指涉

**公司Lore层（最强叙事）：**
- $CASHCAT 🏆 — 公司2013年原名 ($179M)
- $JUGGERNAUT — X-Men红坦克×Vlad原推 ($14.6M)
- $HOODRAT — 双关+Matt Furie画风 ($11.3M)
- $KITSU — Vlad家柴犬 ($2.7M)
- $FIDEL — 联创Baiju的猫 ($95K)
- $WALLET — Robinhood Wallet产品名
- $1 — "1美元就够了"营销梗 ($1.65M)
- $4663 — Chain ID=HOOD(T9键盘)
- $CONFETTI — 监管抗争史 ($4万)

### 🔵 HOOD双关/罗宾汉传说层（~10%）
- $HOODRAT — 街俚×Robinhood双关
- $ROB — "劫富济贫"散户反建制
- $MARIAN — 传说女主重写
- $DIH — 帮规梗，社区运营最强

### 🟣 AI Agent基础设施层（新兴叙事）
**核心逻辑：** Robinhood链上的AI Agent平台/TG Bot代币，结合Meme+实用

| 代币 | MC | 叙事 |
|:----|:--:|:------|
| **$VEX** | **$12M** 🔥 | "Verifiable AI agent infrastructure" — 本地运行时+链上证明，50x已过正在回调(-26%) |
| **$RAXOL** | — | axol.io 开源Agent runtime，链上商务Agent |
| **$SPARKLE** | — | 虚拟生态系统中的Agent基础设施层 |
| **$AXOL** | — | axol.io 实验项目的代币，同生态关联 |

**识别方式：** 这类币的GMGN数据特征——Smart Money较多（$VEX有18个），Top10偏高（52%），Lore不同于纯Meme但仍在Robinhood生态内。叙事介于"纯Meme"和"实用币"之间，寿命比纯Meme长但波动同样剧烈。

### 🟡 WSB散户记忆层（~1%）
- $TENDIES — WSB黑话"炸鸡柳=利润"
- $GME — 2021拔插头恩怨

### 还没发币的热门叙事（埋伏机会）
- KENNY/mayo man — Ken Griffin 2021反派
- WE ARE ALL INVESTORS — 550万广告梗
- Vlad the Stock Impaler — 全网外号
- MOASS — GME信仰词

## Robinhood 跨链模仿逻辑
Solana Ansem叙事 → BSC CZ对位 → Robinhood 公司Lore

## 参考文件

- `references/robinhood-narrative-catalog.md` — 完整叙事目录（含MC、叙事原文、未发币埋伏机会）
- `references/scanning-workflow.md` — 用户编写的扫链全流程（筛选→检查清单→风控→潜力判断）
- `references/scoring-cheatsheet.md` — Quick reference for terminal commands and common filters

## Blockscout 链上验证（重要补充）

当用户提供一个 Robinhood Chain 币的地址，用 Blockscout 验证链上数据是**独立于GMGN的另一条验证路径**，能补充GMGN Robinhood链不支持token detail的缺口。

```bash
# 打开币的Blockscout页面（浏览器）
https://robinhoodchain.blockscout.com/token/<ADDRESS>

# 会自动显示：
# - 总供应量（通常10亿）
# - 持仓人数（Holders）
# - 转账次数（Transfers）
# - 创造者地址（Creator）

# 查看持有人分布加 ?tab=holders
https://robinhoodchain.blockscout.com/token/<ADDRESS>?tab=holders
```

**参考案例 — $1 代币的Blockscout数据解读（2026-07-10）：**

| 指标 | 数值 | 解读 |
|:----|:----|:------|
| 总供应量 | 1,000,000,000 (10亿) | Robinhood链标准供应量 |
| 持仓人数 | **2,364** | 🟢 不错，分散度中等 |
| 转账次数 | **62,344** | 🟢 非常活跃，链上真实交易 |
| 创造者 | 0xD9...FCcB | ✅ 部署交易成功，非蜜罐 |
| 合约验证 | 未验证（常见） | ⚠️ Robinhood链上线仅10天，合约验证率低 |

**注意：** Blockscout 的持有人列表页显示的是 Token 持有分布，不是个别钱包。要查具体前10持仓需翻页。Blockscout页面有时需要点击 token 标签页（不是 address 标签页）。

1. 搜该币的叙事归属（对照`references/robinhood-narrative-catalog.md`）
2. 查GMGN/DexScreener数据（流动性/MC/成交量/聪明钱）
3. 看同板块龙头表现（CASHCAT→$1→CONFETTI轮动逻辑）
4. 评估赔率
5. 出结论

## 板块轮动逻辑

同板块内**龙头站住脚后，其他币会轮动跟涨**。当前Robinhood链板块轮动：
```
$CASHCAT ($179M) — 大盘稳住了
    ↓ 轮动到
$WALLET ($929K) — 官方产品名，仍在上涨
    ↓ 再轮动到
$1 ($1.68M) — 营销梗，用户以$1.5M入场持有
    ↓ 再轮动到
$CONFETTI ($4万) — 赔率最大，但风险也最高
```
