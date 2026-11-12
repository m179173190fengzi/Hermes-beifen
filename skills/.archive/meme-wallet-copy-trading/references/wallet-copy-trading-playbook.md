# Wallet Copy-Trading Playbook — 带来源全文（Solana + BSC meme）

每条结论后附来源 URL。找不到量化阈值处明确标注「未找到」。仅研究，非投资建议。

## 0. 前提纠正：fomo 标签 + 「30天已实现盈利 TOP5」

- **`fomo` 是「平台使用标签」，不是聪明钱标签。** GMGN 官方博客：标签只说明「这个地址用过哪个平台」，不代表资金来源。某币前 100 持有者中 **42 个带 fomo、17 个 gmgn、1 个 axiom**；前 100 交易者 45 fomo / 26 gmgn。
  https://gmgn.ai/blog/what-to-check-after-finding-a-trending-memecoin/
- **fomo.family 的 top traders 偏长期持有。** App Store 用户反馈 + 开发者回复：大部分 top traders 是长期持有、资产在增值的人，无短线洞察；要短线通知请关注风格相近的人。
  https://apps.apple.com/us/app/fomo-never-miss-out/id6741115427
- **「30 天已实现盈利排名」= 循环论证。** 原文："A win rate is an output, not evidence."；排名用的度量（已实现盈亏）本身被当证据，天然奖励自导自演的假市场和高换手刷量。
  https://dev.to/verixia_233e4721792ce3390/how-copy-trading-rugs-work-when-the-wallet-you-follow-is-the-trap-198n
- GMGN 图表上的 Fomo 标记来自第三方指数 **FomoScan**（官方声明与 fomo.family 无关联），按已实现 PnL 排名，有最小 round-trip 与成交量门槛；GMGN 未公开取哪个窗口/取到第几名。
  https://gmgn.ai/blog/how-to-read-fomo-calls-on-gmgn-chart/

## 1. 选钱包阈值

| 指标 | 阈值 | 来源 |
|---|---|---|
| 7 天胜率 | 50%–90%（无好钱包可 40%–90%） | https://www.reddit.com/r/CryptoTrenching/comments/1lfebic/how_to_find_good_wallets_to_track/ |
| 实盘更严 | 70%+ 胜率 / 50+ 笔 | https://www.reddit.com/r/SolanaMemeCoins/comments/1rnhud6/i_spent_over_5k_on_rpc_nodes_and_30_days_of_my/ |
| 样本量 | 7 天 ≥100 笔 TX | r/CryptoTrenching（同上） |
| 平均持仓 | 避开秒级；GMGN Phishing 标「5 秒内买卖」 | https://gmgn.ai/blog/how-to-track-copy-solana-smart-money/ |
| 单笔 vs 池子 | 相对池子要小 | https://memecentral.fun/guides/copy-trading-memecoin-wallets |
| 稳定性 | 7D vs 30D 并排；去掉单笔最好交易后仍成立 | GMGN 同上；memecentral 同上 |
| 资金源 | 拒绝与部署者共用 CEX 子账户/桥 | r/SolanaMemeCoins（同上） |

**三个坑**：A 排行榜赢利可自导自演（自己发币+隐藏钱包拉盘）；B 少样本（kolscan 30天榜前50名输多于赢，中位胜率 1d/7d 43%、30d 34%，72% 低于 50%，中位交易数 1375）https://accompli.sh/research/onchain-memecoin-trading-study/ ；C 高换手刷量（rugs_trap）。

**5 问筛选法**（rups_trap 原文）：①钱从哪来（大赢是否在微盘）②谁资助它/它资助谁（gas 与部署者同源 = 演员）③多老多稳（几个月真实 > 三周神迹）④优势是否依赖抢第一（依赖则不可复制）⑤是否卖信号/收费群。
来源：https://dev.to/verixia_233e4721792ce3390/how-copy-trading-rugs-work-when-the-wallet-you-follow-is-the-trap-198n

## 2. 择时 / 延迟

- 6 步延迟：上链 400ms + 索引 1–5s + 扫描 0.5–3s + 警报 0.5–2s + 人反应 0.2–0.5s + 下单 400ms。**乐观 3–7s，现实 10–30s。** 新盘头 30s 常 $50k→$150k–250k（3–5x）。
  https://xhuntr.com/blog/why-copy-trading-kols-on-solana-fails
- 买晚是买贵，卖晚是砸在下跌簿里，滑点更差；联合曲线上后买必然更高价（确定性劣势）。
  https://memecentral.fun/guides/copy-trading-memecoin-wallets
