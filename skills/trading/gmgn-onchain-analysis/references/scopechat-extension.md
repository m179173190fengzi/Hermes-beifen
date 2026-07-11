# X/Twitter 名人标签插件：Scopechat (0xScope)

## 是什么

Scopechat（原名 0xScope）是一个 Chrome/Edge 浏览器扩展，在 **X.com（推特）** 上自动给币圈推文作者打标签：
- 🐋 Whale — 鲸鱼大户
- 👑 SmartMoney — 聪明钱
- 🎙️ KOL — 喊单名人
- 💰 VC — 风投
- 🤖 Bot — 机器人
- 🔥 Degen — 赌狗

用于快速判断一条推文是谁发的、有没有参考价值。

## 与 GMGN Extension 的区别

| 功能 | Scopechat (0xScope) | GMGN Extension |
|:-----|:--------------------|:---------------|
| X/Twitter 标签 | ✅ 主功能 | ✅ 也有 |
| DexScreener 标签 | ✅ | ✅ 更详细 |
| 聪明钱追踪 | ✅ Scopechat 平台 | ✅ GMGN 平台 |
| 国内流行度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 安装方式 | Chrome Web Store / 官网 | GMGN 官网下载 .crx |

> ⚠️ **用户偏好**：当用户说"X名人插件"或者"推特名人显示插件"时，**默认指 Scopechat（0xScope）**，不是 GMGN Extension。不要猜错。

## 下载方式

### Chrome Web Store（推荐）
```
https://chromewebstore.google.com/detail/scopechat-tweet-tagger/akbkkmniehbjngifggfadbgmojbgonmf
```
需登录 Google 账号。如果提示「此商品无法购买或下载」，尝试切换区域或直接在搜索框搜 "scopechat"。

### Edge 浏览器
Edge 可以直接装 Chrome 扩展：
1. Edge → `...` → 扩展 → 管理扩展
2. 打开「允许来自其他商店的扩展」
3. 去 Chrome 商店安装同上链接

### 无影云桌面 / 浏览器受限环境
如果 Web Store 打不开或卡住：
1. 找个能正常上网的机器，从 Chrome Web Store 或 Scopechat 官网下载 .crx 文件
2. 拷到目标机器
3. 浏览器 → `chrome://extensions/` → 打开「开发者模式」
4. 把 .crx 拖进去

### 官网（备选）
```
https://0xscope.com
https://scopechat.ai/extension
```
注意：这两站都有 Cloudflare 防护，需要开代理才能访问。

## 安装后设置

1. 打开 Scopechat / 0xScope 官网，用 X/Twitter 账号登录
2. 授权浏览器扩展连接你的账号
3. 去 X.com 刷推，每条推文右上角会显示标签
4. 点标签可以查看该钱包的持仓/盈亏详情

## 故障排查

| 问题 | 原因 | 解决 |
|:----|:-----|:-----|
| 装了但没显示标签 | 未登录 Scopechat 账号 | 去 0xscope.com 注册/登录 |
| 显示「无法获取」 | 需要翻墙 | 打开代理后刷新 X.com |
| 标签全是机器人 | 新账号/无钱包绑定 | 绑定钱包地址到 Scopechat 账号 |
| Chrome 商店搜不到 | 区域限制或下架 | 用 Edge 或直接 .crx 安装 |
| 无影云桌面 Chrome 卡 | 配置太低 | 用 Edge 浏览器，比 Chrome 轻量 |
