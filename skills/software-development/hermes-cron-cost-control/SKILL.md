---
name: hermes-cron-cost-control
description: |
  Design, audit, and refactor Hermes cron jobs so they cost as little token as possible.
  Use when the user complains about token spend ("太费token了"), when a recurring LLM job
  runs daily and burns balance, when designing a new scheduled report, or when auditing
  why a cron job is expensive. Covers the measured cost anatomy (skill injection is the
  #1 hidden cost), the script-pre-digestion pattern, no_agent conversion, frequency
  reduction, and the audit commands.
  Triggers: 费token / token 成本 / 日报太贵 / 优化 cron / 少花钱 / 成本审计.
---

# Hermes Cron 成本控制

> 核心原则：**确定性工作交给脚本，LLM 只做判断和写作。raw JSON 永远不进上下文。**

用户对 token 成本极度敏感（会直接叫停任务）。任何"每天跑一次的 LLM cron"都必须按本文件设计。

## 成本解剖（实测，2026-10）

一个"扫链日报"cron 的真实构成：

| 成本项 | 体积 | 约合 tokens | 说明 |
|---|---|---|---|
| **skill 全文注入** | **136 KB** | **~40,000** | `gmgn-onchain-analysis` 一个 skill 就这么大，**每次运行都注入** |
| prompt | 4,566 字 | ~2,500 | |
| 36 次工具调用 + `--raw` 输出 | 几千行 JSON | ~100,000 | 每个候选代币的完整 JSON 都进上下文 |
| **单次合计** | | **~144,000** | |

**最大的浪费通常不是聊天，是 skill 注入和 raw JSON。** 先查这两项，不要一上来就减功能。

## 六个杠杆（按收益排序）

### 1. 卸掉 cron 上的 skill（往往是最大一笔）
如果脚本已经做完了确定性工作，agent 根本不需要那些 API 文档：

```python
cronjob(action="update", job_id="<id>", skills=[])   # 清空
```

验证：`jq -r '.jobs[]|select(.id=="<id>")|.skills' ~/.hermes/cron/jobs.json`

判断依据：**cron 输出文件大小 ≈ prompt + skill 注入量**。
```bash
ls -t ~/.hermes/cron/output/<job_id>/*.md | head -3 | xargs wc -c
```
单个输出文件 200-300 KB → 说明 skill 注入很重（正文只有几 KB）。

### 2. 脚本预消化（把 raw JSON 挡在上下文外）
写一个脚本，一次调用输出 **30 行以内的紧凑摘要**，agent 只读它。
参考实现：`~/.hermes/scripts/daily_scan.py`（双链扫链 + 硬门槛 + 打分 + 去重 + TVL，输出 ~30 行）。
效果：工具调用 36 次 → **1 次**；单次 ~144K → **~3-5K tokens**。

### 3. prompt 瘦身到 ≤1500 字
只写三件事：① 跑哪个脚本 ② 数据规则（禁止编造数字/CA 照抄）③ 输出格式。
把"怎么扫链/怎么调 API"全部删掉——那是脚本的事。参考：`~/.hermes/cron/prompts/lean-report-v2.md`。

### 4. 能 no_agent 就 no_agent（零 LLM）
纯确定性的任务一律 `no_agent=True` + `script=`：
阈值告警（`price_watch.py`）、交易记录（`trade_log.py`）、余额看门狗、备份、Token 日报。
**静默语义**：脚本无输出 = 不推送（watchdog 模式）；非零退出 = 错误告警。

### 5. 减频而不是减内容
4 条日报/天 → 2 条（早盘 + 晚盘）。先保住内容和格式，砍次数。
暂停用 `cronjob(action="pause")`，不要直接删（用户要求留可恢复的备份态）。

### 6. 压缩链路必须是通的
`compression` 模型挂掉时（provider 403/余额），Hermes 会**静默跳过压缩**，上下文只增不减
→ 每一轮都重发全部历史 → 成本指数上升。症状：`⚠ Compression aborted: ... No messages were dropped`。
排查：`hermes config get auxiliary.compression`，再实测该 provider 的 chat 端点。

**第二种失败：`hermes auth` 凭证池里有失效 key。** 症状是
`401 Authentication Fails, Your api key: ****xxxx is invalid`，而主对话完全正常——
因为主模型用 config 里的 key，辅助调用（compression / title_generation）走的是**凭证池**，
按顺序逐个尝试，第一个是早期手动加的旧 key 就直接 401。

```bash
hermes auth list                          # 每个 provider 下列出所有凭证，失效的会标 auth failed (401)
hermes auth remove deepseek api-key-2     # 按 label 删掉失效的，只留 env:DEEPSEEK_API_KEY
hermes auth status deepseek               # 应显示 logged in
```
删完务必发一次真实请求验证（不能只看 status）：
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE/chat/completions" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```
判据：一个 provider 应该**只留一个**有效凭证。留多个迟早踩到失效那个。

### 7. 空跑也要计费：给周期性 agent cron 加早退
每 2 小时跑一次的 agent cron，即使无事可做也要付「prompt + 一次工具调用」的钱（实测 ~1.5K tokens/次 × 12 次/天）。
pattern：**脚本零输出时让 agent 只回 `[SILENT]`**（Hermes 视为静默，不推送）。prompt 里写死：

```
1. 先跑 python3 <script>
2. 若它没有任何输出（队列为空）→ 只回复 [SILENT]，不要多说一个字
3. 有输出 → 按格式写
```

配合脚本侧「没有待处理项就直接 return（零输出）」，空跑成本压到最低。
配套：给这类 job 设 `enabled_toolsets=["terminal"]`，少加载无关工具的定义。

### 8. 事件驱动优于定时轮询
「每 15 分钟查一次公告」这种可以拆成两层：
- **检测层**：`no_agent` 脚本，零 token，有变化才推送（见杠杆 4 的静默语义）
- **分析层**：agent cron，低频（每 2 小时）+ `[SILENT]` 早退
千万别让带 LLM 的那一层跑高频。

**但先问要不要建，别默认建。** 用户说「以后币安出现 TGE 帮我分析一下」听起来像常驻指令，
实际建成两层架构后他的回答是「**算了还是费钱，我刷X看见了你给我分析就行了不用监控了**」，两个 job 当场删掉。

所以要固化这个顺序：
1. 先把**成本**说清楚（检测层 0 token；分析层 ~1.5K/次 × 12 次/天 ≈ 15K tokens/天）
2. 问一句「要常驻还是我等你发我就分析」——一句话的成本，省掉建完再拆
3. 默认形态是 **on-demand**：脚本留着当手动工具，**不挂 cron**；用户贴链接/币名时现场跑一次
4. 只有他明确说「要监控/帮我盯着」才建 job

### 9. 常驻成本：装上去的 skill 每轮都在收费

不只是 cron —— **每个已装 skill 的描述都进每轮上下文**，跟跑不跑 cron 无关。

实测（2026-10-20）：一次装了 9 个 `binance-*` skill（仓库 21 个里挑 9 个），
SKILL.md 总量 ~218 KB，但**每轮固定成本只是描述** ≈ 800-1200 tokens/轮；
按 30 轮/天算 ≈ 25-35K tokens/天（约 ¥0.1-0.2/天）。单看不多，但它是**永远在付**的。

规矩：**按需保留，用完就关** —— 一个月用不到一次的 skill 不该常驻。

```bash
hermes config set skills.disabled '["skill-a","skill-b"]'
hermes skills list --enabled-only | grep -c <关键词>     # 必须验证数量真的降了
```

⚠️ **实测坑**：`hermes config set` 把 JSON 数组**存成字符串**，而 `skills_config._normalize_skill_names`
遇到字符串会当成**单个 skill 名** → **静默失效**（配置写了，`--enabled-only` 里照样全在），
同时提示 `is not a recognized config key`。改完必须验数量；不生效就走删除：
`~/.hermes/skills/<name>` 是指向 `~/.agents/skills/<name>` 的软链，**两处都要删**。

删除属破坏性操作，审批超时被拦时**不要重试同一命令**（也不要用「换个写法」绕过），
把一行命令交给用户自己跑，然后继续。

## 审计：怎么证明「这个 job 真的不花 token」

用户会追问「确定不耗 token？」——不要只回一句「确定」，给三条可验证的证据：

```bash
# ① 配置层：没有模型参与
jq -r '.jobs[]|select(.id=="<id>")|"no_agent=\(.no_agent) model=\(.model // "null") provider=\(.provider // "null")"' \
  ~/.hermes/cron/jobs.json
# → no_agent=true  model=null  provider=null

# ② 执行层：每分钟都在跑，但只是脚本
sqlite3 ~/.hermes/cron/executions.db \
  "select job_id,status,started_at,finished_at from executions order by rowid desc limit 5"
# → status=completed，单次耗时 3-6 秒

# ③ 计费层：sessions / session_model_usage 里查不到它
sqlite3 ~/.hermes/state.db "select count(*) from sessions where id like 'cron_<job_id>%'"   # → 0
```

三条都过 = 结构上不可能产生 token。**no_agent 的 job 不进模型，也不创建 session**，
这是它和「agent cron 空跑」最本质的区别（后者每次至少付 prompt + 一次工具调用）。

### insights 的 total tokens 会骗人
`hermes insights --days 1` 的 Total tokens **把 cache_read 也算进去了**。
实测某天两条日报显示 146,662 tokens，看着像烧钱，拆开是
`input 26,924 / output 14,650 / cache_read 105,088` —— 缓存单价只有正常的 1/10 左右。

**报成本一律用 `session_model_usage.estimated_cost_usd`：**
```sql
select session_id, api_call_count, input_tokens, output_tokens,
       cache_read_tokens, round(estimated_cost_usd,5)
from session_model_usage order by last_seen desc limit 5;
```
实测（2026-10-20）：早报 5 次 API ≈ $0.0058，晚报 3 次 API ≈ $0.0024，合计 **≈¥0.06/天**。
给用户报「一天多少钱」时用这个数，不要用 insights 的 total（会把人吓到）。

### 查历史会话的坑
`sessions.started_at` 是 **epoch 浮点数**，不是 ISO 字符串 →
`where date(started_at) = date('now')` 永远返回空。按 epoch 比较，或直接 `order by rowid desc` 取最近几条。

## 审计流程（拿到"太费token"的抱怨时照做）

1. `hermes insights --days 1` —— 看 sessions / tool calls / total tokens / "Most tokens" 会话
2. 定位是哪类会话贵：
   - `cron_*` = 定时任务 → 走上面六个杠杆
   - 交互会话贵 = 上下文太长 → 建议 `/new`，并检查压缩是否生效
3. 对可疑 cron：
   ```bash
   jq -r '.jobs[]|select(.id=="<id>")|"\(.name) skills=\(.skills|length) prompt=\(.prompt|length)"' \
     ~/.hermes/cron/jobs.json
   ls -t ~/.hermes/cron/output/<id>/*.md | head -1 | xargs wc -c
   ```
4. 改造后**跑一次验证**，再对比 insights 的 total tokens。

## 坑

- **不要用"减功能"当第一手段**。用户要的是"同样的报告、更少的钱"。先卸 skill、再预消化、最后才减频。
- **改 cron prompt 要走脚本**：`jobs.json` → 精确替换 → `hermes cron edit <id> --prompt`。多条长 prompt 直接在对话里重发既贵又容易出错。改前把旧 prompt 备份到 `~/.hermes/cron/prompts/backup-<id>-<日期>.md`。
- **数据源限流要写在脚本里**：GMGN 连续调用会 `429 RATE_LIMIT_BANNED`，且**每次重试会把封禁延长 5 秒**（最多 5 分钟）——所以重试间隔必须 ≥ 呼叫间隔（实测 6 秒间隔 + 按提示退避可用）。别在调试时反复手敲同一个接口。
- **网络类错误也要重试**：只判断 `429` 会漏掉 `fetch failed / TLS / socket` 这类偶发断连，导致整条链"扫描 0 个"。
- **辅助模型（compression/vision/web_extract/approval）用的是另一套 key**：中转服务（如 wawazz.xyz）的"分组"被删会让这四块一起 403。`approval` 挂了的表现是"命令老是被审批超时拦掉"——不是审批慢，是判定模型死了。切换：`hermes config set auxiliary.<块>.provider deepseek` + `...model deepseek-v4-flash`（四个块逐个设）。
- **config.yaml 有写保护**：`patch` / `write_file` 改 `~/.hermes/config.yaml` 会被拒（security-sensitive config）。一律走 `hermes config set <key> <value>`，改完 `hermes config check`；改动在网关重启后生效。**agent 不能自己重启网关**（`cronjob` 或脚本里带 restart/stop/kill 会被 block）——把命令交给用户：`hermes gateway restart`。
- **`skill_view` 大技能会淹上下文**：本机 `gmgn-onchain-analysis` 约 136 KB。只想看结构时先 `skills_list`，或直接读 `references/` 下的子文件，不要整篇 view。
