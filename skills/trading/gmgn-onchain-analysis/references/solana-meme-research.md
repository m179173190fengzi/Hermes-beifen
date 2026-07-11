# Solana 链上土狗/迷因币调研工作流

用于通过社交信息寻找 Solana 链上迷因币，查询链上数据并评估风险。

## 社交线索搜寻（X/Twitter）

### 前置条件
- X/Twitter 在用户浏览器已登录
- OpenCLI Chrome 扩展已安装（chrome://extensions 确认开启）
- 浏览器 x.com 标签页保持打开（扩展读取 cookie）

### 搜索喊单/Alpha 信息

```bash
# 搜索中文喊单
opencli twitter search "solana 土狗 喊单" --limit 10

# 搜索英文迷因币
opencli twitter search "\$ansem solana" --limit 10

# 搜索特定 KOL 喊单
opencli twitter search "solana memecoin" --from blknoiz06 --limit 10
```

返回结果包含：
- `author` — 发帖人
- `bio` — 简介
- `text` — 推文全文
- `likes / views` — 热度指标
- `created_at` — 时间戳（注意时区）
- 引用/回复推文在 `quoted_tweet`

### GMGN Extension（辅助社交信号）

在 X.com 刷推时，安装 **GMGN Extension** 可自动显示发帖人身份：

| 标签 | 含义 | 权重 |
|:----|:-----|:----|
| 👑 Smart Money | 聪明钱 | ⭐⭐⭐ 值得仔细看 |
| 🐋 Whale | 鲸鱼大户 | ⭐⭐ 观察方向 |
| 📢 KOL | 喊单KOL | ⭐ 注意是否付费喊单 |
| 🔥 Degen | 赌狗 | ⭐ 反向指标 |
| 🤖 Bot | 机器人 | ⚠️ 无视 |

安装方法：gmgn.ai → Chrome Extension → 下载 .crx → chrome://extensions 开发者模式拖入安装

### 关键信息提取
从推文中提取：
- **代币合约地址**（格式：`solana:...` 或裸地址）
- **代币符号**（如 `$ANSEM`）
- **市值变化**（如 "20万→1000万"、"速通38M"）
- **上车时机**（如 "1.6M 群友就发了"）

## 二、链上数据查询

### 获取代币供应量（Solana RPC）
```bash
curl -s "https://api.mainnet-beta.solana.com" \
  -X POST -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "getTokenSupply",
    "params": ["<CONTRACT_ADDRESS>"]
  }'
```
返回 `uiAmount` = 总供应量。

### 风险评估（Rugcheck）
```bash
curl -s "https://api.rugcheck.xyz/v1/tokens/<ADDRESS>/report/summary"
```
关键字段：
- `risks[].name` — 风险名称（如 "Top 10 holders high ownership"）
- `risks[].level` — 风险等级（danger/warning）
- `score_normalised` — 归一化评分（0-100，越高越危险）
- `lpLockedPct` — 流动性锁仓百分比

常见风险信号：
- Top10 持仓 >70% → 抛压风险大
- 单一地址持仓 >50% → 控盘嫌疑
- LP Locked <50% → 可能 Rug

## 三、高热度判断标准

通过 X 搜索结果判断是否为"现象级"：
- **市值峰值**：> 30M USD 算现象级（Solana 几个月才出一个）
- **速通速度**：从发币到峰值 <24 小时
- **KOL 背书**：知名人物（如 Ansem/@blknoiz06）明牌喊
- **社交热度**：推文阅读 >10K，互动 >100

## 四、数据源局限性

| 数据源 | 可用性 | 说明 |
|--------|--------|------|
| Solana RPC | ✅ 稳定 | 只查供应量，不查价格 |
| Rugcheck | ✅ 稳定 | 风险评估，无价格 |
| Birdeye | ⚠️ 需 API Key | 价格/交易量/持有者分析 |
| Jupiter Price | ❌ SSL 错误 | 被代理/Cloudflare 阻挡 |
| DexScreener | ❌ Cloudflare | 网页端被挡 |
| gmgn.ai | ❌ Cloudflare | 网页+API 均被挡 |
| CoinGecko | ⚠️ 有时被挡 | 适合主流币，迷因币少 |

## 五、建议用户操作

当链上数据无法直接获取时：
1. 让用户打开 gmgn.ai / DexScreener 搜索合约地址
2. 截图发过来，用 vision 分析
3. 或者用户直接告知当前价格/市值
