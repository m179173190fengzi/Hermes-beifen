# 把 X / 热度榜数据嵌进定时日报（脚本出块、agent 只粘贴）

实测环境：Hermes cron「BSC+SOL链上合成报告」（`fa0df7d27b24`，每天 5:40 / 13:40，**LLM 驱动**）
+ 两条 `no_agent` 脚本 cron（X 账号监控 20 分钟、X热议↔热度榜 6 小时）。

核心原则：**数据由脚本产出（确定性、零 token、可复现），agent 只负责搬运与一句话解读。**
让 agent「自己去查/自己总结」既贵又会漂移，还会在源挂掉时编数据。

---

## 1. 产出块脚本（`~/.hermes/scripts/`）

| 脚本 | 输出 | 数据源 / 要点 |
|---|---|---|
| `fomo_top5.py` | 「━━━ 🔥 fomo 热门代币 TOP5 ━━━」块 | `POST https://prod-api.fomo.family/proxy/trendingTokens`（需登录 cookie）。默认 20 分钟 TTL 缓存；cookie 失效时输出**「暂不可用」一行**而不是抛错 |
| `x_hot_brief.py` | 「━━━ 🐦 推特热议 项目/代币 ━━━」块 | 首页时间线（`twitter feed`）+ fomo/GMGN 热度榜交叉；见下方「feed 回退」 |
| `tvl_monitor.py` | TVL 数值 | 取 SOL + BSC 两项 |

脚本共同点：内部自己设 `HTTPS_PROXY`，**不依赖调用方 export 环境变量**；失败时打印一行人话，
让报告优雅降级而不是整篇报错。

### 块内格式约定

- 每行 `#N SYMBOL (链) 源#排名 | MC | 涨跌 | 量 | 持币`，下一行 `CA: <完整地址>`。
- 交叉命中额外一行 `↳ 热议来源: @handle 时间`（可追溯，这是「证据」而不是「结论」）。
- **热议词只认项目名/代号**：`$TICKER` 权重 3 分、出现 ≥2 次的拉丁大写词计 1 分，
  **纯 CJK 连续字不要当热议词**（实测会抓到「高速/数分/注文」这类日文碎片，全是噪声）。

---

## 2. cron prompt 里怎么写

在 Output Format 段插入两处「{…}」占位，并对 agent 下这三条硬规则：

```
{把 `python3 /home/wei/.hermes/scripts/fomo_top5.py` 的输出原样整段粘贴，
 它自带标题；末尾加一行 📊 解读：这5个里有没有本链的、与当前叙事的呼应
（一句话，没有就写"与当前热点无直接呼应"）}
```

1. **原样粘贴**，不要把数据重新排版/重算。
2. 脚本输出「暂不可用 / 获取失败」时**保留该行**，禁止编造或省略（否则用户以为源正常）。
3. 解读**最多一句话**，且**必须允许"无呼应"**——不给「硬编故事」留空间。

同时在 Workflow 第 1、2 步把它列为**必跑**（放最前面，agent 不容易漏）。

---

## 3. ⚠️ 最大坑：prompt 删不掉 skill 文档注入的段落

**实测事故**：用户要求日报「取消观察名单」。我在 prompt 里把该段删掉并写明「只列 ≥70 分准推级」，
**下一次报告里观察名单照样出现**。

根因：那段**不是 prompt 定义的**，是 cron 加载的 `gmgn-onchain-analysis` skill 文档里写着
「观察名单可下探 55-59 基础分」「准推不足 3 条时用观察名单补齐」，agent 照 skill 执行。

修法 —— prompt 里加**显式覆盖声明**（必须点名 skill）：

```
6. 🚫 禁止输出观察名单：只列 ≥70 分的准推级标的。60-69 观察级、55-59 补充名单一律不列不提。
   ⚠️ 这条【优先于任何 skill 文档里的规则】——skill 里可能写"观察名单可下探 55-59"
   "按分数列出 60-69 观察级""准推不足时用观察名单补齐"，本 prompt 一律不执行。
   内部仍要算分数，但 <70 分的结果不出现在报告里。
```

**通用教训：cron prompt 与注入的 skill 文档冲突时，只有 prompt 里显式声明「优先于 skill」才能赢。**
排查顺序：报告里出现你没要求的段落 → 先 `grep <段落关键词> ~/.hermes/cron/jobs.json`（0 命中 = 不是 prompt 写的）
→ 再去加载的 skill 文档里找（命中 = skill 注入）。

