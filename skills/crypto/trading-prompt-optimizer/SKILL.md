---
name: trading-prompt-optimizer
description: 基于prompt-optimizer（linshenkx）的结构化方法论，专为加密货币交易/市场分析提示词设计的优化模板系统
category: crypto
---

# 交易提示词优化器

> 灵感来源：https://github.com/linshenkx/prompt-optimizer — 将其结构化提示词优化方法论适配到加密货币交易分析场景

## 用法（4种模式）

### 模式1：首次优化（general-optimize）
1. 加载本skill：`skill_view name=trading-prompt-optimizer`
2. 把你要优化的原始prompt贴在user消息中
3. 我会自动输出结构化版本

### 模式2：使用模板直接写（最快）
1. 选对应类型的模板文件（见下方 Templates 表）
2. 复制模板，替换 `[占位符]` 内容
3. 完成

### 模式3：迭代改进已有prompt（iterate）
1. 加载本skill，贴出你现有的结构化prompt
2. 说："迭代这个prompt：[具体需求]"
3. 我会针对性修改，保留原有核心逻辑和占位符

### 模式4：优化现有cron job
1. 先用 `cronjob action=list` 找出你要优化的job
2. 用 `session_search` 找到该cron的原始prompt
3. 贴给本skill处理
4. 确认后用 `cronjob action=update` 替换

## 核心方法论

借鉴 prompt-optimizer 的三个核心层：

| prompt-optimizer 层 | 交易场景适配 |
|---|---|
| **结构化重组** (general-optimize) | 松散交易指令 → Role/Market/Workflow/Risk 结构 |
| **分析式优化** (analytical-optimize) | 深度分析交易意图，增加背景和风控约束 |
| **迭代改进** (iterate) | 在已有优化prompt基础上针对性微调，不丢失核心逻辑 |
| **评估对比** (evaluation) | 对比优化前后的输出质量，评估是否实质改进 |

## 交易分析提示词结构化模板

优化后的输出必须按以下结构：

```
# Role: [角色名称]

## Profile
- Language: [语言]
- Description: [角色核心定位 - 一句话]
- Expertise: [专业领域]
- Market: [交易市场/标的范围]

## Market Context
- Direction: [做空 / 做多 / 双向]
- Timeframe: [时间周期，如 1h/4h/daily]
- Preference: [标的偏好，如 BTC/SOL/链上代币]

## Tools & Data Sources
- [数据来源1：如 GMGN CLI、DexScreener]
- [数据来源2：如 Twitter CLI、X API]
- [数据来源3：如 DeFiLlama]
- [数据来源4（可选）：OKX ATK — `okx market ticker` 行情 / `okx market candles` K线 / `okx news sentiment` 情绪 / `okx smartmoney` 聪明钱]
- [策略计算脚本：`~/v4-strategy.py` — 6MA看跌排列检测，详见 references/v4-atk-execution.md]

## Analysis Framework
### [分析维度1 标题]
- [具体规则]
- [具体规则]

### [分析维度2 标题]
- [具体规则]
- [具体规则]

## Risk Rules
1. [止损规则]
2. [仓位规则]
3. [杠杆限制]
4. [资金费率警戒]
5. [特殊约束：如熊市只做空 / 评分<60跳过]

## Workflow
1. [第一步：数据获取]
2. [第二步：分析计算]
3. [第三步：判断决策]
4. [第四步：格式化输出]

## Output Format
- [字段1]
- [字段2]
- 静默模式：当无信号时输出 [SILENT]

## Initialization
作为[Role]，遵守上述Risk Rules，按Workflow执行，以Output Format输出。
```

### 类型C：社媒监控/叙事追踪
- 场景：KOL喊单检测、Twitter热点、叙事演变
- 核心：搜索策略、来源可信度、噪音过滤
- **分析师定点追踪**：用 `twitter search from:用户名` 追踪固定分析师列表，每天汇总观点
- **内容质量分级**：🟢KOL/高互动保留原文 / 🟡普通仅摘要 / 🔴丢弃纯喊单

### 类型D：每日Alpha合成简报（cron合并流水线）
- 场景：把多个独立cron合并成一条每日情报流水线，减少LLM调用次数
- 核心：链上扫描 + 推特分析师追踪 + TVL资金流 + 交叉验证 → 一份简报
- 增强渠道：女娲蒸馏交易分析师成Skill，在Alpha简报里调用分析观点
- **ATK数据增强**：集成 `okx` CLI行情 + `okx news sentiment` 情绪 + `okx smartmoney` 聪明钱信号（见 references/atk-integration.md）

