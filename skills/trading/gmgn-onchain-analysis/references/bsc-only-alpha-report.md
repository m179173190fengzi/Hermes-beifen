# BSC 单链 Alpha 简报（cron「BSC链Alpha情报合成师」）运行笔记

Cron 变体：**只扫 BSC 单链**（取消 Solana / Robinhood，不做跨链镜像），纯文本直发 Telegram（**不生成任何 HTML**）。触发数据源：BSC trending 6h + TVL(BSC) + hot-searches(BSC) + trenches(BSC)。

## 输出格式（5 段）

1. **💰 BSC TVL** — BSC TVL + 7d 变化 + 一句话结论（🔴/🟢）
2. **💥 BSC成交量TOP5** — trending 6h 按 `volume` 降序取前 5；**只列符号不列 CA**；每条之间空一行；字段：MC / LP / 6h / 量
3. **🔥 BSC链优质标的** — 得分榜；每条带 📋叙事 / 🏷️类别 / 💵MC·评分 / ✅11项检查 / 👥持币·聪明钱 / 📈6h / 🐦推特 / 🔗CA / ⚠️注意 / 💡价值
4. **🆕 BSC新币监控（1D内 MC稳定≥$1M）** — 无合格时明写「严格标准下无合格新币」+ 列接近标的
5. **🧠 叙事验证 & Alpha** — 核心叙事簇 / 🚩预警 / 📊TVL联动 / 🎯建议关注

硬规则：**禁 pipe table**（TG 不渲染）；除 TOP5 段外**每币必带完整 CA + 叙事**（不能只给数据）；结论先行；无 ≥70 准推级但有热点/TVL/新盘时**照常推送**并明说「本日无准推级」（SILENT 只用于「无热点且无信号」）。

## 双门槛评分（与三链变体的关键差异）

- **门槛1：75分制** A共识(0-25) + B数据健康(0-20) + C体量(0-12) + D动量(0-10) + E叙事(0-8)，**≥60 进观察级**（≥70 准推）
- **门槛2：11项评分 ≥6/11**
- **两条都过才进「优质标的」完整条目**；75分≥60 但 11项<6 的 → 只进一行「观察名单」（分数/叙事/风险 + 行内 CA）
- 11项字段源：①LP>$30K→trending `liquidity`；②LP锁定→`token security` `lock_summary.is_locked`+`lock_detail[].is_blackhole`（或 UNCX Locker `lock_percent`）；③EVM `is_renounced`；④EVM 不适用计过；⑤`top_10_holder_rate`<20%；⑥`bundler_rate`<15%；⑦`creator_token_status`=creator_close 计过 + `dev.creator_open_count` >10 盘=职业 dev ❌；⑧社交通常老盘✅/新盘❌；⑨粉丝真实→存疑不计；⑩holders 增长→新盘✅/老盘存疑；⑪vol6h/LP≥0.5
- 硬规则仍优先于分数：bundler>30% 不推 / rug>0.3 剔除 / MC<$10K 不推 / top10>70% 标高度控盘

## BSC TOP5 常年被合成/证券盘霸占（重要读数）

按 volume 取的 BSC TOP5 常**全部是非 meme 标的**——必须在 TOP5 段照列但标注「非 meme 博弈标的」，且**不进优质标的/新币段**。已确认样本（2026-10-14）：

| 符号 | name | 类型 |
|------|------|------|
| pPOLY | Paimon Polymarket SPV Token | **SPV（特殊目的载体）**，price $16.77 / circ 32.3万 / LP $4.11M |
| QQQB | Invesqo QQQ | 合成 ETF |
| BNCB | Binance Coin B | 合成 |
| NVDAB | NVIDIA | 合成股票 |
| TNHB/AAPLB/GMEB/TSLAB/SPCXB/BABAB | 真实股票代码 | 合成股票簇 |
| BNC4 | Cea Industries | **真实 Nasdaq 公司**（price $5.07 / circ 123万 / holders 7.2万） |
| FXIon | iShares China ETF | 合成 ETF |
| SKHYB | SK Hynix | 合成（韩国半导体，top10 91.6%） |
| BEM | BEM（web=tapeout.net 半导体） | 科技 SPV |
| CT | Concrete Token | 真实 DeFi 实用型（top10 78%，非 meme） |
| DOS / ARX | DAPPOS（意图）、Arcium（机密计算） | 真实项目盘 |

