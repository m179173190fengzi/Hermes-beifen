---
name: onchain-meme-analysis
category: crypto
description: 全链打狗数据分析。整合GMGN + DexScreener + Twitter + DeFiLlama + NOXA/Robinhood链数据，任何币地址扔过来自动评分。
---

# 链上打狗数据分析系统

## 触发条件

用户提供任何链上的代币地址，或是要求扫链分析时，执行本技能。

## 工具链

- `gmgn-cli` — GMGN链上数据（热搜/聪明钱/Token信息/信号）
- `curl` — DexScreener API / DeFiLlama API
- `twitter` — X/Twitter搜索
- `yt-dlp` — YouTube信息抓取

## 工作流

### 模式A：分析单个代币

用户发来一个代币地址和链名时：

1. **GMGN数据拉取**
   ```bash
   gmgn-cli token info --chain <chain> --address <地址> --raw
   gmgn-cli token signal --chain <chain> --address <地址> --raw
   ```
   
2. **DexScreener数据**
   ```bash
   curl -s "https://api.dexscreener.com/latest/dex/tokens/<地址>"
   ```

3. **Twitter搜索**（看社区热度）
   ```bash
   twitter search "\$<币符号> -is:retweet" 
   ```

4. **评分（0~100）**
   - 筹码分布(25%): Top10集中度 + Bundle率
   - 聪明钱(25%): smart_degen_count数量
   - 流动性(20%): 流动性与市值比
   - 交易活跃(15%): Volume/MC比
   - 社交热度(15%): Twitter提及量

5. **输出格式**
   ```
   🔍 <币符号> 评分分析
   ━━━━━━━━━━━━━━━━━━━━━━━
   链: <chain> | 地址: <address[:12]>
   
   📊 维度评分:
     筹码分布: XX/100 (Top10 X%, Bundle X%)
     聪明钱:   XX/100 (Smart X个)
     流动性:   XX/100 ($X)
     交易活跃: XX/100 (Vol $X)
     社交热度: XX/100 (Twitter X条)
   
   🔥 复合总分: XX/100
   
   ⚠️ 风险提示:
   - Bundle > 30%? → 机器人盘
   - Dev还在持币? → 随时出货
   - 流动性可移除? → 可能rug
   
   💡 建议: [买入/观察/回避]
   ```

### 模式B：扫链浏览

用户要求扫某个链时：

1. **GMGN热搜榜**
   ```bash
   gmgn-cli market trending --chain <chain> --limit 20
   ```
   
2. **DexScreener新币**（Robinhood链专用）
   ```bash
   curl -s "https://api.dexscreener.com/latest/dex/search?q=robinhood"
   ```
   
3. **新币Trenches**（Solana/BSC/Base/ETH）
   ```bash
   gmgn-cli market trenches --chain <chain> --limit 30
   ```

4. **信号检测**
   ```bash
   gmgn-cli market signal --chain <chain>
   ```

5. **过滤规则**
   - ✅ Bundle < 20%
   - ✅ Top10 < 50%
   - ✅ 聪明钱 > 2个
   - ✅ 流动性 > $5K
   - ✅ < 1小时 新币优先
   - ✅ 有社交链接优先

### 模式C：Robinhood链专用扫链

按用户的完整流程：

1. 打开壁门监控：DexScreener Robinhood New Pairs + NOXA Fun Trending
2. 实时刷新，关注年龄 < 30分钟的新对
3. 快速筛选：
   - 有社交链接(Twitter/TG)?
   - 叙述是否强？（Robinhood/GME/官方相关）
   - 交易量和买入笔数是否突破？
4. 深入分析：
   - GMGN查聪明钱
   - Blockscout查持仓分布
   - 合约安全检查

### 模式D：链市纵观（定时合成日报）

用于定时任务，输出简报。**用户钦定的"每日Alpha合成简报"格式**（2026-07-31两次改版确认：①加回完整5板块 ②新增新币监控 ③排版简明每条≤3行，不要擅自加回长格式）：

```
━━━ 📡 每日Alpha合成简报 ━━━
⏰ {日期时间}

━━━ 💰 三链TVL ━━━
Sol: $XB(±X%) | BSC: $YB(±X%) | RH: $ZB(±X%)
📊 [一句话结论]

━━━ 🔥 优质标的 ━━━
#1 $SYM (CHAIN) | MC $X | 评分XX/75 | 6h ±X%
📋 [叙事1句] | 类别:XX
👥 持币X 聪明钱X | 💡 [价值1句]

━━━ 🆕 新币监控(1D内 MC≥$1M) ━━━
#1 $SYM (CHAIN) | MC $X | 高点 $Y | 6h ±X%
📋 [叙事1句]
👥 持币X 聪明钱X | ⚠️ [风险1句] | 💡 [价值1句]

━━━ 🧠 交叉验证 & Alpha ━━━
🚀 [核心叙事/热点簇 1-2句]
🔗 [跨链镜像检测结果 1-2句]
🚩 [风险预警 1-2句]
🎯 [建议关注方向 2-4条，每条一行]
```

