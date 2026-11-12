# 用浏览器 cookie 打通「登录后才有」的站点 API

适用：数据在登录墙后、又没有公开 API 文档的站（fomo.family 热门榜、App 化的交易/社交平台、
任何「只能在网页/App 里看」的榜单）。目标是把「人在 App 里看」变成「脚本可拉」。

前提：本机 Chrome 里已登录该站（Chrome 是 cookie 的唯一来源）。

---

## 四步法

### 1. 抽整组 cookie（不是只抽两个）
X/Twitter 只要 `auth_token`+`ct0`，但通用站点要**整组**，并用 `; ` 拼成可直接塞进
`Cookie:` 头的字符串。参考实现：`~/.hermes/scripts/fomo_cookie_extract.py`
（输出 `{"cookies":[...], "header":"a=b; c=d"}` 到 `~/.hermes/secrets/<site>_cookies.json`，chmod 600）。

必须跑在**独立 venv**（系统 py3.14 会让 `browser_cookie3` 崩；被 uv 管理的 py3.11 不能
`--break-system-packages`）——见主 SKILL.md 的 twitter-cli 抽取段。

### 2. 找 API 域名：从 JS 分片里挖，不要猜
应用壳 HTML 通常只有 12KB 左右（SPA），数据全走 XHR。流程：

```bash
# a) 抓应用壳（带 cookie + 完整浏览器头）
curl -s --http2 -L -H "Cookie: $CK" -H "User-Agent: $UA" "https://<site>/" -o shell.html
# b) 列出 JS 分片
grep -oE '(src|href)="[^"]*\.js[^"]*"' shell.html
# c) 很多站有 manifest（React Router/Vite）→ 里面是全部 route chunk 的名字
grep -oE '/assets/[a-zA-Z0-9._-]+\.js' manifest*.js | sort -u | wc -l   # 实测 375 个
# d) 全量下载分片后 grep 域名/路径 —— 真正的 API base 常只出现 1 次
grep -ohE 'https://[a-zA-Z0-9.-]+\.[a-z]{2,6}' *.js | sort | uniq -c | sort -rn
```

实测：全部 375 个分片里，唯一出现的业务域名是 `https://prod-api.fomo.family`
（其余是 google/facebook/react.dev）。**先按分片名筛关键字（fetch/api/client/leaderboard/token）
再下全量**，能省时间。

### 3. 找端点与 HTTP 方法：读字面量表
前端通常把端点写成一张表，直接可读：

```js
Gl={trending:"/proxy/trendingTokens","most-held":"/proxy/mostHeld",
    graduated:"/proxy/graduatedTokens", ...}
async function Gi(e){const t=Gl[e],n=await Y(t,{method:e==="verified"?"GET":"POST"})}
```

**同一个 API 会混用方法**（`trending` 必须 POST、`verified` 用 GET）——用错就是 404，
看起来像「端点不存在」，其实是方法错。调用点那行 `{method: ...}` 一定要看。

### 4. 认证：先试纯 cookie，再试 Bearer —— 且**要试对哪个 token**

很多站（Privy/Auth0 这类）同时支持 cookie 和 `Authorization: Bearer <jwt>`。
**JWT 过期不代表 cookie 无效**：实测 Bearer 返回
`{"success":false,"message":"Authentication token is invalid","statusCode":401}`，
而同一个请求只带 Cookie 头 → **200 + 真实数据**。所以 401 时先降级成纯 cookie 再判定认证失败。

**⚠️ 但存在「cookie 不够、必须带 Bearer」的端点，这时要挑对 token。** 实测 fomo.family：
`/config`、`/proxy/trendingTokens` 纯 cookie 就够；而 `/v2/users/<id>/swaps` 纯 cookie 返回 401，
**Bearer 用 `privy-access-token` 也 401，用 `privy-token` 才 200**。

> 判据：Privy 的 `privy-access-token` 的 `aud` 是 **Privy 自己的域**（`privy.fomo.family`），
> `privy-token` 的 `aud` 才是**这个应用的 client id**。应用 API 校验的是后者。
> 通用做法：把所有 JWT 逐个解码（只 base64 第二段，不用验签）、看 `aud`/`iss`，
> **拿 `aud` 指向本应用/本域的那个当 Bearer**，别默认用最长的那个。

