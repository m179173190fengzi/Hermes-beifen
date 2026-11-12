---
name: cron-job-diagnostics
description: Diagnose why a Hermes cron job didn't fire or didn't deliver (missed reports, silent jobs, "日报怎么还没发"). Use when user asks why a scheduled report/backup/watchdog hasn't arrived.
---

# Cron Job Diagnostics

## Trigger
用户问"X 怎么还没发 / 没跑 / 没收到"——定时报告、日报、备份、watchdog 等 cron 任务。不要凭 `cronjob list` 的 `last_status` 直接下结论：**运行中的任务 `last_run_at` 还没更新，会显示上一次的旧值**，看起来像"没跑"。

## Diagnostic flow

1. `cronjob list` → 找到 job_id，判断是否已触发：
   - **`next_run_at` 已经跳到下一个时间点** = 该次任务已触发过（正在跑或已完成）
   - `last_run_at` 仍是旧时间 + `last_status=error` = 可能还在跑，也可能失败——不能只看这里

2. 看输出目录：
   ```
   ls -lt ~/.hermes/cron/output/<job_id>/
   ```
   - 最新文件 mtime = 上次完成写出的时间
   - 没有预期时间点的新文件 = 任务未完成

3. 查 agent.log 跟踪实时进度：
   ```
   grep -a "cron_<job_id>_<yyyymmdd_hhmmss>" ~/.hermes/logs/agent.log | tail
   ```
   日志前缀 `[cron_<job_id>_<触发时间戳>]` = 该次运行的 session ID。关键标记：
   - `agent.conversation_loop: API call #N` = 还在跑
   - `Turn ended: reason=text_response` = agent 已完成
   - `cron.scheduler: Job '<id>': delivered to telegram:<uid> via live adapter` = 已送达 ✅

4. 若日志显示已送达但用户没收到：查 gateway.log 的 Telegram 网络错误。`httpx.RemoteProtocolError: Server disconnected` + `reconnecting in 5s (attempt N/10)` 是自动重连的正常重试，等它恢复即可，不用干预。

## Key gotchas

- **cronjob list 的 `last_run_at` 只在任务完成后更新**。任务正在跑时它显示上一次的旧时间——这是"任务没跑"的最大假象来源。
- **慢 provider 是常态**：DeepSeek 每次 API 调用延迟 20-90s，16 次调用的日报任务要 10-15 分钟。改时间后第一次运行慢是正常的，别过早判失败、别重复触发。
- grep 无匹配时 exit code=1，terminal 会显示为 error——这是 grep 的正常行为，不是命令失败（加 `|| true` 或只看输出）。
- 长任务等待：一次 `sleep 60-90` + 一次 grep，比连续多次短 grep 高效，还能避免触发 tool-loop 警告。

## 投递可靠性：no_agent 任务的投递层没有重试

`no_agent` 任务的机制是「跑脚本 → stdout 原样投递」。**投递这一层不重试**：网络抖动一次
（`last_delivery_error: delivery error: Telegram send failed: httpx.ConnectError: All connection attempts failed`）
那条消息就永久丢了，而 `last_status` **仍然是 `ok`**（脚本本身成功了）。

**关键任务（备份、日报、告警）不要让调度器投递，让脚本自己发**：

1. 脚本内把进度累积到变量（`LOG`），**不要 echo 到 stdout**
2. 结尾用 Bot API 自己发送，**指数退避重试 5 次**（15/30/45/60/75s），发送带 `HTTPS_PROXY` 前缀
3. 成功 → **stdout 保持空**（调度器静默，从此不再出现投递错误）
4. 全部重试失败 → 才打印一行短提示，让调度器兜底再试一次（双保险）

脚本骨架（含 git push 重试、token 从 `~/.hermes/.env` 读取）：
`references/delivery-reliability.md`。

⚠️ **这类脚本不要用 `set -e`** —— 中途任何一步失败就直接退出，**连"发送报告"那步都到不了**，
用户什么都收不到。用 `set -uo pipefail` + 每步 `|| true` 或显式判断。

## 任务失败（`last_status=error`）：原因在输出文件末尾，不在 list 里

`cronjob list` / `jobs.json` 只标 `error`，**具体原因要读该次运行的输出文件**：

