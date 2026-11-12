# 案例：扫链日报 144K → 3-5K tokens / 次（2026-10-19）

## 改造前

```
4 条/天（5:40 / 13:00 / 19:00 / 23:00）
prompt 4,566 字
挂 6 个 skill（gmgn-onchain-analysis 一个就 136 KB）
36 次工具调用，每次 gmgn-cli --raw 的完整 JSON 进上下文
单条 ≈ 144,000 tokens；一天 ≈ 50-60 万
输出文件 290 KB（其中绝大多数是 skill 全文）
```

## 改造后

```
2 条/天（5:40 + 19:00；13:00 / 23:00 暂停保留）
prompt 1,440 字（只写：跑脚本 + 数据规则 + 输出格式）
挂 0 个 skill
1 次工具调用（python3 ~/.hermes/scripts/daily_scan.py）
单条 ≈ 3,000-5,000 tokens；一天 ≈ 1 万
```

## daily_scan.py 的设计要点（可直接复用）

1. **一次 trenches 调用拿全打分字段**：`market trenches --chain X --type new_creation --type near_completion --type completed --raw`
   返回值里已经有 `market_cap / liquidity / holder_count / volume_24h / top_10_holder_rate /
   bundler_trader_amount_rate / entrapment_ratio / rat_trader_amount_rate / creator_created_count /
   is_honeypot / burn_status / twitter / x_user_follower / buy_tax / sell_tax / created_timestamp`。
   → **不需要对每个代币再调 token info**（这是省 token 的关键，也是省 API 配额的关键）。
2. **硬门槛前置**（不合格的直接丢，不参与排序）：
   `LP<$10K`、`Top10>50%`、`围猎盘>30%`、`bundle>40%`、`持币<200`、`24h量<$50K`。
   实测淘汰率 ~95%（BSC 172/180、SOL 174/180）——说明门槛是硬的，不是安慰剂。
   注意：SOL 未迁移的 pump/curve 币 LP 天然很小，LP 门槛要放到 $10K 而非 $30K，否则会把整条 SOL 链卡光。
3. **同名去重**：同一 ticker 多个地址（仿盘）只留评分最高的一个。不去重时 SOL 一次能出 102 个"候选"。
4. **输出给 agent 的行数上限**：每链 top 5，每币 4 行（指标行 / 亮点 / 风险 / CA）。
5. **链上活跃度用「DEX 成交量 + Fees」，不要用 TVL**（用户 2026-10-19 明确要求替换）。
   TVL 是锁仓量，跟打狗无关；且 `tvl_monitor.py` 拿的 `change_1d/change_7d` 字段对不上，24h/7d 变化恒为 `+0.0%`（假数据）。
   ```python
   LLAMA = ("https://api.llama.fi/overview/%s/%s"
            "?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
   d = fetch_json(LLAMA % ("dexs", "solana"))   # {"total24h":…, "total7d":…, "change_1d":…}
   f = fetch_json(LLAMA % ("fees", "solana"))
   # 输出：SOL: 成交 $1.57B (+25%) | Fees $9.7M (+4%)
   ```
   判读规则（写进 prompt 让 agent 每次念一句）：**成交放大 + Fees 跟上 = 真活跃；成交放大 + Fees 不动 = 刷量**。
   参考量级：SOL 成交/Fees ≈ 161x，BSC ≈ 413x（BSC 手续费更低，或刷量成分更高）。
   四条链端点是 4 次免费调用，不吃 GMGN 配额。

## 调用节流（必须）

```python
MIN_GAP = 6.0                      # 两次 gmgn-cli 之间至少 6 秒
# 429 处理：从错误串里解析 "~Ns remaining"，等 N+12 秒再试（最多 120 秒）
# 网络错误（fetch failed / TLS / socket / timeout）也要重试，间隔 6 秒
```
**每次重试会把 GMGN 的封禁延长 5 秒（最多 5 分钟）**——所以调试时不要反复手敲同一个端点，
一次脚本运行（4 次调用）在正常状态下约 30 秒完成。

## 数据源字段坑（每一条都真实踩过，浪费过整轮调试）

| 坑 | 事实 | 症状 / 正确写法 |
|---|---|---|
| `is_honeypot` 的类型 | 是**字符串** `"no"` / `"yes"`，不是布尔也不是 0/1 | 用 `str(v).lower() in ("no","0","false","none","")`。用布尔或 `in (0,"0",None)` 判断 → **全部 BSC 币被误判成蜜罐** |
| `burn_status` | 同样是 `"yes"` / `"no"` | 别只匹配 `"burned"/"locked"`，否则全部误报"LP未烧" |
| MC 字段在哪 | `token info` **没有** `market_cap`；`trenches` 有 | token info 里用 `price.price × circulating_supply`（回退缩 `total_supply`），否则 MC=0、MC 档位标签全错 |
| `trending` 结构 | `{"code":0,"data":{"rank":[...]}}` | 不是数组、也不是 `data[]`；写成 `.data[0]` 会解析失败 |
| `price_change_percent1h` | **已经是百分数**（-98.66 表示 -98.66%） | 再 ×100 会出现 `1h -9866%` 这种明显错误 |
| trending 字段厚度 | 没有 bundle / 围猎 / dev 发币数 / 税 | trending **只能做"热度榜"一行**，打分必须用 trenches |
| `market trenches --type` | 可重复传，一次拿三类 | `--type new_creation --type near_completion --type completed` |

## 验证清单

- [ ] `jq '.jobs[]|select(.id=="<id>")|.skills'` 为空
- [ ] `wc -c` 看新输出文件是否从 ~290 KB 降到 ~40 KB 以下
- [ ] 脚本单跑一次，两链都出数据（不是"数据源失败"）
- [ ] 改造后跑一次 cron，`hermes insights --days 1` 的 total tokens 应下降一个数量级