**读数**：TOP5 100% 合成/证券/实用盘 = 资金在「类股票」标的里空转、**真实 meme 端成交萎缩 = 存量博弈市**，写进 TVL 结论。判据：`price` 与真实股价同量级 + `circulating_supply` 数量级为「份额式」（<10^6，非 10 亿 meme 式）+ `created=0/open=0`（无 launchpad）→ 合成盘。识别非 meme 的通用法：token info 的 `name` 是公司/产品全名、`web` 指向企业站 → 排除。

## 2026-10-14 早场（05:46 BJT）运行记录

- **TVL**：BSC $5,396M（7d **-6.4%** 净流出，较 10-11 晚场 $5,576M/-4.4% 进一步失血）——与链上真实 meme 缩量互证，主线「存量博弈」
- **TOP5（6h by volume）**：pPOLY $5.43M / QQQB $4.00M / BNCB $2.75M / NVDAB $2.60M / CT $2.36M（全合成/实用盘）
- **本日无准推级（全场最高 68）**：观察到 8 条双门槛达标（75分≥60 且 11项≥6）——
  - 旺柴 68（A25 B20 C12 D5 E6；MC $19.41M，top10 17.83%/bundle 0% 全绿，11项 8/11，唯一 A25+B20+C12）
  - Moolah 64（A25 B20 C12 D2 E5；MC $38.91M，top10 **6.61%** 全链最分散但 6h 量仅 $189K 极冷）
  - SAFU 63（A25 B20 C8 D2 E8；币安经典梗 Funds Are Safu，tw=cz_binance/status/ 喊单伪装，dev 开 45 盘）
  - 龙虾 62 / 牛来 61 / MarsCoin 61 / 哈基米 61（均 top10 66-83% 高控盘 + 6h 量 <$500K 极薄）
  - 破茧成蝶 60（11项 7/11，数据干净但 MC 仅 $263K 小盘）
  - 一行观察名单（11项<6）：我踏马来了 61、うさぎ 61
- **新币段**：**严格标准无合格新币**——BSC trenches `new_creation --min-marketcap 1000000` 返回空 `{"new_creation":[]}`；trending 侧 1D 内新盘全 <$100K（币安理论 7.6h $143.6K 最接近、binancians 11.7h $103.7K）
- **核心叙事**：**口字辈币安/CZ 中文梗簇**同日批量部署——币安理论 / 何一的书(=币安日记，name「何一的书」)/ binancians（tw=binance 官方推文伪装，dev 开 38 盘，6h -44.57%）/ BIBI(Binance AI) / 币安借呗 / BinanceMan / GM(GREEN MORNING, tw=cz_binance) / SAFU / CZ。喊单源多为 cz_binance / binance 官方推文伪装链接 = 「大号喊单载体簇」
- **预警**：binancians 6h -44.57%（职业 dev 收割）/ 中国人能飞 -12.74%（bundle 24.9% 贴线）/ CZ 6h -31.43%（D0，08-02 阴谋盘主角转弱）/ TeslaSI -74.73% / SpaceXSI（name=「QQ:467286912会议:921336836」推广垃圾命名）
- **dog/动物梗簇**：旺柴（狗，$19.4M）/ 哈基米（猫，$25.2M，1 年老盘 CTO）/ 龙虾（虾，$46.5M）/ 招财猫（$2.58M）/ うさぎ Suica Rabbit（$980K）——中文动物梗线，均老盘高控盘缩量

## 工具流（本场确认可用）