```bash
F=$(ls -t ~/.hermes/cron/output/<job_id>/* | head -1); echo "$F"; tail -c 900 "$F"
# 文件末尾会有 "## Error" 段
```

实测最常见的两类：

| 错误体 | 含义 | 处理 |
|---|---|---|
| `RuntimeError: HTTP 402: Insufficient Balance` | **provider 余额耗尽** —— 不是配置/网络/prompt 问题 | 查余额 → 充值 → **其余什么都不用改** |
| `HTTP 401` / `invalid api key` | 凭据被换或失效 | 换 key + 重启网关 |
| `HTTP 403 {"code":"GROUP_DELETED","message":"API Key 所属分组已删除"}` | **中转服务（wawazz 这类 relay）的套餐/分组被删**，该组下所有 key 一起失效 | 换 provider，见下节 |

### 403 GROUP_DELETED 的连带伤害：辅助模型全挂（表现为"工具审批总超时"）

`auxiliary.*` 下的辅助模型（`compression` / `vision` / `web_extract` / `approval`）可能全部指向同一个中转
provider。那个分组被删时，症状分散且很难联想到病因：

| 症状 | 真实原因 |
|---|---|
| 长会话报 `Compression aborted: HTTP 403 ... GROUP_DELETED`（消息没丢，但上下文不再压缩 → 之后每轮都变贵） | `auxiliary.compression` 的 provider 死了 |
| **命令老是被"审批超时 / 被拦"**，用户以为审批流程慢 | `auxiliary.approval` 是同一个死 provider：调用 403 → 无人判定 → 拦掉 |
| 发图片无反应 / web_extract 失败 | `auxiliary.vision` / `web_extract` 同样 |