### 类型E：人物蒸馏（crypto KOL视角Skill）
- 场景：把交易KOL的思维框架炼成可对话的Hermes Skill
- 核心：心智模型 + 决策启发式 + 表达DNA + 反模式 + 诚实边界
- 使用女娲快速档（3维度：表达+对话+他者），或手动从推特搜索构建

**合并流程（从@0xJeff工作流提炼）：**
1. 检查现有cron列表（`cronjob action=list`），找出同时间段的多条cron
2. 统一用 `cronjob action=remove` 删除旧cron
3. 创建一条新cron，prompt内以4阶段Pipeline组织：扫链→分析师追踪→交叉验证→输出
4. 4阶段Pipeline定义：
   - **阶段1 链上扫描**：三链trending + 6类过滤 + 评分
   - **阶段2 分析师追踪**：固定名单 `twitter search from:用户名`，取每人当天观点
   - **阶段3 交叉验证**：链上 vs 推特情绪对比
   - **阶段4 TVL资金流**：三链TVL对比 + 7天趋势 + 资金流向结论

**默认分析师名单（可自定义）：**
- @AIBullss(交易策略) @0xJeff(链上Alpha) @Ansem(Sol/KOL)
- @Murad(meme) @Cobie(热点评论) @Hsaka(宏观)

**外部源周轮换（来自@0xJeff，防止信息茧房）：**
- 周一论文 → 周二对冲基金信 → 周三链上数据 → 周四衍生品 → 周五宏观

**交叉验证逻辑（核心方法论）：**
- 链上卖出 + 推特喊涨 → 🚩 预警（出货掩护）
- 推特冷清 + 链上流入 → 🐋 有人偷偷建仓
- Sol热点 + BSC有同叙事CZ版本 → 跨链镜像交易机会

**输出格式顺序：** TVL对比 → 链上优质标的 → 分析师观点 → 交叉验证 → 资金流向结论

**cron合并注意事项：**
- 合并后确保新cron的 `enabled_toolsets` 包含原所有cron需要的工具集
- cron job自包含single prompt，不加载skills（防上下文溢出）
- 默认 `deliver: origin` 推送到当前聊天

## 示例：优化前后对比

### ❌ 原始prompt（松散版）
```
查一下今天的链上热搜，看看有没有新币值得关注。先扫Solana再扫BSC，帮我看看哪些有聪明钱进去的。评分低的不看。
```

### ✅ 优化后（结构化版）
```
# Role: 链上狩猎分析师

## Profile
- Language: 中文
- Description: 专门扫描多链新发射代币的专业分析师，从链上数据中挖掘有潜力的标的
- Expertise: 链上数据解读、聪明钱追踪、叙事分析
- Market: Solana / BSC / Robinhood Chain 链上meme币

## Market Context
- Direction: 双向（仅捕捉叙事驱动的短期机会）
- Timeframe: 按1h热搜窗口扫描
- Preference: 匹配6类过滤器（链创始人/KOL/政治/科技/社会/机构）的代币

## Tools & Data Sources
- gmgn-cli market trending --interval 1h — 热搜榜
- gmgn-cli token info — 代币详情（筹码/聪明钱/流动性）
- Google / Twitter — 叙事背景验证

## Analysis Framework
### 6类过滤器（硬性条件）
- 代币名/符号必须匹配以下类别关键词之一：
  - 🔗 链创始人（CZ、Vitalik、Anatoly...）
  - 📣 KOL喊单（Ansem、Cobie、Murad...）
  - 🏛️ 政治人物（Trump、Musk、Biden...）
  - 🔬 科技领袖（Altman、Hinton、Torvalds...）
  - 🌐 社会事件（对抗、Meme潮、热点...）
  - 🏢 知名机构（a16z、Binance、Pantera...）
- 不匹配 → 直接跳过

### 代币4维评分
1. 部署者质量(30%)：Bundle率/Top10集中度/Dev持仓/放弃铸币
2. 聪明钱质量(25%)：聪明钱数量/知名追踪者/狙击手数量
3. 链上健康度(25%)：流动性/市值/锁仓率/成交量市值比
4. 交易活跃度(20%)：买卖比/总交易笔数/持仓人数

## Risk Rules
1. 评分 < 60 的代币不推送
2. Bundle率 > 30% 不推荐
3. MC > $2M 的币谨慎（错过早期窗口）
4. 冷市场（三链都无≥60分）输出[SILENT]静默

## Workflow
1. 扫Sol→BSC→RH三链热搜榜（1h），取前20
2. 对每个代币执行6类过滤
3. 通过过滤的代币执行4维评分
4. 输出评分≥60的代币报告

## Output Format
━━━ 链上代币实值评估 ━━━
📋 叙事: [1-2句说明]
🏷️ 类别: [匹配的6类标签]
🐦 推特: [x.com/链接]
代币: $SYMBOL
📊 维度评分: [4项明细]
🔥 总分: XX/100
判定: 🟢推荐 / 🟡观察 / 🔴跳过
关键数据: [MC/流动性/聪明钱/持仓等]

## Initialization
作为链上狩猎分析师，遵守上述Risk Rules，按Workflow执行，确保每个输出都包含完整字段。
```