- 抓取：`HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 gmgn-cli ...`（**所有外部请求必须带代理前缀**）
- TVL：`python3 <skill_dir>/scripts/tvl-7d-change.py` 只取 BSC 行（实算 7d，脚本已内置代理；BSC slug = `BSC`）
- 评分/TOP5/新币：自写脚本（`write_file` → `python3 /tmp/xxx_<ts>.py`），trending `--raw` 是 `data.rank` 数组；hot-searches `--raw` **有时是根级 flat list**（`[{chain,interval,tokens}]`）——先 `isinstance(d, list)` 再取
- 候选核验：`token info --raw`（扁平对象）+ `token security --raw`（扁平对象）批量抓，JOB=PID 前缀隔离；**打印创建时间务必带 `%Y`**（见 SKILL.md 坑表）

## 🆕 11项评分可直接从 trending `--raw` 字段算出（零额外请求，抗限流）

**关键效率发现（2026-10-14 午场实测）**：`market trending --raw` 的 `data.rank[]` 每条**已带齐 11 项里绝大多数判据字段**，无需再对每个候选跑 `token info` + `token security`（省掉 N×2 次请求——429 高发时段这是决定性的）：

| 11项 | trending `data.rank[]` 字段 |
|------|------------------------------|
| ① LP>$30K | `liquidity` |
| ② LP锁定/销毁 | `lock_percent` ≥ 0.5 **或** `burn_status` == "yes" |
| ③ 铸币权限（EVM=owner renounced） | `is_renounced` == 1 |
| ④ 冻结权限（EVM 不适用） | 计过 |
| ⑤ top10<20% | `top_10_holder_rate` |
| ⑥ bundler 干净 | `bundler_rate` < 0.15 |
| ⑦ dev 无抛弃史 | `creator_token_status`（= creator_close 计过；creator_hold ✗）|
| ⑧ 社交>1周 | `creation_timestamp` 算年龄 >7d **且** `twitter_username`/`website` 非空 |
| ⑨ 粉丝真实 | 无数据 → 存疑（默认 ✗）|
| ⑩ holders 增长 | 无趋势数据 → 存疑（默认 ✗）|
| ⑪ vol6h/LP ≥ 0.5 | `volume` / `liquidity` |

实测校准：旺柴 8/11、牛来 7/11、龙虾 7/11、BS 8/11、柴犬小黑 7/11、MarsCoin 6/11——与 token info 侧核验结果一致（BSC EVM 盘 `is_renounced`/`lock_percent`/`burn_status` 在 trending raw 里均有值，③④ 无需 security）。**流程：先用 trending raw 全量算 11 项 + 75 分，只对最终入榜的 2-3 个候选补 `token info`（取叙事/description/dev_open_count）**，把 token info 从「每个候选都跑」降为「只补入榜者」，抗 429 且省时。

## 2026-10-14 午场（13:58 BJT）运行记录

- **TVL**：BSC **$5,408M**（24h +1.0% | 7d **-6.7%**）——较早场 $5,396M/-6.4% 继续净失血，主线「存量博弈」不变
- **TOP5（6h by volume）**：pPOLY $42.82M / NVDAB $10.07M / BABAB $9.07M / AAPLB $7.88M / QQQB $4.67M——**再次 100% 合成/证券盘**（SPV+4 合成股票/ETF），真实 meme 未进前五
- **本场无准推级（全场最高 65）**，双门槛达标 3 条：
  - **旺柴 65**（A25 B20 C12 D2 E6；MC $18.40M，top10 17.8%/bundler 4.3%/rug 0 全绿，11项 8/11）——早场 68 → 午场 65（D 从 5 掉到 2，6h -5.7%/1h -13.4% 动量转弱）
  - **牛来 62**（top10 83.3% 极端控盘 + dev 开 27 盘，11项 7/11）
  - **MarsCoin 60**（太空簇，top10 66.8%，11项 6/11）
  - 观察名单：BS 59（热搜#1，6h +17,080%，bundler 19.6%/bot 74%）、柴犬小黑 59（新盘）、龙虾 58