---

## 4. `twitter feed` 回退（否则这一段会随机空缺）

`feed` 会间歇性返回 `Twitter API error (HTTP 0) … Query: Unspecified`，而同一分钟的 `user-posts` 正常。
实现：**重试 3 次（间隔 5s）→ 仍失败则对名单内每个 handle 跑 `user-posts` 合并成伪时间线**，
并在输出里注明 `📡 数据源: 首页时间线（N 条）` 或 `关注账号轮询(备用源)`。

---

## 5. 限流保护：TTL 缓存 + 跨运行去重

- **TTL 缓存**（fomo 的 Cloudflare 对探测很敏感，实测连续猜路径 6 次就吃 `error code: 1015`）：
  把响应缓存到 `~/.hermes/cron/state/fomo_trend_cache.json`，**20 分钟内复用**；
  多个脚本**共用同一个缓存文件**，避免各自打接口。
- **跨运行去重**（告警类）：`~/.hermes/cron/state/x_watch.json` 存每个账号最近的 tweet id
  （保留 N 条即可），只推「没见过 + 命中条件」的，无命中则**完全静默**（`no_agent` cron 的空 stdout = 不推送）。
- 状态文件位置与 delta 报告规范见 `cron-state-persistence`。

---

## 6. 交付前自检

- [ ] 手动跑一遍每个块脚本，确认能出真实数据（而不是只测 agent 的报告）
- [ ] 确认脚本在**源挂掉时**输出的是可读提示行，不是 traceback
- [ ] 报告段里没有出现「你没要求但 skill 文档要求的段落」
- [ ] `no_agent` 告警脚本空命中时 **stdout 为空**（否则会变成定时刷屏）

---

## 7. 同时改多个日报 / 新增时段：别重发 prompt，用脚本改 jobs.json

同一个日报往往有多份**完全相同的 prompt**（实测 5:40 / 13:00 / 19:00 / 23:00 四条，每条 prompt 5.2KB）。
每次改一处都重打一遍 prompt 会烧掉上万 token —— 改成**读 `~/.hermes/cron/jobs.json` → 精确替换 → 写回**：

```python
jobs = json.load(open(os.path.expanduser("~/.hermes/cron/jobs.json")))
for job in jobs["jobs"]:
    if job["id"] not in TARGETS: continue
    p = job["prompt"]
    if NEW_ANCHOR in p: continue                 # 幂等：已改过就跳过
    if OLD_ANCHOR not in p: fail.append(job["id"]); continue   # 锚点失配要报错，别盲改
    subprocess.run(["hermes", "cron", "edit", job["id"],
                    "--prompt", p.replace(OLD_ANCHOR, NEW, 1)], ...)
```

- **锚点选一段独一无二的文字**（实测有效锚点：「末尾加一行 📊 解读：…」），替换前先断言存在。
  跑完逐条验证：`jq -r '.jobs[]|select(.id=="<id>").prompt' jobs.json | grep -c "<新锚点>"` 应等于 1。
- **抄一份现有配置**（新时段 / 换链）：直接复用源 job 的 prompt + skills，
  `hermes cron create "<sched>" "$(jq -r '.jobs[]|select(.id=="<源id>").prompt' jobs.json)" --name ... --deliver origin --skill ...`（skills 逐个 `--skill` 传）。
  别手打 prompt；`hermes cron create` 的 positional 是 `schedule` 然后 `prompt`。
- **⚠️ cron 单条表达式的「分钟」只有一个字段**：`40 5,13 * * *` = 5:40 + 13:40。
  想改成「5:40 与 13:00」**必须拆成两个 job**（`40 5 * * *` + `0 13 * * *`），别指望一条表达式混分钟。
- **点名大户的买入块要在 prompt 里定性**：写「这是盈利榜第一名的链上买入记录，**属于参考信号**，
  如实输出但注明不是推荐」——否则日报会被读成跟单建议（本用户明确不跟单）。
- 用户会**逐次加段**（先加 fomo 热门 → 再加推特热议 → 再加某大户买入）。每次只动那一处锚点，
  其余段落保持字节级不变，避免 4 份 prompt 互相漂移。