- 回测：头 10 秒入场赚钱；1–10 分钟窗口亏得最多（接盘流动性）；即便叠加过滤器把 100k 峰值率抬一个数量级，也没让「晚 60 秒」的买家盈利（去掉唯一 runner 后所有倍数 <1.000）。
  https://accompli.sh/research/onchain-memecoin-trading-study/
- 结论：只跟 edge 能扛过延迟的钱包；薄池子不跟；机器对机器去掉人反应 1–2s。
  https://xhuntr.com/blog/why-copy-trading-kols-on-solana-fails

## 3. 共识 / 集群

- Reign 默认 min 2 / 24h；配方：<20 钱包 min2/24h；20–100 min3/6h；100+ min4/1h；**Solana meme min2/30m**。
  https://docs.reigntracker.com/features/cluster-alerts/
- 开源检测器默认 min_wallets=3 / window 15min / 评分加权。
  https://github.com/baronguyen001/wallet-cluster-detector
- Nansen：10+ 聪明钱 48h 内同买 = 协同信念；名单 10–20 钱包起步。
  https://nansen.ai/post/how-to-track-solana-wallets-complete-guide-for-smart-money-analysis
- RugSniffer：两个「历史早期命中率 ≥50% 且不 scalp」钱包进同一新盘 = signal。
  https://rugsniffer.com/
- 伪造共识特征（同一时间创建/相同资金源/同批代币同步/利润回流同地址）；关联集群 >20% 供应风险显著升高。
  https://defade.org/blog/solana-memecoin-insider-networks
- Nansen：多钱包同天创建、只交易单一代币 = 协同非独立。

## 4. 过滤器

- GMGN 默认线：Top10 30%、DEV 30%、Insiders 5%、Phishing 5%、Bundlers/Fresh/Sniper/Rugged 10%；Burnt 100% = 无法提款。Top10 只覆盖 10 地址，要看前 100 累计（`TOP100 Owned`）。
  https://gmgn.ai/blog/what-to-check-after-finding-a-trending-memecoin/
- Bundle% = `bundler_trader_amount_rate`（多少成交量来自打包），非安全评级；AI 示例用 0.3 作筛线。
  https://gmgn.ai/blog/what-is-a-meme-coin-bundle/
- Axiom：Bundle% 规则 = 同一区块 ≥4 笔；snipers/insiders/dev hold 无公布方法。
  https://apebrief.com/axiom/token-metrics/
- MELT：相关账户覆盖——同一笔交易 9.16% + 共享资金源 28.22% + 共享 Jito bundle 15.96% = 合计 36.5%。
  https://gmgn.ai/blog/what-is-a-meme-coin-bundle/
- 回测命中率提升：Twitter 主页 7.2% vs 无 0.9%；有官网 5.0% vs 无 0.3%；单次发射 5.0% vs 连环发币 0.4%；叠加「非连环/非克隆/有官网」100k 峰值率 2.2%→15.2%。每个 100k 峰值都来自「窗口内 <3 次 + 有官网」创建者。
  https://accompli.sh/research/onchain-memecoin-trading-study/
- USENIX 2023：BSC 上 1% 地址创建 24.3% 代币；4,231 个 spammer 中 50% 至少一次 rug；约 60% 代币存活 <1 天。
  https://gmgn.ai/blog/what-to-check-after-finding-a-trending-memecoin/
- 流动性 <$10k 结构性脆弱；<$50k HIGH RISK；量/LP >5x 提示操纵；币龄 <24h 极高风险，<7d 高风险，>90d 较低。
  https://medium.com/@fxmbrand/what-actually-happens-before-a-meme-coin-pumps-and-why-most-people-chasing-it-get-rugged-c7129c96ecc6 ；https://github.com/Spydiecy/Sniffle
- 蜜罐：honeypot.is（模拟买+卖）https://honeypot.is/ ；Guava/GoPlus（蜜罐+mint+隐藏owner+代理+暂停/黑名单+LP锁）https://www.guavaintel.com/bsc-honeypot-checker

## 5. 退出

- 1–5% 仓位法则；止损按入场大小反推（蓝筹 -20%、新低市值 -80%）。
  https://trojan.com/blog/solana-memecoin-risk-management
- Trojan：2x 卖 50% → 5–10x 卖 25% → 尾仓 50x–1000x 分层 + 止损。
- TechBullion：2x 卖 25%、4x 卖 25%，剩余挂移动止损。
  https://techbullion.com/when-to-sell-crypto-in-a-meme-coin-rally-ladders-trailing-stops-and-size/