**⚠️ 这类 token 会随浏览器活动轮换。** 实测：抽出来的 token 新鲜有效（`exp - now ≈ 31 分钟`）却仍返回
`JWT token expired`/`Authentication token is invalid`，紧接着同一 token 又成功一次 —— 用户在浏览器里
刷新页面就会作废旧 token。对策（按优先级）：

1. **401 时自动重抽 cookie 再重试一次**（重抽是本地读 Chrome，便宜）：`subprocess.run([venv_py, extractor])`
   然后重发请求。这一层能救回大部分偶发 401。
2. **有非浏览器源就用非浏览器源。** 实测「盯某个大户的最新买入」——fomo 接口时好时坏，
   而 **GMGN 按钱包地址查活动稳定可用**（见下节）。**浏览器的会话令牌是自动化里最脆的一环，
   只要等价数据有链上/API 直连版本，就把它降级为兜底，不要当主源。**

---

## 坑（都踩过）

| 症状 | 原因 | 处理 |
|---|---|---|
| Python `urllib` 403，curl 正常 | TLS/头部指纹被 Cloudflare 判为非浏览器 | 用 `curl --http2` + 完整头：`sec-ch-ua`、`sec-ch-ua-mobile`、`sec-ch-ua-platform`、`sec-fetch-dest/mode/site/user`、`upgrade-insecure-requests`、`Accept-Language` |
| `HTTP 302 location: /token` | 站点的默认跳转 | 跟 `-L`，别当成失败 |
| `error code: 1015` + 429 | **Cloudflare 限流**，多半是你连续猜路径猜出来的 | 停止暴力探测；改成从 JS 里读端点表（第 3 步）。等待数分钟后，后续请求之间 sleep 3-5s，并给脚本加 20 分钟缓存 |
| 任意路径都 200 返回 HTML | SPA catch-all | 用 `/this-does-not-exist-xyz` 做对照；是 200 就说明探测无意义，去读 JS |
| 榜单数据每次都要真请求 | 触发限流 | 落盘缓存（TTL 20 min），每次运行最多 1 次上游请求 |
| cookie 过期 | 站点会话失效 | **优雅降级**：打印「⚠️ X 榜不可用（cookie 失效或接口变动）」并继续跑其它源，不要静默失败也不要崩 |

---

## fomo.family 实测记录（2026-10，已验证可用）

- **API base**：`https://prod-api.fomo.family`（同源 `fomo.family` 只是 SPA 壳，`/config` 等路径在壳上返回 HTML 不是 JSON）
- **认证**：纯 cookie 即可（Privy 登录）
- **热门代币榜**：`POST /proxy/trendingTokens`（body `{}`）→ 36 条，字段
  `marketCap / change24 / volume24 / holders / liquidity / priceUSD / token.{symbol,name,address,networkId}`
  （`networkId == 1399811149` = Solana）
- **交易者榜**：`GET /v2/leaderboard` → 100 人（`displayName / followers / numTrades / swapCount / address`）；
  实测榜首 **Unipcs**（即用户问过的 "Bonk Guy"）
- **其余端点表**：`/proxy/{mostHeld,graduatedTokens,cryptoTokens,verifiedTokens,communityTokens,filterTokens,tokenDetails}`、
  `/feed/token`、`/feed/token/thesis`、`/feed/token/sortedThesis`、`/feed/react`、`/feed/unreact`、
  `/v2/users`、`/v2/users/<id>/balances`、`/v1/perps/listed-perps`、`/tokenAllowList/detailed`、`/watchlist`、`/refresh?silent=1`
- **抽取脚本**：`~/.hermes/scripts/fomo_cookie_extract.py`；JWT 解码调试用 `fomo_jwt_decode.py`；
  端点挖掘用 `fomo_find_paths.py` / `fomo_sweep_paths.py`（会存到 `/tmp/fomojs*/`）
- **维护**：Chrome 保持登录 → cookie 失效时重跑抽取脚本即可

