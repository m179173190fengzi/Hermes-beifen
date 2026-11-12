# GMGN 运维坑与报告配置（实战补充）

来源：2026-10-14 / 10-16 BSC 日报与硬过滤器调试会话。这些坑会**直接把结论搞反**，比调参重要。

---

## 1. 限流会把「整批候选」误判成「全是垃圾」

重度使用 `gmgn-cli`（例如一次跑 160+ 次调用、或连续跑多轮 trending）会触发 **IP 级临时封禁**，返回文本：

```
RATE_LIMIT_BANNED — IP is temporarily banned due to repeated rate limit violations
```

ban 是针对**出口 IP**的（走代理时=代理出口），约 5 分钟自解。

**危险后果**：`token info` 对每个候选都返回空 → 批量结果看起来像"12/12 全被淘汰"。这是**限流假象，不是真实淘汰**，但报告会把它当成真数据发出去。

**必须这样写脚本**：
- 缺数据 → 归类为 `❓无数据 / NODATA`，**单独一格统计，绝不混进 FAIL/淘汰**
- 429 / ban → 自动退避重试（60 / 120 / 180 秒）
- 一次批跑后**先看无数据计数**：`无数据 > 0` 时对结论打问号，别报出去
- 分散调用：脚本里每次 token 调用之间 sleep，别 20 个连发

## 2. 网络抖动 ≠ 币不存在

偶发 `fetch failed: Client network socket disconnected before secure TLS connection was established`。
**重试一次**；仍失败就换 DexScreener 独立取值（`https://api.dexscreener.com/latest/dex/tokens/<CA>`），不要直接判"无此币"。

## 3. ticker ≠ 标的：必须先解析成 CA，并确认链

用户提到一个 ticker（尤其"XX 今天开发布会"这类事件驱动对话）时，**绝不要拿同名币直接分析**。同一个 ticker 同时存在于：

- 不同链（BSC 的 FTR vs Solana 的 FTR —— 实测 MC $52K vs $5.56M，完全两个东西）
- 同链的多个克隆盘（实测 Solana 上两个 "Flying Tesla Roadster"：主盘 MC $5.56M/量 $21M，另一个地址 MC $982K）

**解析套路**：
```bash
curl -s "https://api.dexscreener.com/latest/dex/search?q=FTR" | \
  jq -r '.pairs[]? | select(.chainId=="solana") | "\(.baseToken.symbol) | \(.baseToken.address) | MC $\(.marketCap) | 24h \(.priceChange.h24)%"'
```
按 `chainId` 过滤，用 **CA + 链**再去做 GMGN 分析。报告里带 CA 也顺便解决了"看着像同一个币"的歧义。

判据：**主盘 = 流动性/成交量最大的那个**；同名低 MC 盘在叙事爆点里常常是仿盘。

## 4. 股票镜像 / 机构盘：按结构识别，不要按发射台名字

BSC trending 常年被**代币化股票/机构盘**霸占（QQQB / NVDAB / AAPLB / TSLAB / STBL / CT / 4Stock…）。特征：

- **代理合约**（EIP-1167）+ **Top10 66-89%**（托管方持有背书资产，不是控盘）+ 持币 >1000
- price 锚定真实股价、supply 是份额式（几万）而非 meme 式（10 亿）
- 量能可以霸榜（$10-16M）但**不是 meme 博弈标的**

**关键教训（踩过）**：曾把发射台名字硬编码成"股票类"名单（`tapeout`/`geniusfun`/`openfour`/`flap_stocks`），结果把 **TapeFour**（MC $1.39M、持币 641、Top10 仅 1.4%）这种明显 meme 误判为股票镜像。

→ **只按结构特征判定**：`is_proxy && Top10>55% && holders>1000`。名字像股票不代表是股票盘。
→ 股票盘要**分流到单独一段/单独计数**，不要混进"淘汰"，否则报告读起来像"今天全是垃圾"。

## 5. 硬过滤器：二值通过/淘汰会变成废工具

实测把 GoPlus + GMGN 双源门槛设严后，**BSC trending 12/12 全淘汰**——通过率 0 的过滤器在实践中没有价值。

