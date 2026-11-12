---
name: hermes-model-auth-troubleshooting
description: |
  排查 Hermes 的模型/供应商鉴权失败 —— 主模型或辅助模型（compression / vision / web_extract /
  approval / title_generation）报 401 / 403 / 402、上下文压缩失败、标题生成失败、备用凭证
  "stale/unrefreshable credential" 等。含认证池（auth store）里残留旧 key 这个最常见元凶的定位与修复。
  触发词：Compression aborted、401、api key is invalid、authentication_error、辅助模型报错、
  压缩失败、GROUP_DELETED、额度不足、hermes auth、模型 key 失效。
  English: hermes 401, invalid api key, compression aborted, auxiliary model auth failure,
  stale credential, provider fallback failed.
---

# Hermes 模型鉴权失败排查

> 核心认知：**Hermes 的「凭证」是每个 provider 下的一个列表（认证池），按顺序尝试。**
> 只要池子里躺着一把失效的旧 key，它就可能先撞上它 —— 而主对话用的 config key 明明是好的。

## 1. 症状 → 病因对照

| 症状 | 病因 | 是不是数据丢失 |
|---|---|---|
| `⚠️ Context compression aborted` + `401 Authentication Fails` | 压缩用的辅助模型凭证失效 | **否**，原文会写 `No messages were dropped` |
| `title_generation` 也同时报 401 | 同一个认证池，辅助功能共用 | 否 |
| `✓ mark api-key unhealthy for 600s` + `fallback candidate has a stale/unrefreshable credential` | **池子里有旧 key**，正在被跳过 | 否 |
| `403 {"code":"GROUP_DELETED"}` | 中转/代理服务的分组被删（供应商跑路） | 否 |
| `402 / insufficient balance` | 余额问题，换 key 没用 | 否 |

**关键区分**：401 是**鉴权**问题，不是**数据**问题。不要一见报错就 `/reset` 丢上下文，
先 `/compress` 重试或修 key。

## 2. 定位顺序（照这个走，不要跳步）

```bash
# ① 看认证池：同一 provider 下有没有多把 key、哪些已被标失败
hermes auth list <provider>          # 例：hermes auth list deepseek
```
典型输出（实测）：
```
deepseek (4 credentials)
  #1  api-key-2         api_key  manual  auth failed (401)
  #2  api-key-3         api_key  manual  auth failed (401)
  #3  api-key-4         api_key  manual  auth failed (401)   ← 报错里那把 ****cv_S
  #4  DEEPSEEK_API_KEY  api_key  env:DEEPSEEK_API_KEY        ← 唯一有效的
```

```bash
# ② 看辅助模型槽位配的是哪个 provider/model
hermes config get auxiliary.compression
hermes config get auxiliary.vision        # 其余槽位同理

# ③ 从日志里确认到底是哪把 key 在失败（会直接点名）
grep -B3 -A3 "Authentication Fails" ~/.hermes/logs/errors.log | tail -30
grep -E "marking .* unhealthy|stale/unrefreshable" ~/.hermes/logs/errors.log | tail -5
```

```bash
# ④ 验证「唯一那把还活着」——直接打供应商，别靠猜
K=$(grep -E '^DEEPSEEK_API_KEY' ~/.hermes/.env | cut -d= -f2)
curl -s -o /dev/null -w "%{http_code}\n" --max-time 30 https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $K"
```

## 3. 修复：删掉池子里的废凭证

```bash
hermes auth remove <provider> <label>     # 例：hermes auth remove deepseek api-key-2
hermes auth list <provider>               # 复查只剩有效那把
hermes auth status <provider>             # 期望 logged in
```

- **不要**用 `hermes config set model.api_key` 去覆盖 —— 那只改主模型，辅助模型的池子还在。
- 删完不需要重启网关就能生效（下次解析凭证时读取）。
- 若 key 来自 `.env`（`env:XXX`），那一条不要删，它是唯一可靠的来源。

## 4. 403 GROUP_DELETED（中转商跑路）

```
POST https://<reseller>/v1/chat/completions  http=403
{"code":"GROUP_DELETED","message":"API Key 所属分组已删除"}
```
这不是本地配置错，是**上游把套餐分组删了**。做法：把 `auxiliary.*` 全部切到有直连的 provider
（实测切到 `deepseek` + `deepseek-v4-flash` 即可），别在这个中转上反复试。

```bash
for s in compression web_extract vision approval; do
  hermes config set auxiliary.$s.provider deepseek
  hermes config set auxiliary.$s.model deepseek-v4-flash
done
```

## 5. 修完怎么确认

1. `hermes auth status <provider>` → `logged in`
2. 直接 curl 供应商 `/v1/models` → **200**（不是 401）
3. `/compress`：成功会报压缩了多少轮，不再弹 401
4. 侧证：`title_generation` 的 401 从 `errors.log` 里消失

## 6. 常见误判（踩过）

- ❌ 「401 说明 key 泄露/被封」→ 多数只是**池子里有旧 key**，删掉就好。
- ❌ 「主模型能用，所以 key 没问题」→ 辅助模型**不一定**走同一个 key，它有自己的池子与 fallback 链。
- ❌ 「网关重启一下就好」→ 池子里的失效条目不会自愈，必须删。
- ❌ 在 `config.yaml` / `.env` 里 grep 报错 key 的尾号找不到 → 说明它来自 **auth store**，不是配置
  文件（查 `hermes auth list`，别在文件里死找）。