**新币监控筛选标准（2026-07-31用户确认）**：部署时间1D内 + MC稳定在$1M以上（不是瞬时冲高，看MC历史最高值vs当前值判断是否站稳），标注Rug/貔貅风险（bundle率、creator撤池、锁定情况）。

**流程**：扫Sol/BSC/RH三链 trending 6h → 6类过滤器（链创始人/KOL/政治/科技/社会/机构）→ 加分制评分≤75分，≥70推/<60过滤（RH链特例：creator_close不加减分）→ 跨链叙事交叉验证 → 新币监控（1D内+MC≥$1M）→ TVL资金流（`python3 /home/wei/.hermes/scripts/tvl_monitor.py`，勿用/tmp路径——重启会丢）。

**风控规则**：不推MC<$10K；不推Bundle>30%；Top10>70%标注高度控盘；三链都无≥70分+无热点 → 回复 [SILENT] 不推送。

**📰 公众号排版交付（2026-07-31用户钦定）**：定时链上日报最终产物用 `gzh-design` 技能排成公众号HTML，不再发纯文本长报。流程：生成Markdown简报 → 加载gzh-design（题材=数据复盘/行情报告，主题用「石墨极简风」或「橄榄手记」）→ 读theme-index + 对应主题组件库 + common-components → 装配HTML → 跑 `python3 ~/.hermes/skills/gzh-design/scripts/validate_gzh_html.py <html>` 清零ERROR和半角标点WARNING → 用 `scripts/wrap_preview.py` 生成带复制按钮的预览页 → 最终响应附HTML文件路径（MEDIA:发送预览页）。gzh-design已装于 `~/.hermes/skills/gzh-design/`（6主题+自定义主题生成器）。

**🔴 程序化生成HTML的坑（Python拼HTML时踩过，validate脚本会报WARNING）**：
- 用辅助函数做关键词下划线标记时，简单 `text.replace(keyword, '<span style=...>...</span>')` 会让**外层文本失去 `<span leaf="">` 包裹**，粘贴到公众号样式整片丢失。
- 正确模式：**按关键词拆分文本，交替拼接**——每段普通文本包 `<span leaf="">text</span>`，关键词包 `<span style="border-bottom:2px solid #52525B;font-weight:600;color:#27272A;"><span leaf="">kw</span></span>`（leaf嵌套在样式span里）。
- 每个装饰性空元素（细线/水印编号装饰/END短线）内部必须放 `<span leaf=""><br></span>` 占位，否则微信剥样式。
- 生成后**必跑** `validate_gzh_html.py`，ERROR必须清零，半角标点WARNING也要修到0（中文正文用全角标点，代码/URL内保持半角）。
- 文件名规范：`{日期}_链上日报_排版.html`（干净正文，纯section片段不带DOCTYPE）+ `{...}_预览.html`（wrap_preview.py产物）。

**⚠️ cron异步跑全套慢**：7个技能加载+排版全流程2-3分钟，用户会催。方案：①纯文本简报先出（快），HTML排版文件随后补发；②或接受延迟。用户已确认排版交付为最终形态，但每次手动验收时直接用execute_code跑数据+拼HTML（15秒出数据+校验），别等cron。

**⚠️ 代理坑**：`gmgn-cli` 直连会 ECONNREFUSED，必须在带代理环境变量下运行（`HTTPS_PROXY=http://127.0.0.1:7890` 等）。execute_code 的 subprocess 不继承 shell 代理，需显式传 env。`curl api.llama.fi` 同样需要代理。

**数据命令**：
```bash
gmgn-cli market trending --chain sol --interval 6h --limit 30 --raw
gmgn-cli market trending --chain bsc --interval 6h --limit 30 --raw
gmgn-cli market trending --chain robinhood --interval 6h --limit 30 --raw
```

## 相关技能

- `mc-robinhood-narrative-map` (crypto) — Robinhood Chain叙事图谱，判断新币的叙事层和板块轮动。分析Robinhood链代币时优先加载该技能对照叙事地图。
- `meme-coin-scoring` (crypto) — 0~100分复合评分系统（部署者信誉/聪明钱/链上健康/交易活跃度/社交热度）

- GMGN CLI对Robinhood Chain仅支持market trending，不支持token info和signal
- Twitter搜索不需要认证
- DexScreener API限流较宽，但不要高频请求
- 评分中Bundle/SmartMoney数据优先来自GMGN，因为最准确