正确形态：
- **安全项**（蜜罐/不能卖出/隐藏 owner/可增发/黑名单）→ 命中即 `判死`，置底
- **市场质量项**（LP 大小 / 币龄 / dev 发币次数 / 官网 / 推特 / Top10 / bundle / 围猎盘 / 量LP比）→ **扣分制**，永远输出一个**排序榜**
- 缺数据 → `❓无数据` 单独归类

参考实现：`~/.hermes/scripts/bsc_hard_filter.py`（`--trending N` / `<CA> ...` / `--pass-only` / `--json`），告警包装 `~/.hermes/scripts/bsc_filter_alert.py`（≥60 分才推、12h 按 CA 去重、静默=零打扰，挂 no_agent cron）。

## 6. cron 报告段落：改动必须在 prompt 里显式覆盖本 skill

**这是最重要的一条流程教训。**

用户说"取消 X" 时，先分清 X 是 **prompt 里定义的段落** 还是 **本 skill 文档里的规则**：

- **成交量TOP5** → prompt 定义 → 删 prompt 即可
- **观察名单** → 本 skill 的规则（"60-69 观察级"、"观察名单可下探 55-59"）→ **只删 prompt 没用**，agent 会照着 skill 继续输出 `🔎 观察位`

→ 凡是"取消/禁止某段"的变更，都要在 cron prompt 里写**显式覆盖声明**，例如：
> 🚫 禁止输出观察名单…**这条优先于任何 skill 文档里的规则**——skill 里可能写"可下探 55-59""准推不足时用观察名单补齐"，本 prompt 一律不执行。

### 日报当前生效配置（2026-10-16 定版）

**三个 job 跑同一份完整版 prompt**（用户明确要求"每个时段都要完整版，不要简报"；单条 cron 表达式
无法让不同小时用不同分钟，所以必须拆 job）：

| job | 时间 | 名称 |
|---|---|---|
| `fa0df7d27b24` | 5:40 | BSC+SOL链上日报(5:40) |
| `2d1bbc759615` | 13:00 | BSC+SOL链上日报(13:00) |
| `b4468ed62c8e` | 19:00 | BSC+SOL链上日报(19:00) |

六段，**纯文本直发 TG**（禁 HTML）：
1. 💰 链上TVL —— **SOL + BSC 双链**（RH 已取消），含资金流向哪边
2. 🔥 **fomo.family 热门代币 TOP5** —— 由 `~/.hermes/scripts/fomo_top5.py` 出块，**原样粘贴**
3. 🐦 **推特热议 项目/代币** —— 由 `~/.hermes/scripts/x_hot_brief.py` 出块，**原样粘贴**
4. 🔥 优质标的 —— **只列 ≥70 分准推级**；无则写一行「本日无准推级」，**不列观察名单**
5. 🆕 新币监控（1D 内 + MC 稳定 ≥$1M，**保留，勿删**）
6. 🧠 叙事验证 & Alpha（含 **SOL ↔ BSC 跨链对照**，无镜像就写"今日无强跨链镜像"）

- ❌ 已取消：成交量TOP5、观察名单（60-69 / 55-59）、以及 19:00 原来的 [SILENT] 逻辑
- **脚本出块 + agent 原样粘贴**是这里的标准模式：数据零 token、不会漂移；脚本输出"暂不可用"时
  保留该行、**禁止编造**
- 无 ≥70 分时**不再 [SILENT]**，其余段照常推送（否则会连 fomo/热议/新币信息一起吞掉）
- 任何"取消段落"的指令都要**同时**确认它是否需要在新币段/其他段保留 → 用户曾把「新币观察」与「观察名单」说混，
  **删错一次就得回滚**；拿不准时先问一句或先备份 prompt
- 变更流程：改前把 prompt 存档（`~/.hermes/cron/prompts/`），改名/改方向**留备份、不直删**
- 相关：`token-100x-screening`（11 项评分）、`cron-job-diagnostics`（投递可靠性/假成功/排期形状）、
  `cron-state-persistence`、`multi-platform-search-cli`（`references/report-embedding-blocks.md`）

- ❌ 已取消：成交量TOP5、观察名单（60-69 / 55-59）
- 无 ≥70 分时**不再 [SILENT]**，其余段照常推送（否则会连新币信息一起吞掉）
- 任何"取消段落"的指令都要**同时**确认它是否需要在新币段/其他段保留 → 用户曾把「新币观察」与「观察名单」说混，**删错一次就得回滚**；拿不准时先问一句或先备份 prompt
- 变更流程：改前把 prompt 存档（`~/.hermes/cron/prompts/`），改名/改方向**留备份、不直删**
- 相关：`token-100x-screening`（11 项评分）、`cron-job-diagnostics`、`cron-state-persistence`

