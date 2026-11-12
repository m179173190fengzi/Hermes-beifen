---
name: site-api-reverse-engineering
description: |
  把「只有登录后才能看的网站数据」接成可编程接口：从本机浏览器抽 cookie → 过 Cloudflare →
  从前端 JS 包里挖 API 域名与端点表 → 判断认证方式（cookie / 哪个 JWT）→ 处理 token 轮换与限流 →
  落成带缓存和兜底的数据源。
  适用于没有公开 API、或公开 API 需要登录的平台（社交交易 App、榜单站、SaaS 后台）。
  触发词：接入这个平台、能不能抓这个网站、这个榜单一小时更新一次、cookie 登录、
  privy/JWT 认证、XHR 端点、抓包、reverse engineer API、没有开放 API。
  English: no public API, scrape behind login, find their API endpoint, session cookie auth.
---

# 网站私有 API 逆向接入

## 何时用

- 用户想要某平台的数据自动化，但那平台**没有公开 API**，或数据在登录后才可见
- 「我登录上了，看你能不能接上」
- 已有公开接口但缺关键数据（如榜单在 App 里、网页只有静态图）

**前提（必须守住）**：只接**用户自己的账号**、只取**用户自己有权限看的数据**。
不抓别人的私信/后台、不绕付费墙、不做高频轮询。先看 robots/ToS 再动手。

## 六步流程

### 1. 抽浏览器 cookie —— 用独立 venv，别动系统 Python

```bash
python3.11 -m venv ~/.venvs/xmon
~/.venvs/xmon/bin/pip install browser_cookie3
# 然后写个脚本跑：browser_cookie3.chrome(domain_name='xxx.com') → 落盘 secrets/xxx_cookies.json (600)
```

- **系统 Python 3.14 上 `browser_cookie3` 会崩**（`TypeError: expected str, bytes or os.PathLike object, not NoneType`，路径解析拿到 None）→ 换 3.11 独立 venv 就好。
- 不要用 `--break-system-packages`：被 uv 管理的 py3.11 会拒绝，且会污染 agent 自己的 venv。
- 把 cookie 存成「`header` 字符串 + 明细数组」两份，后续 curl 直接用 `-H "Cookie: $header"`。
- 顺手把 httpOnly 的 **JWT 也解出来**（base64url 解 payload，看 `aud` / `sub` / `exp`）——它往往比 cookie 更有用。

### 2. 探测：用 curl，不要用 urllib/requests

- `urllib` 的 TLS 指纹会被 Cloudflare 判成机器人（403）；**同一个 URL 用 curl 就过**。
- 带齐浏览器头再试：`--http2`、真实 UA、`Accept-Language`、`sec-ch-ua*`、`sec-fetch-*`、`Origin`、`Referer`。
- 先看状态码语义：`302 → location:/token` 说明路由重定向（跟下去），`200` 但只有 ~10KB = **SPA 壳**（数据在 XHR 里，不在 HTML 里）。

### 3. 挖 API 域名：从 JS 包里找，别猜子域

```bash
# 1) 拿壳 → 列出 chunk
grep -oE '/assets/[a-zA-Z0-9._-]+\.js' page.html | sort -u
# 2) 批量下载 chunk，全局搜域名
grep -rhoE 'https?://[a-zA-Z0-9.-]+\.[a-z]{2,6}' chunks/*.js | sort | uniq -c | sort -rn
```

- API 域名几乎总在 **`*fetch*.js` / `*client*.js` / `config*.js`** 这类 chunk 里（实测 `prod-api.<domain>`）。
- 先猜子域（`api.` / `backend.`）往往全是 `000/404`——**这一步是纯浪费**，直接挖包。

### 4. 端点表 + HTTP 方法

- 搜 chunk 里的路径字面量：`grep -ohE '"/[a-z0-9]+/...`' chunks/*.js | sort -u`
- 前端常把端点收敛成一个映射对象，例如
  `{trending:"/proxy/trendingTokens", "most-held":"/proxy/mostHeld", graduated:"/proxy/graduatedTokens"}`
  —— 找到这个 map 等于拿到半张 API 文档。
- ⚠️ **同一 map 里不同端点的方法可能不同**：调用点写着
  `fetch(path, {method: type === "verified" ? "GET" : "POST"})`。
  对一个 POST 端点用 GET 会返回 **404**，极容易被误判成"路径写错了"，然后白猜半小时。
- 猜路径要**放慢**：连发会撞 Cloudflare `error code: 1015`（429 速率拦截）。间隔 ≥4–5 秒，先读代码再猜。

### 5. 认证方式：cookie 还是 Bearer？是哪个 JWT？

实测同一个应用里可能同时存在多套凭据：

| 尝试 | 结果 |
|---|---|
| 只带 Cookie | 对某些端点够用（如 `/config`），对另一些 401 |
| `Authorization: Bearer <access-token>` | 401 `Authentication token is invalid` |
| `Authorization: Bearer <app-token>` | ✅ 200 |

判断法：**JWT 的 `aud` 应该指向 API 域**（例：`aud: "privy.<domain>"` 的那枚是 Privy 自己的，不是业务 API 的；
`aud: "<app id>"` 的那枚才是应用会话 token）。两个都试，别假设"最新抽到的就是对的"。

### 6. 在脚本里落地（否则一天就坏）

- **401 是常态，不是故障**：用户在浏览器里活动会刷新 token，把旧 token 作废。
  处理：收到 401 → 重跑第 1 步重抽 cookie → 重试**一次** → 仍失败才降级。
- **缓存**：结果缓存 15–30 分钟（`state/xxx_cache.json`），顺手把限流风险也降掉。
- **必须有兜底源**：私有 API 挂掉时用公开数据（交易所 API / 聚合站 / 同域公开榜单）替代，
  并在输出里**注明数据源**，绝不硬失败让整条报告/监控全挂。
- **写清过期提示**：cookie 过期时输出「暂不可用（需重抽 cookie）」而不是抛异常。

## 坑清单

1. `browser_cookie3` 在 py3.14 崩，且别用 `--break-system-packages` → 独立 py3.11 venv。
2. `urllib` 403 / `curl` 200 —— Cloudflare 看 TLS 指纹，不是看 header。
3. 200 + 10KB HTML ≠ 成功，那是 SPA 壳；数据在 XHR。
4. `api.<domain>` 猜不中；API 域名在 JS chunk 里。
5. GET 打 POST 端点 → 404，看起来像"路径错"。
6. 多枚 JWT 时，认 `aud`；不是"最新那枚就对"。
7. 会话 token 会轮换 → 401 当常态处理，重抽+重试一次。
8. 连发探测 → `error code: 1015`（Cloudflare 429），需要退避而不是换路径。
9. 抓到的社媒字段常是**伪装的链接**（`用户名/status/123`、`search?q=`），渲染前用 `^[A-Za-z0-9_]{2,20}$` 校验。

## 已接入的平台

- **fomo.family**（社交交易 App：热门代币榜 / 用户交易记录 / 交易者榜）→ `references/fomo-family-api.md`