诊断：
```bash
hermes config get auxiliary.compression          # 看 provider/model
grep -n "provider:" ~/.hermes/config.yaml | head # 揪出指向同一 relay 的项
# 直接打 provider 端点确认 key 是否整组失效（返回 403 GROUP_DELETED 即坐实）
curl -s -o /dev/null -w '%{http_code}\n' -X POST "<base_url>/chat/completions" \
  -H "Authorization: Bearer <key>" -H 'Content-Type: application/json' \
  -d '{"model":"<model>","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

修复（**config.yaml 有写保护**，patch/write 工具会被拒，必须走 CLI）：
```bash
hermes config set auxiliary.compression.provider deepseek
hermes config set auxiliary.compression.model deepseek-v4-flash
# vision / web_extract / approval 同理逐项切
hermes config check
hermes gateway restart      # agent 不能自己重启网关，给用户命令让他执行
```

⚠️ `approval` 修好之后，之前为绕审批而"必须写成脚本文件"的绕法就可以放松了 —— 那些拦截本来就是死 provider 造成的。
⚠️ 新 provider 若没有视觉能力（DeepSeek 就没有），`vision` 仍不可用（报"模型不支持图片"），要另配视觉 provider。

⚠️ **余额类失败是静默的**：job 只在 `last_status` 上标 error，不会主动说"我没钱跑"。
实测同一早上一连挂 3 次（5:40 / 13:00 / 23:00），用户只看到"日报没来"。

→ 对策：挂**余额看门狗**（`balance_watch.py` 思路：每小时查 provider 余额，低于阈值才发声，平时完全静默）。
**阈值不要设 ¥1** —— 重度使用下从 ¥1 掉到 0 只够十几分钟，等它报警已经错过整轮定时任务。
按「半天到一天的用量」设（成本敏感用户建议 ¥5 量级）。

## 没有输出文件时：查执行库 executions.db

任务还在跑、或失败到连输出文件都没写，就读执行库。**机器上通常没有 `sqlite3` CLI**，
用本 skill 附带的脚本（拷到 `~/.hermes/scripts/` 或直接跑）：

```bash
python3 scripts/cron_runs_query.py <job_id> 5
# 输出：状态 + 起止时间 + error 文本
# status=running 且 end 为空 → 还在跑，别重复触发
```

对应 `hermes cron runs` 的表格版；脚本版能一次筛单个 job 并直接带出 `error` 字段。

## 假成功：job 报 ok，其实什么都没做

`last_status=ok` 只说明脚本/agent 正常退出，**不说明它做了有用的事**。
实例：备份脚本连续两个月报 `ok`，但备份源是 `~/.hermes/memory/`（**单数，7 月的死目录**），
真实记忆在 `~/.hermes/memories/`（**复数**）——于是一直复制一个不再变化的旧文件，
git 仓库因此两个月没有新提交（一直走"无变更，跳过提交"分支），任务却天天报成功。

**排查法（任何"备份/同步"类任务都适用）**：
1. `diff -q <live> <backup>` —— 目标文件很旧 / 内容一致但源已变 = 源路径可疑
2. `ls -la <src>` 确认源存在且有内容；**相似目录名（单复数 `memory` vs `memories`）逐一核对**
3. 同步任务**长期**报"无变更" = 要么真没变，要么源路径错了
4. `git log --oneline -5`：最后提交时间远早于任务运行时间 = 假成功

## 备份类任务的密钥卫生（踩过一次真事故）

自动备份有两种"看起来没坏、其实坏了"：源路径写错（见上节），以及**把凭据文件推到了公开仓库**。
后者实测发生过：备份脚本把含 Telegram Bot token / OpenRouter / DeepSeek / API-server 密钥的
env 副本明文推送上去，任务天天报 `ok`，而那个仓库其实是 **public**，持续约 3 个月。

规则：
1. 备份脚本**永不复制 env / 凭据文件**。需要留痕时只导出 key 名：
   ```bash
   grep -oE '^[A-Z_0-9]+=' "$HERMES_HOME/.env" | sed 's/=$/=<REDACTED>/' > config/env-keys-only.txt
   ```
2. 顺手核实仓库可见性（别信"我建的是私有"）：
   ```bash
   # 200 = 公开（任何人可拉），404 = 私有
   curl -sI -o /dev/null -w "%{http_code}\n" https://github.com/<owner>/<repo>
   ```
   用网页 HEAD；`api.github.com` 在共享出口 IP 上常返 403 限流，会误判成"查不到"。
3. **确认泄露后：先轮换密钥，再清历史。** 清历史收不回已被抓走的凭据，顺序反了等于白做。
4. 清历史（backup repo 可安全重写，工作区数据不丢）：
   ```bash
   export FILTER_BRANCH_SQUELCH_WARNING=1
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch <path>' --prune-empty --tag-name-filter cat -- --all
   rm -rf .git/refs/original && git reflog expire --expire=now --all && git gc --prune=now
   git log --all --oneline -- <path> | wc -l   # 必须 = 0
   git push origin main --force
   ```
5. ⚠️ force-push 改写所有 commit SHA，且 GitHub 服务端仍会缓存旧 blob 一段时间 ——
   再次说明**轮换密钥才是第一步**。

## 排期形状的坑

- **一条 cron 表达式没法让不同小时用不同分钟**（分钟只有一个字段）：`5:40` 和 `13:00` 必须
  **拆成两个 job**，各存一份 prompt。别指望 `40 5,13 * * *` 之类能表达"5点40+13点整"。
- 用户要"每个时段都是完整版"时，就是把同一份完整 prompt 复制到各时段 job —— 内容重复是可接受的，
  比在一个 job 里塞条件分支可靠。

## 批量改多条同款任务的 prompt（省 token 的做法）

多条 job 共用同一份 prompt 时（见上节），要改同一处**不要**把整份长 prompt 重发 N 遍
（3 条 ≈ 上万 token）。写个一次性脚本：

1. 读 `~/.hermes/cron/jobs.json`，按 job id 取出当前 prompt
2. 对目标段落做**精确字符串替换**——先断言旧片段存在，找不到就跳过并报告，**别盲写**
3. 对每个 job 调 `hermes cron edit <job_id> --prompt "<新完整 prompt>"`
4. 验证：`jq -r '.jobs[]|select(.id=="…")|.prompt' jobs.json | grep -c "<新标记>"` 每条都应为 1

⚠️ **不要直接改写 jobs.json**：调度器进程在跑，绕过 `.jobs.lock` 有被覆盖的风险，必须走 `hermes cron edit`。
参考实现：`~/.hermes/scripts/patch_report_prompt.py`。

### 用户在"做减法"时的处理方式（实测会连续好几轮）

报告类 cron 的用户行为模式：**先加满功能，然后一轮一轮砍**（"取消成交量TOP5" → "取消观察名单" →
"取消推特热搜" → "取消 fomo 热门榜" → "条目里的 🐦 链接也删"）。每轮都要：

1. **先读当前 prompt 原文再改**（`jq -r '.jobs[]|select(.id=="…")|.prompt'`），按**行/精确片段**移除，
   不要凭记忆重写整份 prompt。
2. **多行块要整体删**：以 `{把 ...` 开头、以 `}` 结尾的输出块跨多行，用"进入块 → 见到行尾 `}` 退出"的状态机删，
   删完 `re.sub(r"\n{3,}", "\n\n")` 压掉多余空行。
3. **Workflow 里的步骤要重新编号**（删掉第 1、2 步后把 3-8 改成 1-6），否则下次 agent 会读到跳号指令。
4. **改完必须验证 0 残留**：
   `jq -r '.jobs[]|select(.id=="…")|.prompt' jobs.json | grep -c "<被删的关键词>"` → 每条都应是 `0`。
5. **"取消任务"≠ 立刻物理删除**：先把定义导出成备份再删，方便一句话重建——
   ```bash
   jq '[.jobs[] | select(.id=="<id1>" or .id=="<id2>")]' ~/.hermes/cron/jobs.json \
     > ~/.hermes/cron/prompts/<name>-backup-$(date +%Y%m%d).json
   ```
   备份文件里含 schedule + script + prompt，用 `hermes cron create` 就能还原。
6. **脚本不要跟着删**：停用/删除 job 后，`~/.hermes/scripts/` 里的实现脚本保留——恢复时只需重挂 cron。

## Token 成本：日报类任务最容易失控的地方

用户抱怨「太费 token / 充 10 块一天用掉一半」时，走 `references/token-cost-optimization.md`：

1. `hermes insights --days 1` 量化，看 `Notable Sessions` 里 tool calls / tokens 最多的 `cron_<job_id>`
2. 先砍频次（4 条/天 → 2 条/天，暂停中间时段），再谈重构
3. 主改造是**脚本预消化**：脚本干完扫描/硬门槛/打分/去重，输出 30-60 行摘要，agent 只写叙事
   （实测 36 次工具调用 → 1 次，单次 ~144K → ~15K tokens）
4. 看门狗/阈值告警一律 no_agent（零 LLM 成本）
5. 上下文压缩必须活着（见 `403 GROUP_DELETED` 一节），长会话及时 `/new`

核心结论：**成本在「raw 数据进上下文」，不在「写报告」**。

## 「活了么 / 好了吗」：两三个字的状态探针

用户常用两三个字问状态（"活了么"、"好了吗"，甚至打字走样成 `huo l mav` / `好了ma`）。
**不要反问"你指的是哪个"、不要长篇解释** —— 直接跑探针，给结论 + 数据：

```bash
systemctl --user is-active hermes-gateway      # active = 活着
hermes --version                                # 没变就别提议升级
jq -r '.jobs[] | "\(.enabled) \(.name) [\(.id)] \(.schedule.expr // .schedule)"' ~/.hermes/cron/jobs.json
python3 ~/.hermes/scripts/token_daily.py        # 今日花费（脚本存在时）
```

⚠️ **`jobs.json` 里的 `last_run` / `last_status` 可能整列为空或显示 `无`，这不等于"没跑"**
（调度器不保证回写）。判断"今早那份到底发没发"只能靠**运行痕迹**：

- `session_search()` 浏览最近会话，找 `cron_<job_id>_<YYYYMMDD_HHMMSS>`，时间对得上 = 跑过
- 要判断**内容质量**（不只是送达），读该 cron session 的最后一条 assistant 消息 —— 那就是投递出去的原文，
  报告里的口径矛盾/自相矛盾的数字只有在这里才看得到

回复形状（该用户偏好）：一句结论（活着 / 发出来了 / 卡在哪）→ 3-5 行数据（版本、enabled 的 job、
今日花费、上次完成时间）→ 一句风险提醒（如果有）。别加小标题层级、别写"以下是…"。

## Verification
向用户确认"已发出"前必须两个证据齐全：
1. `~/.hermes/cron/output/<job_id>/` 出现该时间点的新文件
2. agent.log 有 `delivered ... via live adapter`

回复格式：结论先行（发出来了/还在跑），数据随后（触发时间 → 完成时间 → 投递时间，以及慢的原因）。
