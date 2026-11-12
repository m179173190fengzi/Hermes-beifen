# fomo.family API（逆向结果，2026-10 实测）

社交交易 App（Solana 为主）。官网/落地页是静态图，榜单与交易数据全在 App 内 → 必须登录后走私有 API。

## 基础信息

```
API base:  https://prod-api.fomo.family      # 从 *fetch*.js chunk 里挖出来的
Web:       https://fomo.family               # SPA（React Router），/token 是主路由
Auth:      Cookie + Authorization: Bearer <privy-token>
```

- 登录走 **Privy**；cookie 里有多枚 JWT：
  - `privy-token`（domain `.fomo.family`，`aud: <app id>`）← **这枚是业务 API 认的**
  - `privy-access-token`（domain `.privy.fomo.family`，`aud: privy.fomo.family`）← 用它做 Bearer 会 401
  - `privy-session` / `privy-refresh-token`（刷新用）
- **部分端点只要 Cookie 就够**（`/config`、`/proxy/trendingTokens`），部分必须带 Bearer（`/v2/users/<id>/swaps`）。

## 已确认端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/config` | 应用配置（可用作"认证是否通过"的探针；返回 `{"success":true,...}`） |
| POST | `/proxy/trendingTokens` | **热门代币榜**（36 条）。GET 会 404 —— 这是 POST 端点 |
| GET | `/v2/leaderboard` | 交易者榜（100 人，含 `totalPnL` / `followers` / `numTrades` / `clan`） |
| GET | `/v2/users/<id>/swaps?limit=N` | 某用户的成交记录（含 `display.side=buy/sell`） |
| GET | `/v2/users/<id>/balances` | 持仓 |
| GET | `/v2/users/fuzzy-search?searchTerm=` | 用户搜索 |
| GET | `/feed/token?tokenAddress=&networkId=` | 单币讨论流（`/thesis`、`/sortedThesis` 是变体） |

前端端点 map（在某个 chunk 里，等于半张文档）：

```js
{trending:"/proxy/trendingTokens", "most-held":"/proxy/mostHeld",
 graduated:"/proxy/graduatedTokens", "crypto-tokens":"/proxy/cryptoTokens",
 verified:"/proxy/verifiedTokens", community:"/proxy/communityTokens"}
```

`networkId`：`1399811149` = Solana，`56` = BSC，`1` = ETH，`8453` = Base。

## 响应形状

`POST /proxy/trendingTokens`

```json
{"success":true,"responseObject":[
  {"change24":"91.1","holders":1815,"liquidity":"38428.2","marketCap":"288891.9",
   "priceUSD":"0.00030480","volume24":"918349.5",
   "token":{"address":"...","symbol":"LOOM","name":"The Loom","networkId":1399811149,
            "launchpad":{"launchpadName":"Pump.fun","graduationPercent":0},
            "socialLinks":null,
            "info":{"circulatingSupply":"...","totalSupply":"..."}}}]}
```

`GET /v2/users/<id>/swaps?limit=N`

```json
{"success":true,"responseObject":{"swaps":[
  {"inTokenAddress":"...","inHumanAmount":0.462555,
   "outTokenAddress":"EPjFWdd5...","outHumanAmount":175.757,
   "humanUsdAmountIn":175.757,"humanUsdAmountOut":175.757,
   "display":{"side":"sell"},"createdAt":"2026-10-15T16:10:35.000Z","provider":"JUPITER"}]}}
```

判 buy/sell 用 `display.side`，不要靠 in/out 猜（稳定币两侧都可能是 USDC）。

## 已知实体

| 名字 | fomo user id | 备注 |
|---|---|---|
| Unipcs（中文圈叫"小黄人"，fomo 盈利榜 #1，PnL ≈ $5.74M，clan = Fantom Troupe） | `36adb85a-c0fd-5fa8-916d-8fdc32fe4237` | fomo profile 地址 `FJDy9FDRy6bwGEUKuAC98bUtN8MkpE2pT7Dj7HE3Z7Q1` 在 GMGN 查不到活动 |

## 重要经验：查"某人的链上买入"优先用 GMGN，不要用 fomo swaps

- fomo 的 `/v2/users/<id>/swaps` 依赖 Privy JWT，**用户一在浏览器里活动 token 就轮换**，401 随机出现；
  重抽 cookie 能救回，但作为定时任务的唯一数据源不稳。
- **同一个人的真实交易钱包**用 `gmgn-cli portfolio activity --chain sol --wallet <addr> --raw` 查更稳
  （不依赖浏览器），返回 `event_type=buy/sell`、`token.symbol`、`cost_usd`、`timestamp`。
- 实测 Unipcs 的真实交易钱包：`2heJbC32Tpfcb3nbUb5ER61K11FGZVfVGtVnDm6LDogF`。
- 结论：**fomo 只用于"榜单/排名"，钱包级明细走 GMGN**；两者互为兜底。

## 本机脚本

| 脚本 | 作用 |
|---|---|
| `~/.hermes/scripts/fomo_cookie_extract.py` | 抽全部 fomo cookie → `~/.hermes/secrets/fomo_cookies.json`（含 `header` 与明细） |
| `~/.hermes/scripts/fomo_jwt_decode.py` | 解 Privy JWT，看 `aud/sub/exp` |
| `~/.hermes/scripts/fomo_top5.py` | 热门榜 TOP5 + GMGN 补名称/推特/发射台（20 分钟缓存） |
| `~/.hermes/scripts/fomo_api_discover.py` / `fomo_find_paths.py` / `fomo_sweep_paths.py` | 一次性挖包工具（找 base URL / 端点） |

## 坑

1. GET `/proxy/trendingTokens` → 404（必须 POST）。
2. `api.fomo.family` 不存在；只有 `prod-api.fomo.family`。
3. 裸猜 `https://fomo.family/<path>` 会返回 SPA 壳（HTTP 200 + 12KB HTML），看着像成功。
4. 连发探测会撞 Cloudflare `error code: 1015`（429），间隔 ≥4s。
5. 热门榜里有稳定币（`USDG`/Global Dollar 之类）混进"买入标的"，按名称含 `usd/dollar` 过滤。
6. `token.socialLinks` 常为 null；`link.twitter_username` 可能是伪装链接（`Polymarket/status/...`）。