- **新币段**：严格标准无合格新币（trenches 空；1D 内新盘全 <$300K，最接近 柴犬小黑 $253K）
- **核心叙事：Black Shiba 同名狗梗簇**——4 个同名「Black Shiba」地址同窗（BS 0x6cce34 $406.7K 热搜#1 / BS 0x545aba $32.1K 新盘 / 柴犬小黑 $253K 热搜#2 / 黑柴 $7.9K）+ 中文狗系老盘 旺柴 $18.4M，狗梗接管当日主线
- **退潮预警**：币安/CZ 口字辈梗簇集体放量下跌——binancians -51.3%（职业 dev 收割）、CZ -38.8%、小王子 -27.0%、币安理论 -20.8%、SAFU -16.7%、BREW -14.3%
- **限流对策（本场实测）**：GMGN IP 被封 429 多次，`reset_at` 因探活不断后滑；改为「等到 reset+90s 再单发」后 trending/hot/trenches/批量 token info 全部打通。批量 token info 时**首条成功后即被封**（bucket 被抽干），等 2 分钟重跑后 5 条全通 |

## 75分制 A/B/C/D 具体档位表（实测校准，跨运行可复现）

⚠️ 早前记录只写了分项结果（如「旺柴 68 = A25 B20 C12 D5 E6」），**档位表一直缺**——现补全，否则每次运行各自发明档位、分数不可比。**首要教训（2026-10-15 早场实测）**：用保守档位（SM 38 只给 A14 + KOL 不进 A）算出 旺柴 base 44，与历史 A25+B20+C12 差 10+ 分，全场除 1-2 枚外无人达 60，报告发虚失真。**A 档位必须宽松**——BSC meme 的 SM 三四十已是强共识，要接近满档。

**A 共识 (0-25)** = min(25, SM档 + KOL档)
- SM: ≥30→18 / 15-29→15 / 8-14→12 / 4-7→8 / 1-3→4 / 0→0
- KOL: ≥30→7 / 15-29→6 / 8-14→5 / 4-7→3 / 1-3→1 / 0→0
- 校验: 牛来(SM525/KOL178)=25 ✓、GM(SM146/KOL52)=25、BS(SM104/KOL29)=24、旺柴(SM38/KOL14)=23

**B 数据健康 (0-20)**：起始 20，扣项累加，floor 0
- rug: >0.3→-12 / 0.1-0.3→-5 / <0.1→0
- bundler: >0.3→-10 / 0.15-0.3→-5 / <0.15→0
- top10: >0.7→-8 / 0.5-0.7→-5 / 0.2-0.5→-3 / <0.2→0
- is_wash_trading=true→-8

**C 体量 (0-12)** = MC档 + LP档 + vol档，min 12
- MC: ≥20M→5 / 10-20M→4.5 / 5-10M→4 / 2-5M→3 / 1-2M→2.5 / 0.5-1M→2 / <0.5M→1
- LP: ≥1M→4 / 500K-1M→3.5 / 200-500K→3 / 50-200K→2 / 30-50K→1.5 / <30K→0.5
- vol6h: ≥1M→3 / 500K-1M→2.5 / 200-500K→2 / 50-200K→1.5 / <50K→1

**D 动量 (0-10)**（先判 1h，防「6h 大涨+1h 深跌」抛物线顶部误判为强）
- chg1h ≤ -20% → 2（放量出货，硬压）
- 否则按 chg6h: ≥40 且 chg1h≥0→10 / ≥20→8 / ≥5→6 / ≥0→5 / ≥-10→4 / ≥-25→2 / <-25→0

**E 叙事 (0-8)** 手判：老梗主盘/CTO 已验证 6-7 / 有推特官网的实际梗 5-6 / 推广推文伪装的新盘 3 / 无叙事 3-4

**合成/证券盘剔除**：`is_stock_like()` = launchpad_platform 空 **且** total_supply<2e6（份额式非 10 亿 meme 式）**且** name 含公司名（Nvidia/Apple/Invesqo/SPV/ETF/Hynix/Industries/Polymarket…）→ 即使 75 分高也只进 TOP5 段标注，不进优质标的。
现成实现：`templates/bsc-alpha-scorer.py`（trending raw → TOP5 + A/B/C/D + 11项 + 排序，直接跑）。