## 7. CLI 升级走 npm，不是 PyPI

```bash
HTTPS_PROXY=http://127.0.0.1:7890 npm update -g gmgn-cli
gmgn-cli --version                 # 实测 1.5.6 → 1.6.6 → 1.6.7
HTTPS_PROXY=http://127.0.0.1:7890 gmgn-cli market trending --chain bsc --interval 6h --limit 2 --raw   # 升完必须真实调用一次
```
**升级后一定要做一次真实 API 调用**验证（cron 全靠它）。
hub 技能包（`gmgn-market/token/portfolio/track/swap/cooking/holder-analysis`）另走 `npx skills add GMGNAI/gmgn-skills --yes`；**更新前先备份**——本 skill 是自建知识库，不能被外部安装器覆盖。

## 8. 链名参数是 `sol`，不是 `solana`

```bash
gmgn-cli market trending --chain solana …   # ✗ [gmgn-cli] Invalid chain: "solana"
gmgn-cli market trending --chain sol    …   # ✓
```

合法值：`sol` / `bsc` / `base` / `eth` / `arbitrum` / `hyperevm` / `robinhood` / `arc` / `stable`。
`market trending` 与 `market hot-searches` 共用同一套链名。踩过的代价：连试两次才发现，白白多跑两轮。

## 9. `market hot-searches`（热搜榜）= 现成的「热度榜 / 叙事聚类」工具

```bash
HTTPS_PROXY=http://127.0.0.1:7890 gmgn-cli market hot-searches \
  --chain sol --interval 6h --limit 20 --raw
```

- 输出是 **JSON 数组** `[{interval, chain, version, tokens:[…]}]` —— **不是 `{data:{…}}` 包裹**，
  所以 `jq '.data.rank[]'` 会 parse error，直接 `.tokens[]`（或 `.[].tokens[]`）。
- 每条 token 直接给全：`symbol / name / address / market_cap / price / volume /
  price_change_percent / holder_count / top_10_holder_rate / liquidity`——出条目不用二次查询。
- `--interval` 支持 1m/5m/1h/6h/24h；`--limit` 默认 500（拿前 20 当候选池足够）。
- **用法一：叙事聚类**。某一时刻 Solana 热搜前 5 = `FTR(+263%) / BANANA(+1994%) / 1 /
  ELON-SAN(+5653%) / STARMAN(+3278%)` → 整条榜被特斯拉/太空叙事霸占，一眼看出当前形态。
- **用法二：做「外网讨论 ↔ 链上标的」的候选池**（细节见
  `multi-platform-search-cli` 的 `references/x-account-monitor.md` 第二层）。
  **关键：用热榜去匹配文本，不要用关键词去搜代币**——实测拿 "roadster" 搜 DexScreener
  返回 30 条 $5K 级垃圾，真正的 10 倍龙头 FTR 根本不在结果里。
- **fomo.family 官方热度榜已打通（2026-10-16）** —— 本文件早期写的"取不到（SPA+登录墙，`api.fomo.family` 不解析）"
  **是错的**，那是没找到正确 base 时的判断，**不要再引用**：
  - base = `https://prod-api.fomo.family`，**纯 cookie 认证**即可（Bearer JWT 会因 1 小时过期报 401，但 cookie 通道仍有效）
  - 热门代币 = **`POST /proxy/trendingTokens`**（返回 36 条；**是 POST 不是 GET**，GET 会 404）
  - 交易者榜 = `/v2/leaderboard`（实测榜首 Unipcs）
  - 登录 cookie 抽法、端点挖法（JS bundle → `fomoFetch` 分片 → 端点表 `trending: /proxy/trendingTokens`）、
    Cloudflare 注意点（urllib 403 → curl + 完整浏览器头；1015 = 限流，需缓存）见
    `multi-platform-search-cli` 的 `references/authenticated-site-api.md`
- **双热榜做候选池**：`fomo 热门` + `gmgn hot-searches`，按 **CA 去重（fomo 优先）**。
  替代/额外源要**先自证能复现已知事实**（实测两边第 1/第 2 名都是 FTR）再当等价物，并告知用户数据源来历。