- TradeLabs 模板：SL -40%；移动止损 +20% 启动、回撤 25%；+50% 移止损到成本；2x 收回本金；3s/1s 检查周期；失败重试 2/5/10/30s。
  https://tradelabs.org/docs/templates/memecoins-robinhood-chain/
- RugSniffer：TP +50/+100/+300%，SL -30%，时间止损 + 死亡检测器。
  https://rugsniffer.com/
- 移动止损宽度：15–20% scalp / 25–35% 甜点 / 40–50% 高信念。
  https://madeonsol.com/blog/solana-memecoin-exit-strategy-guide
- 时间止损 12h/24h/3d；分层减仓 30/40/30。
  https://crypto.lethanhnamwork.com/stop-loss-strategies-that-actually-work-for-meme-coins/
- GMGN：Follow-Selling 与自设 TP/SL 二选一（开 TP/SL 自动关 follow-selling）。
  https://docs.gmgn.ai/index/copy-trade-copy-smart-money-automatically-earn-sol

## 6. 失败模式来源

- 内部人网络（资金树/往返/协同砸盘 5–10min/跨代币网络）：https://defade.org/blog/solana-memecoin-insider-networks
- 伪造战绩、退出流动性、卖信号、MEV 三明治、慢速流失：https://dev.to/verixia_233e4721792ce3390/how-copy-trading-rugs-work-when-the-wallet-you-follow-is-the-trap-198n
- 蜜罐：https://www.guavaintel.com/bsc-honeypot-checker
- BSC Gas 战/三明治 + four.meme Mubaraking 案例：https://blockrazor.io/blog/20250421SANDWICH.md
- 滑点/失败交易仍扣费：https://www.cheetah.trading/learn/copy-trading-risks
- 钱包碎片化（3–7 钱包）：https://xhuntr.com/blog/why-copy-trading-kols-on-solana-fails
- 幸存者偏差/晒单：https://medium.com/@fxmbrand/what-actually-happens-before-a-meme-coin-pumps-and-why-most-people-chasing-it-get-rugged-c7129c96ecc6
- 波动中卖不出：https://memecentral.fun/guides/copy-trading-memecoin-wallets
- 费用复利（fomo 每笔 $1）：https://apps.apple.com/us/app/fomo-never-miss-out/id6741115427
- reorg（BullX/Photon 未防护）：https://www.crypto-reporter.com/press-releases/banana-gun-vs-trojan-vs-bullx-a-90-day-memecoin-trading-bot-comparison-from-a-working-trader-126508/
- 集群 1 小时抽走 $87M（$LIBRA）：https://blog.bubblemaps.io/the-libra-playbook-how-one-cluster-drained-87-million-in-a-single-hour/

## 7. 工具对照

- Nansen / GMGN / Cielo 对比：https://madeonsol.com/blog/nansen-vs-gmgn-vs-cielo-smart-money-solana
- GMGN / Cielo / Axiom 跟单对比：https://madeonsol.com/blog/best-solana-copy-trading-bots
- GMGN Copy Trade 参数与限制：https://docs.gmgn.ai/index/copy-trade-copy-smart-money-automatically-earn-sol
- Maestro vs Photon：https://solanatradingbots.com/compare/maestro-vs-photon/
- Banana Gun vs Photon：https://solanatradingbots.com/compare/banana-gun-vs-photon/
- Banana vs Trojan vs BullX 90 天实测（蜜罐拦截 4/2/3）：https://www.crypto-reporter.com/press-releases/banana-gun-vs-trojan-vs-bullx-a-90-day-memecoin-trading-bot-comparison-from-a-working-trader-126508/
- 开源自建 BSC：https://github.com/cnm750x/four.meme-copy-trading （默认 SLIPPAGE_BPS=300，MIN_GAS_PRICE_GWEI=5）
- RugSniffer（≥70/100 才发 signal，TP +50/+100/+300%，SL -30%）：https://rugsniffer.com/
- GMGN 图表 Fomo 标记：https://gmgn.ai/blog/how-to-read-fomo-calls-on-gmgn-chart/

## 附：未找到确切数字的部分

- 跟单者实际实现的收益：无公开数据集（memecentral 原文明确）。
- 「几钱包算强」的普适经验值：各家只给可调默认值（Reign 2 / 开源框架 3 / Nansen 10+），无跨市场验证的绝对数字。
- GMGN 官方钱包标签完整清单：未找到（`Featured Icon Definition` 文档页面只给了部分定义：Smart Money / Pump Smart Money / Sniper / KOL / Suspected phishing）。
  https://docs.gmgn.ai/index/featured-icon-definition
- BSC 上「fomo 标签钱包」的跟单表现：未找到任何针对性统计。
