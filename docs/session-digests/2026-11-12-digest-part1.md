# 会话提炼 · 2026-11-06 ~ 11-12

> 本文件只保留**可复用的结论与做法**，不含持仓明细、钱包地址、密钥。
> 原始对话保存在本机 `~/.hermes/state.db`（不推送）。

---

## 一、Hermes 升级：v0.19.0 → v0.23.0

### 做了什么

| 步骤 | 结果 |
|---|---|
| 查 PyPI | 最新仍是 0.19.0（官方已停止发 wheel） |
| 查 GitHub | `NousResearch/hermes-agent` 最新 v0.23.0 |
| 尝试 pipx 从 git tag 装 | **失败**：v0.23 起拒绝构建 wheel，只支持安装器/Docker/Nix |
| 改用官方安装器 | `install.sh --non-interactive --channel stable` → 成功 |
| 安装方式变更 | pipx → 源码安装（`~/.hermes/hermes-agent`） |
| 配置迁移 | **v33 → v52**（自动） |

### 踩到的坑：`hermes config set` 会把列表写成字符串

安装器报错：

```
ValueError: plugins.enabled must be a list of names
```

根因：config.yaml 里被写成了字符串

```yaml
# 错（hermes config set 的产物）
plugins:
  enabled: '[omh, hermeskill]'
skills:
  disabled: '["binance", "binance-leaderboard"]'

# 对
plugins:
  enabled: [omh, hermeskill]
skills:
  disabled: [binance, binance-leaderboard]
```

**这同时解释了「禁用 skill 一直不生效」**——`hermes config set` 写数组时会加引号，解析端按字符串处理，等于没配。

排查方法：`grep -nE ": '\[" ~/.hermes/config.yaml`

### 版本号的显示陷阱

`hermes --version` 显示 `vgit.2bd378e (2026.9.24)`，看着像旧版。
真实判断依据是 git 本身：

```bash
git -C ~/.hermes/hermes-agent describe --tags     # → v0.23.0
git -C ~/.hermes/hermes-agent rev-list --count HEAD..v0.23.0   # → 0
```

### 网关自愈重启（护栏 #30719）

Hermes 禁止**从网关进程内部**重启网关（SIGTERM 会传染给子进程）。
可行做法：把重启命令写进脚本，用 `terminal(background=true)` 延迟执行，让当前回复先送达。

---

## 二、Telegram 自愈脚本：一个自我放大的 bug

### 现象

网关每 5 分钟重启一次，每次重启推一条「Hermes is shutting down」。

### 根因

自愈脚本用**固定 15 分钟窗口**判断故障：

```bash
journalctl --since "15 min ago" | grep "Fatal .*adapter error"
```

一条 09:11 的错误，会在 09:14 / 09:20 / 09:26 三次巡检里**重复命中** → 每 5 分钟重启一次。
**脚本本身制造了它要修的故障。**

### 修法（三个改动）

```bash
# ① 水位线：只看「上次自愈之后」的日志
STATE=~/.hermes/cron/state/tg_heal.last
LAST=$(cat "$STATE" 2>/dev/null || echo 0)
[ "$LAST" -eq 0 ] && LAST=$((NOW - 600))
DEAD=$(journalctl --user -u hermes-gateway --since "@$LAST" | grep -iE "Fatal .*adapter error")

# ② 冷却：5 分钟内刚自愈过就跳过
[ $((NOW - LAST)) -lt 300 ] && exit 0

# ③ 成功静默：只写日志，不推 Telegram；失败仍推 🔴
```

### 治本：`telegram_network_error` 的源头是直连

```yaml
platforms.telegram.proxy_url: http://127.0.0.1:7890
```

配置后 **2.5 天零 fatal、零重启**（改之前每 5-10 分钟一次）。

### 关掉重启广播

```yaml
platforms.telegram.gateway_restart_notification: false
telegram.gateway_restart_notification: false
```

---

## 三、叙事扩散计数器（narrative_radar.py）

### 设计目标

回答一个问题：**「这个叙事是不是真在扩散」**——不调 LLM，零 token。

### 数据源（全部免费无 key）

```
RSS：The Block / Cointelegraph / Decrypt / Blockworks / CryptoSlate / CoinDesk
Google News：关键词 RSS
GDELT：全球新闻库
Telegram：公开频道网页预览 t.me/s/<channel>
```

### 判定标准：独立事件数（不是条目数）

关键设计：**一条通稿被 8 家转载 = 1 个事件 + 8 个渠道，不是 8 个独立信号。**

```
标题归一化去重
  → Jaccard > 0.55 折叠为同一事件
  → 只匹配标题（正文提及不算）
  → 泛化叙事（AI Agent/监管/DeFi）必须带加密上下文
  → 过滤活动文案（referral / earn up to / price today）
  → 按独立事件数排序
```

### 判定梯度

| 独立事件 | 含义 | 动作 |
|---|---|---|
| 1 | 单一来源 | 忽略 |
| 2-3 | 开始扩散 | 记录，等 24h |
| 4-6 | 已被确认 | 可按叙事布局 |
| 7+ | 全市场共识 | **派发段，退出** |

### 踩坑记录

1. **Google News 的 `<source>` 不解析** → 所有转载算作同一个「域名」，独立事件失真
2. **标题尾部的 ` - 媒体名`** → 媒体名里的 "Crypto" 字样混进匹配，导致「美联航禁止 AI 代理」被判为 crypto 叙事
3. **只看正文** → 交易所有站每篇都提稳定币，稳定币事件虚高到 8 个

---