## Templates（模板文件）

| 文件 | 类型 | 适用场景 |
|------|------|---------|
| `templates/type-a-strategy-signal.md` | 类型A | V4策略/行情分析/趋势判断 |
| `templates/type-b-chain-hunting.md` | 类型B | meme币扫描/Trenches/新币评分 |
| `templates/type-c-social-monitoring.md` | 类型C | KOL喊单/Twitter热点/叙事追踪 |
| `templates/type-d-alpha-synthesis.md` | 类型D | cron合并/每日Alpha合成简报 |

用法：`skill_view name=trading-prompt-optimizer file_path=templates/type-X-*.md`，复制内容，替换 `[占位符]`。

## Reference Files

| File | Description |
|------|-------------|
| `references/quick-guide.md` | 4种使用方式（首次优化/深度分析/迭代改进/评估对比） |
| `references/optimization-case-study.md` | 实战案例1：链上打狗扫描prompt优化前后对比 |
| `references/twitter-monitoring-case-study.md` | 实战案例2：推特热点监控prompt优化前后对比 |
| `references/super-hermes-meta-reasoning.md` | Super Hermes元推理层 — 结构化优化后的下一步：让prompt反思自身盲区 |
| `references/community-ecosystem.md` | Hermes社区生态工具速查（Workspace/Dashboard/OMH/Achievements/Super Hermes） |
| `references/upstream-architecture.md` | prompt-optimizer上游项目架构参考（MCP Server/模板引擎/评估驱动重写） |
| `references/prebuilt-personas.md` | 社区预蒸馏人物Skill索引（Panmax/awesome-nuwa 165个人物速查+安装命令） |
| `references/v4-atk-execution.md` | V4策略 + OKX ATK CLI 集成 — 均线计算脚本/CLI命令/多时间框架分析流程 |
| `references/atk-integration.md` | OKX Agent Trade Kit 集成指南 — 安装流程/11个Skills索引/CLI速查/Alpha简报集成方案 |

## Pitfalls

- ⚠️ **不要过度结构化** — 如果原始prompt只有3个简单步骤，强行塞满10个section反而降低可读性。核心是让逻辑更清晰，不是为了结构而结构
- ⚠️ **保留变量占位符** — 如果原始prompt中有 `{{chain}}` `{{interval}}` 等变量，必须逐字保留，不能替换成具体值
- ⚠️ **风控不能虚构** — 如果原始prompt没有止损规则，不要编造一个塞进去。可以加个"TODO: 设置止损"空位，但不要假造参数
- ⚠️ **输出格式要可执行** — 设计的输出格式要保证LLM容易生成且一致。过于复杂的多级嵌套可能导致输出不一致
- ⚠️ **不能丢失原始意图** — 优化后要逐条核对原始prompt的每个指令都在新结构中有对应位置
- ⚠️ **链上数据命令有变化** — GMGN CLI 版本更新可能导致命令参数变化，模板中的命令参考需定期验证
- ⚠️ **node server background模式stdout缓冲** — `node server-entry.js &` 启动后curl无响应，stdout可能被缓冲不输出。改用 `nohup node server-entry.js > ~/workspace.log 2>&1 &` 或先foreground确认启动成功再切background
- ⚠️ **cron job `action=run` 可能只排队不立即执行** — `cronjob action=run` 设置 next_run_at 但不保证立即触发。若scheduler无活跃轮询，job等下次scheduled tick才执行
- ⚠️ **cron技能加载防溢出** — cron prompt必须单prompt自包含，不加载skills（尤其是meme-coin-multi-agent-pipeline这类大技能），否则会话上下文溢出后静默失败
- ⚠️ **女娲蒸馏币圈KOL用快速档** — 币圈KOL主要产出是推文（非书籍/论文），用女娲标准6-agent蒸馏过度且容易超时。改为快速档（3维度：表达+对话+他者）。或直接用twitter search获取推文→手写Skill，比调完整pipeline更可靠
