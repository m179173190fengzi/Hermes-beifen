# X 账号监控（cron）设计与踩坑

用 `twitter-cli` 的 `user-posts` 把「刷推」变成「推给你」。可运行脚本：
`scripts/x_watch.py`（复制到 `~/.hermes/scripts/`）+ 名单 `~/.hermes/cron/x_watchlist.json`。

## 为什么盯账号而不是关键词搜索

1. `twitter search` 常因 X 前端改版返回 404（client 算不出 `x-client-transaction-id`），
   `user-posts` 稳定可用。
2. 催化剂/公告/喊单**总是从某个具体账号先发**——发布会、上线、合作预告的第一现场是账号，
   不是搜索结果。盯账号 = 提前量。

## 配置（x_watchlist.json）

```json
{
  "accounts": [
    {"handle": "realDonaldTrump", "label": "特朗普", "mode": "viral", "min_likes": 60000},
    {"handle": "elonmusk", "label": "马斯克", "mode": "keyword", "min_likes": 15000},
    {"handle": "cz_binance", "label": "CZ", "mode": "keyword", "min_likes": 5000},
    {"handle": "heyibinance", "label": "何一", "mode": "keyword", "min_likes": 2000}
  ],
  "keywords": ["币","上币","上线","空投","coin","token","crypto","btc","bnb","sol",
               "binance","listing","launch","airdrop","mainnet","doge","trump","tesla",
               "spacex","关税","tariff","降息","合作","收购","发布"],
  "max_per_account": 10
}
```

**模式选择规则**

| 账号特征 | mode | 原因 |
|---|---|---|
| 正文常只有 `t.co` 链接（图片/视频帖，如特朗普） | `viral` | 关键词匹配对纯链接正文**完全无效**，只能靠互动量筛 |
| 正常发文字（CZ / 何一 / 多数 KOL） | `keyword` | 内容相关就推，不靠热度 |
| 极少发推但要全量（官方公告号） | `all` | 频率低，全推不吵 |

`min_likes > 0` 与 `keyword` 是**或**关系：关键词命中必推，高互动也推。
先用宽松阈值跑一轮，再看信噪比往上调（实测：特朗普 20k 时 7/10 条都推 → 调到 60k；CZ 1500 几乎全推 → 调到 5000）。

## 四个已修复的坑（复现时别重犯）

1. **`--test` 必须绕过去重**。否则调参时状态里已存满 ID，`--test` 永远输出空 —— 会误判成「过滤器全灭」。
2. **ASCII 关键词必须词边界匹配**。`kw in text` 让 `star` 命中 `started`、`eth` 命中 `whether`，
   实测信噪比直接崩。用 `\b<kw>\b`（CJK 仍用子串）。
3. **先收集全部命中、按点赞降序、再截断到单次上限**。按账号顺序边扫边截断会让名单里靠前的账号
   吃光额度，后面的账号永远推不出来。
4. **twitter-cli 会在 JSON 之前打印一行 WARNING**（`Failed to init ClientTransaction…`）。
   解析前必须先 `out.find("[")` 定位 JSON 起点，不能直接 `json.loads(stdout)`。

另外：**抓取全失败时必须出声**（打印一行异常告警），否则监控静默失效 = 比刷屏更糟。

## 挂 cron（no_agent，零 token）

```
cronjob(action=create, name="X推文监控", schedule="*/20 * * * *",
        no_agent=true, script="x_watch.py", deliver="origin")
```

- stdout 空 = 静默不推送（no_agent 语义），所以「无命中」不打扰用户。
- 去重状态：`~/.hermes/cron/state/x_watch.json`（每个账号保留最近 40 条已见 ID）。
- 频率：`*/20`（4 账号 × 72 次/天 = 288 次抓取，实测不触发限流）。

## 验证与维护

```bash
python3 ~/.hermes/scripts/x_watch.py --all    # 验证抓取链路（每账号最新一条）
python3 ~/.hermes/scripts/x_watch.py --test   # 看当前命中、调阈值/关键词
python3 ~/.hermes/scripts/x_watch.py           # 真跑一次并更新去重状态
```

- cookie 失效（`twitter status` 不再 authenticated）→ 重跑
  `~/.venvs/xmon/bin/python ~/.hermes/scripts/x_cookie_extract.py`（见本技能 SKILL.md 的抽取小节）。
- 名单里加人只改 JSON 的 `accounts`，脚本不用动。

## 实测价值（为什么值得建）

部署当天就抓到一条关键线索：马斯克在发 Roadster 相关推文（35k 赞，"Roadster transforms in
Track Mode…"）—— 而这正是用户前一天「刷推看到、事后才反应过来该埋伏」的那条 Solana FTR
（Flying Tesla Roadster）叙事的**源头账号**。刷推是滞后且被算法决定的；盯账号才是提前量。

---

# 第二层：推文 ↔ 链上热度榜交叉验证

只推「谁说了什么」还不够——用户真正要的是**这条推文对应哪个链上标的**。
（用户原话要求：「X热议加名人kol推文和代币交叉验证要有这条」「结合热度榜代币前5一起参数」。）

## 方向必须是「热度榜 → 匹配文本」，不是「关键词 → 搜代币」

**这是本层最重要的一条，反直觉且必须照做。**

先说失败路径：拿到推文后提取词（`$TICKER` / 大写词 / 命中关键词），再拿去
`api.dexscreener.com/latest/dex/search?q=<词>` 找代币。**精度不行，会整层失效。**