## 新增叙事簇型：日韩卡通角色梗簇（2026-10-15 早场实测）

载体是**日韩动漫/卡通角色 IP**（非加密 KOL、非中文梗）——与中文动物梗线并列，但受众是日韩圈。已确认成员：
- **ハッチャン / Hatchan**（One Piece 八爪鱼角色，JP）——同窗 **2 个地址**（`…ae8a7777` $18.6K / `…9c877777` $100.2K），tw+web **双 `/status/` 推广推文伪装**（Zeeko__Dev/status）、6h +390%/+2683% 后 **1h -58%/-47%**
- **루피 / 잠망루피 / Loopy**（韩国 Zanmang Loopy 卡通，KR）——루피 web=xcoinsol.lol（Sol 系站）+ tw 是 `search?q=<CA>` 占位；잠망루피 web=tiktok.com/@zanmangloopyofficial（真实 TikTok 主页）；6h -70.6% / -76.5%
- **윤 / Yoon**（KR）——tw=`i/status/…` 推广推文伪装
- 识别法：token info `name` 用日文片假名/韩文，或 web/tw 直链动漫角色官方 TikTok/X
- 簇内行为：同日批量出现但**集体崩盘**（1h -33%~-58%）= 拉高出货、无主盘跑出（参 SKILL.md「簇内轮动」变体）

## 2026-10-15 早场（05:50 BJT）运行记录

- **TVL**：BSC **$5,336M**（7d **-5.6%**；24h 失真）——较 10-14 $5,408M/-6.7% 继续失血，主线「存量博弈」延续
- **TOP5（6h by volume）**：NVDAB $8.33M / pPOLY $6.48M / QQQB $6.03M / AAPLB $3.17M / BNCB $1.99M——**连续第三次 100% 合成/证券盘**
- **本场无准推级（全场最高 62）**，双门槛达标仅 **2 条**（合成盘已剔除）：
  - **宇树科技 62**（A24 B20 C6.5 D6 E5；MC $670K，rug 0/bundle 0/top10 18.9%，11项 **8/11**；flap_stocks，web=东方财富 688836 = 国产机器人 IPO 叙事）
  - **牛来 60**（A25 B12 C12 D4 E7；MC $68.75M，top10 **83.2%** 极端控盘 + dev 开 27 盘，11项 8/11，62 天老盘 CTO）
  - 一行观察名单：旺柴 59（6h **-31.5%** 动量崩 D0）/ BIBI 58 / SAFU 58 / GM 56 / BREW 56 / 루피 56 / 萌兰 55（dev 开 **118** 盘 = 职业盘极端样本）
- **新币段**：严格标准无合格新币（trenches 三栏全空 `{"completed":[],"near_completion":[],"new_creation":[]}`；1D 内新盘全 <$1M，最接近 萌兰 $115K）
- **核心叙事 4 条**：①合成/证券盘霸榜（TOP5 100%）②**日韩卡通角色梗簇集体崩盘**（ハッチャン/루피/잠망루피/윤）③中文动物梗线（旺柴/BS/萌兰/眉眉/猫头鹰/蟾蜍）④币安·CZ 梗簇延续缩量（SAFU/GM/BIBI/币安理论/中国人能飞 bundle 25.3%）
- **退潮预警**：루피 -70.6% / 4HOOK -72.5% / 잠망루피 -76.5% / ハッチャン 1h -57.9% / 眉眉 1h -32.4% / 윤 1h -33.2%——全为拉高后 1h 放量腰斩
- **抓取零失败**：15 条候选 token info 批量抓（顺序 for + retry-once + 代理前缀 + JOB 前缀）OK=15 FAIL=0，本场未触发 429
- ⚠️ **报告排版教训**：CA 行里发现笔误时不要「行内注：以完整地址为准 → 重贴」这种自我修正写法——直接在上面把 CA 写对即可，二次纠错行会被读者当成第二个代币

## 新增叙事簇型：flap「飞行的特斯拉」簇 + 超长慢毕业（2026-10-16 午场实测）