## 与监控脚本的集成（双热榜源）

`~/.hermes/scripts/x_watch.py` 现在把 **fomo 热门（前 20 做匹配池、前 5 展示）** 与
**GMGN 热搜（`gmgn-cli market hot-searches`，链名 `sol` 不是 `solana`）** 合并去重（按 CA，fomo 优先），
再与 X 推文正文做词级匹配。**匹配方向必须是「拉热度榜 → 匹配正文」**——
反向的「提关键词 → 搜 DexScreener」会把真正的叙事龙头淹在 $5K 小盘里（实测搜 `roadster`
的前 30 条全是 $5K 级垃圾，而正盘 FTR 在 fomo/GMGN 榜上都是前列）。

---

## 盯「某个大户/盈利榜第一名」的最新买入（用户会直接点名要这个人）

用户会点名「fomo 盈利榜一大哥」这种人物，要求把**他最新买了什么**接进日报（带叙事）。
识别与取数分两步，**两处都有坑**：

### 1. 先确认「这个人」是谁 —— 榜上有 Profit 字段，别只看榜单顺序

`GET /v2/leaderboard` 的条目里除 `displayName/userHandle/followers/numTrades/swapCount` 外，
还有 **`totalPnL`** 与 `totalHoldings/topHoldings/badge/clan`。实测榜首 **Unipcs**
（`id=36adb85a-c0fd-5fa8-916d-8fdc32fe4237`，`totalPnL ≈ $5.74M`，clan `Fantom Troupe`，
用户口中的「小黄人 / 盈利榜一大哥」），其 `address` 是 **fomo 资料地址**，
**不是他的链上交易钱包** —— 拿它去查链上会得到 0 条活动。

> ⚠️ `GET /v2/leaderboard` 默认那份看起来像「按粉丝排」，**要用 `totalPnL` 自己确认**盈利名次，
> 别把用户说的「盈利榜第一」和默认返回顺序当同一件事（先问清/自查，别猜）。

### 2. 取「最新买入」：主源用链上，fomo 接口只做兜底

**主源（推荐）—— GMGN 按钱包查活动，不需要任何 cookie：**

```bash
# 注意参数名是 --wallet，不是 --address（后者报 required option '--wallet' not specified）
HTTPS_PROXY=http://127.0.0.1:7890 gmgn-cli portfolio activity --chain sol \
  --wallet 2heJbC32Tpfcb3nbUb5ER61K11FGZVfVGtVnDm6LDogF --raw
# → {"activities":[{event_type: buy|sell, token:{address,symbol}, cost_usd, timestamp, ...}]}
```

拿到 `event_type == "buy"` 即买入；按 `token.address` 去重、取最近 N 笔。

**兜底源 —— fomo 接口**（`GET /v2/users/<id>/swaps?limit=150`，Bearer 必须是 `privy-token`）：
结构为 `responseObject.swaps[]`，字段 `inTokenAddress/outTokenAddress`、`inHumanAmount/outHumanAmount`、
`humanUsdAmountIn/Out`、`createdAt`、**`display.side`（`buy`/`sell`）**。
注意 `responseObject` 在不同参数/鉴权失败时会退化成**空数组**而不是对象 —— 解析前先判类型。

### 3. 两个必须加的过滤器

- **稳定币要剔除**：实测「最新买入」里混进 `USDG (Global Dollar)` —— 那不是标的。
  用「符号 + 名称」双重判断（含 `usd/dollar/usdc/usdt/dai/tether/stable` 即排除），
  **只按符号过滤会在符号缺失时失效**（DexScreener 偶尔不返回该地址），所以名称也要参与。
- **符号缺失时要有兜底链**：`GMGN 活动里的 symbol` → `DexScreener 批量 /latest/dex/tokens/<addr,addr>` →
  `gmgn-cli token info` 的 `symbol`。三者任一有值就用，否则输出 `?` 而不是崩。
- 缓存：叙事素材（名称/推特/发射台）按 **CA 做 6h 缓存**；链名注意 **GMGN 的 Solana 是 `sol`**。
