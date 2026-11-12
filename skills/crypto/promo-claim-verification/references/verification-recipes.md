# 验证配方（可直接复制的命令 + 实测基准）

会话实测记录（2026-10），所有数字都是真实跑出来的，可作为下次判断的基准线。
所有外网命令都需要代理前缀：`HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890`。

---

## 1. 验证"某人赚了 $X"（Polymarket —— 公开账本，30 秒可查）

老的 `lb-api.polymarket.com` 已废弃（返回 `CRAWL_NOT_FOUND` / 403）。用：

```bash
# 全站排行榜（all-time PnL），拿 500 条足够覆盖高位
curl -s --max-time 30 "https://data-api.polymarket.com/v2/leaderboard?window=all&limit=500" -o lb.json
jq -r '.data|length' lb.json
jq -r '.data[] | select(.user_name|test("mo-money";"i")) |
  "\(.rank) \(.user_name) \(.user_id) pnl=\(.pnl) vol=\(.volume)"' lb.json
```

- 返回字段：`rank / user_id / pnl / volume / user_name / x_username`。
- **实测校准**：被宣称"125 天赚 $508,183"的账号 `mo-money`，真实 all-time PnL = **$7,477，rank #211**（差 **68 倍**）。
- **关键交叉验证**：同时看榜首量级——当时的 #1 是 $548,782、#2 是 $413,089，而**全站前 500 名里没有任何人 PnL 落在 48-53 万区间** → 被宣称的数字在整个平台上根本不存在。这种"数字落在分布空档"的观察比单点比对更硬。

```bash
# 看他的真实仓位规模（判断帖子里的仓位数字是否可信）
U=0x32ed2e546b187ca15e2841edc82b22c713cf8ec3
curl -s "https://data-api.polymarket.com/positions?user=$U&limit=10" | \
  jq -r '.[] | "\(.title[0:40]) | size $\(.size) | curValue $\(.currentValue)"'
```
- 实测：号称"投入 $1,666 变 $4,175"的账号，真实单笔规模 **$5–$459**（最大持仓 $1,899）→ 帖子里的仓位量级夸大 3-10 倍。
- **注意留存判断**：策略描述可能是真的（该账号确实在做 BTC/ETH 5-15 分钟 Up-or-Down 市场），**假的是数字**。要分开说。

## 2. 验证代币上线/时间/经济模型

```bash
# 交易所官方公告（Binance 公告 API）
curl -s "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=30" | \
  jq -r '.data.catalogs[]?.articles[]? | .title' | head -20

# 项目官方 tokenomics（常是 PDF，含 TGE 流通比例 + 解锁表）
mcporter call exa.web_fetch_exa urls='["https://<project>/assets/<...>.pdf"]'
```
- **实测（NeoSoul/$DNA）**：官方文档写 Binance Alpha **10月16日 16:00 (UTC+8)**、OKX 永续、Bitget 11:00 UTC、Gate/MEXC/KuCoin 同日；总量 1B、**TGE 只流通 13%**、投资人/团队/顾问 TGE 零释放锁 12 个月、生态 4-39 月解锁；合约 `0xA991F6…c5CF7b`。
- **而转发帖写"北京时间 8 点"** → 时间错误。**帖子连上线时间都没核准，是判断帖子性质的有力证据。**
- 次要源可用 ChainCatcher / Bitget 支持页（`bitget.com/support/articles/...`）交叉印证。
- 与链上传闻对账：`gmgn-cli token info --chain bsc --address <CA> --raw` —— 实测 TGE 前状态为 LP 已建（$1M）但**持币仅 23 个**。

## 3. 算术自检（不联网，先做）

```python
# 复利外推：倍率能维持几天？
c = 52.0
for d in range(1, 6):
    c *= 223
    print(f"第{d}天: ${c:,.0f}")
# 第4天 1286亿（> Jane Street），第5天 28.7万亿（> 全球加密市值）→ 证伪
```
自查清单：
- 日收益 × 天数 = 累计？（对上只说明内部自洽，不代表真实）
- **每笔均值 × 笔数 = 累计？** 与"每小时 N 轮"是否相容？（$508,183 案例在这里崩掉：差 50 倍）
- 胜率是否配了平均盈亏金额？（不配 = 废数据）
- 达到目标档位的**机制**需要什么前提？（预置库存、跨平台转账时间、手续费）

## 4. 验证 GitHub 项目 / 产品能力

- 存在性 + **控制组**（假仓库必须 404）方法在 `multi-platform-search-cli` 的 "Verifying that a claimed project/repo actually exists"。
- 读官方自己的文档，不要只读 README 首段：
```bash
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/main/README.md"
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/main/docs/performance.md"
```
- **实测（browser-use/jev-ultrafast）**：`README` 需 `TYPESAFE_API_KEY` → **核心决策模型是托管 API，不是"本地决策核"**；`docs/performance.md` 给 **决策延迟中位数 178 ms**、Flights 任务 7.073 s（对比 9.450 s）、浏览器协议调用 1,092→101，**并自曝"三组样本统计力不足 p=0.25"+"TypeSafe 只给 token 数不给计费金额"**。
  → 官方文档自我披露 = 可信度**加分**；转发帖说的"本地"、"成本双杀"是**加戏**。
- 一个仓库存在只证明**名字**是真的。

## 5. 激励结构：识别导流

- 推荐码形态：`fomo.family/r/<code>`、`t.co/<short>`（配合"在这里交易"文案）。
- 带自研代币的工具：README 里挂 `$<TOKEN> on pump.fun` + 自家 launchpad → 靠你发币赚钱（实测 gem-search：有代币 + 双链 launchpad）。
- 话术模板（遇到即提高警惕）：**"完不成我就删除"**（虚构赌注）· **"它没有跟我申请延长"**（拟人化叙事）· **"我全程没有动手改任何东西"**（免责铺垫）· **"相比短期价格，我更关心商业模式"**（软性免责）· 只给盈利样本不给亏损（幸存者偏差）· 借用机构名头（"Jane Street 量化代理"——Jane Street 是自营做市，**不做散户代理**，该职位不存在）。

## 6. 报告模板（按本用户偏好）

```
判定：<假 / 部分真 / 真>（一句话）

一、算术自己就把它杀了        ← 最便宜的证据放最前
二、这篇的真实商业模式        ← 推荐码/代币/导流
三、机制上跑不通（技术层）    ← 预置库存/手续费/时间
四、它故意不给的数字          ← 平均盈亏、成本、失败样本
五、核实到的真东西            ← 该承认就承认（账号真、仓库真、上线真）
六、这是同一波的第几篇        ← 模式 vs 单点
七、你可以自己验的下一步      ← 命令或脚本
```