- 载体：Musk「飞行的特斯拉跑车」梗（Roadster 随 Falcon Heavy 送上太空）。**flap 平台批量发同主题**——同窗 5+ 盘：特斯拉能飞（**3 个同名地址** `0x610a…`/`0xf764…`/`0xec2a…`）+ 拉飞(Flying Tesla Roadster `0xd5cd…`) + ROADSTER + 特斯拉飞行汽车(trenches 小盘)
- 识别法同「平台级原生簇」：flap 反复批量发主题币（硬件簇/股票簇/太空簇之后的又一主题），簇内选数据最干净者做承接位观察
- ⚠️ **超长慢毕业**：主盘 特斯拉能飞 created **08-14**、open **10-16 09:28**（gap ≈ **2 个月**！）——慢毕业 gap 已从数小时/数天扩到**月级**，trending 的 `creation_timestamp` 记的是 open 时间（08-14→实际是 10-16 09:28），6h +18629% 是开盘首日假象。新盘核验**必读 token info 的 `creation_timestamp` 与 `open_timestamp` 两字段并算 gap**
- 该盘开盘首日数据：MC $960K（差一线未站稳 $1M）、SM62/KOL27、rug0/bundle 11.3%/top10 13.9% 全绿，但 1h 已 -15.9% 回落

## 2026-10-16 午场（13:41 BJT）运行记录

- **TVL**：BSC **$5,337M**（24h +0.3% | 7d **-3.2%**）——失血放缓但仍净流出；主线「存量博弈」延续
- **TOP5（6h by volume）**：pPOLY $42.65M / STBL $16.36M / NVDAB $12.18M / QQQB $11.16M / AAPLB $7.73M——**连续第 5 次 100% 合成/证券/项目盘**（真实 meme 未进前五）。⚠️ 其中 **STBL**（name「STBL_Token - STBL Governance Token」，open=0，LP $1.65M / holders 1.5万）= **治理代币非 meme**，与合成盘同族，同样照列 TOP5 但剔除出优质标的/新币段
- **本场无准推级（全场最高 65）**，双门槛达标 2 条：
  - **特斯拉能飞 65**（A24 B20 C7 D8 E6；flap 慢毕业首发，11项 **8/11**，见上节）
  - **萌兰 61.5**（A24 B20 C2.5 D10 E5；熊猫 IP 匿名盘，MC $38K 极微盘，SM107 但 hiMC $528K→$38K 回撤 93%，11项 7/11）
  - 一行观察名单（55-59）：逆蝶 59.5（rug0/bundle0/top10 17.6% 数据最干净，5m 转跌）/ 牛来 59 / 拉飞 58.5 / BIBI 58.5 / STBL 58.5
- **新币段**：严格标准**仅 1 个合格新盘 TapeFour**（tapeout 平台，created 10-15 16:01 ≈21.7h，MC $1.40M，hiMC $12.38M → 自高点 **-89%**，1h -20.4% 派发中）。trenches `new_creation --min-marketcap 1000000` 返回空；`--filter-preset smart-money` 返回 60 条但 `usd_market_cap` 全 $0 / liq $0 **不可评估**（BSC trenches 老毛病，别照单收录）
- 🚩 **预警**：① **牛来 `entrapment_ratio` 0.947**（94.7% 诱多/陷阱交易）+ top10 84.1% = 极端控盘派发，量萎缩至 $212K；② **루피(Loopy) 6h -18.7% / 1h -23.8% 崩盘**——10-16 早场唯一双门槛达标（62/75），午场已蒸发（又一例「早场准推→午场崩」）
- **`entrapment_ratio` 判卖压用法确认**：trending raw 直接含 `entrapment_ratio` + `buys`/`sells`，**零额外请求**即可定向——>0.5 派发特征（牛来 94.7% / STBL 79.4% / BIBI 55.3%）、0.2-0.5 存疑、<0.2 相对干净（特斯拉能飞 17.4% / 拉飞 12.1%）；配 6h 跌幅构成 🚩 预警完整证据链