> 实测：马斯克发 "Roadster transforms in Track Mode…"（35k 赞）。用 `q=roadster` 搜 DexScreener，
> 返回 30 条**全是 MC $5K 级别的小盘垃圾**（`Where we're going` $5,245 / `Roadster Coin` $12,003…），
> 而真正涨了 10 倍、MC $5.6M、24h 量 $21M 的 **FTR 根本不在前 30 条里**——搜索按精确符号匹配排序，
> 叙事龙头的名字里带 roadster 也排不上。**该匹配的目标被搜索结果淹掉了。**

正确做法：**先把「正在热」的代币列表拉下来，再拿它的 symbol/name 去匹配推文正文。**
热榜本身已经把噪音滤完了，匹配是「在已确证的候选里找解释」，而不是「在搜索结果里赌哪个是龙头」。

## 热度榜数据源

```bash
HTTPS_PROXY=http://127.0.0.1:7890 gmgn-cli market hot-searches \
  --chain sol --interval 6h --limit 20 --raw
```

- 返回 **JSON 数组**：`[{interval, chain, version, tokens:[…]}]`，不是 `{data:…}` 包裹。
- 每个 token 给 `symbol / name / address / market_cap / volume / price_change_percent /
  holder_count / top_10_holder_rate`——够直接出条目，不用二次查询。
- 每链各拉一次（`sol` + `bsc`），融合成一个候选池。
- 缓存 20 分钟（`~/.hermes/cron/state/x_hot_cache.json`），避免每次 cron 重复打 GMGN。

**⚠️ 链名参数是 `sol` / `bsc` / `base` / `eth`，不是 `solana`。**
`--chain solana` 直接报 `Invalid chain: "solana". Must be one of: sol, bsc, base, eth, …`。
同一坑在 `market trending` 上也一样（见 `gmgn-onchain-analysis`）。

**榜单本身是有效的叙事聚类工具**：实测某一时刻 Solana 热搜前 5 是
`FTR(+263%) / BANANA(+1994%) / 1 / ELON-SAN(+5653%) / STARMAN(+3278%)`——
整条榜被特斯拉/太空叙事霸占，一眼看出当前叙事形态。

## 关于 fomo.family 官方热度榜

用户术语说的是「fomo 热度榜」。**实测拿不到**：`fomo.family` 落地页是静态图 +
Next.js SPA，没有任何 API 域名/路径暴露；`api.fomo.family` 不解析；`/api/trending` 只返回 SPA HTML。
官方榜单在 App 登录之后。

- **替代方案**：用 `gmgn-cli market hot-searches`（同为「搜索热度」口径）顶上，**但必须显式告诉用户这是替代品**。
- **替代品要自证**：验证替代源能复现已知事实——实测热搜 6h 第 1 名正是 FTR，
  与 X 上的特斯拉超跑发布会叙事吻合，所以口径替换是站得住的。没有这一步就别拿替代源当等价物。
- 想真接 fomo.family：需要用户先在 Chrome 登录 → 用同一套 cookie 抽取法
  （`references` 见本技能 SKILL.md 的抽取小节）拿会话，再找它的 API。成功率中等（取决于前端是否调公开端点）。

## 匹配规则（踩过的坑都在这）

- **symbol 匹配**：长度 ≥3 且按词边界出现在正文里（`\b<sym>\b`）。
- **name 匹配**：按非字母数字切词，取长度 ≥5 的词，命中即算。
- **⚠️ 品牌/叙事实体绝不能进停用词表**。实测把所有 `tesla/roadster/elon/spacex` 塞进
  `NAME_STOP` 后，马斯克那条 Roadster 推文**匹配不到 FTR**——刚好把唯一想匹配的目标排除了。
  停用词表只放**通用词**（coin/token/dog/cat/moon/king/baby…），品牌名留给匹配。
- **name 匹配要加成交量门槛**（实测 `>= $300K`）。否则任意推文里出现 "moon" 都会命中一堆同名小盘。
- 命中结果按 volume 降序，**最多留 3 条**——同名多地址是常态（FTR 实测热搜 #1 与 #8 是两条同名盘，
  MC $5.6M vs $998K），两条都要露出来让用户自己分辨，别只给一条。
- 推文正文里的 `https://…` 和 `@handle` 先剥掉再匹配。

## 两个输出面

1. **账号命中时附加**：推文块后面加 `🪙 链上热度匹配:` 段落，列出命中的代币（含 CA）。
2. **`--feed` 模式**：扫**首页时间线**（≈用户会刷到的内容）→ 与热榜交叉 → 输出
   「X 热议 ↔ 链上热度标的」+ 热搜榜 TOP5。挂在第二个 cron 上：

```
cronjob(action=create, name="X热议↔链上热度榜扫描", schedule="0 */6 * * *",
        no_agent=true, script="x_feed_scan.py", deliver="origin")
```

（`script` 参数**不支持传命令行参数**，所以 `--feed` 要用一个两行的包装脚本
`x_feed_scan.py` 去调 `x_watch.py --feed`。）

## 这一层的证明价值

`--feed` 实测扫出：FTR 出现在用户首页时间线的时刻是 **@MYP_1107 / 10-15 18:21** ——
正是用户事后说「昨天就该埋伏」的那个点。**也就是说这套东西前一天就在他眼前过去了一遍，
只是当时没有人替他把它和链上标的接起来。** 这比任何"策略讲解"都有说服力：
监控的价值不是给出新信息，而是**把已经在流的信号接上执行面**。

## 互补的另一半：事件日历

账号监控覆盖「**谁说了什么**」；CEX 上线公告（Binance/OKX/Bitget/Gate/MEXC 公告页/API）
覆盖「**将要发生什么**」——公告通常比上线早 1-3 天（实测 `$DNA` 场景）。
两者合起来才是完整的事件驱动输入。CEX 公告不需要 cookie，比 X 更稳定。
