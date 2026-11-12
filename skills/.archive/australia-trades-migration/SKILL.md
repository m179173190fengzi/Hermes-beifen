---
name: australia-trades-migration
description: "澳洲/新西兰技工移民研究 — TRA职业评估程序选择(MSA/OSAP/TSS)、签证路径(482-SID/189/190/186/462)、材料清单与费用。用户目标NZ/AU干工地(木工方向)。触发词: 澳洲打工、移民条件、职业评估、TRA、木工签证、雇主担保、技能评估、澳大利亚工作。也含官网被墙时用Wayback抓取的检索技法(可复用于任何被墙的gov.au站点)。"
---

# 澳洲/新西兰技工移民研究 (Trades Migration)

## 何时使用
- 用户问澳洲/新西兰打工、移民、签证条件、职业评估(TRA)、雇主担保、技术移民打分
- 用户长期目标: NZ/AU干工地(木工/建筑技工)，已在自学construction英语
- 需要查询澳洲政府官网(immi/tradesrecognitionaustralia)但站点被墙/超时

## 核心结论速查 (2026-08 经Wayback核实)
- 木工 Carpenter [331212] 在 CSOL 上，澳洲全境紧缺，时薪 $35-55 AUD，年收 $85K-110K
- **中国护照+木工 → 走 OSAP 评估，不是 MSA** (TRA国别-职业矩阵决定)
- 482/SID雇主担保 → 走 TSS Skills Assessment 程序
- Carpenter 属 **non-licensed trade** (TRA分类里licensed只指Electrician两类) → 有正式培训=3年经验，无=5年
- OSAP/TSS 通过后 non-licensed 职业直接发 **Certificate III in Carpentry** (澳洲VET学历) — 等于省掉TAFE学费
- 评估总费用约 **$3,120 AUD** (文件$1,120 + 技术面试$2,000)，签证卡支付不退费

## 签证路径对比
- **SID 482** (2024-12起替代旧482): 雇主担保，年薪≥$73,150，雅思5.0(单项≥5)，干满2年→186转PR；PR需<45岁
- **189/190/491**: 打分制65+，雅思4个6，年龄<45，需TRA评估；木工190州担保最实际(WA/SA/QLD/NT缺)
- **186 DE**: 雇主担保直申PR，雅思4个6
- **462 WHV**: 18-30岁抽签(中国5000名额/年)，需大学学历；2024起可同雇主干12个月(建筑行业)，仅试水不能转PR
- **留学路径**: TAFE Cert III Carpentry 1.5-2年($15K-30K/年)→485→482/186，总成本50-100万RMB

## TRA 评估程序选择 (先查矩阵再定)
1. 查 `osap-nominated-occupations-countries-and-sars` 页面: 职业+护照国组合 → 决定 MSA or OSAP
2. MSA ($795): 文件评估，永久技术移民用；**中国护照木工不适用**
3. OSAP: 海外技工评估 = 文件评估 + 技术面试(全英文无翻译)；中国木工走这个
4. TSS: 482/SID 签证专用评估，费用结构同OSAP
5. SAOM: 电工试点补贴项目，免费

## 材料清单 (OSAP/TSS通用)
- 护照身份页 (彩色扫描≥150dpi，PDF≤10MB)
- 学历/学徒证书 + 完整成绩单(含起止日期、课程明细)
- 每段工作经历一张 **Employer Template** (雇佣期/工时/岗位/详细职责/公司抬头纸/签字人联系方式)
- 工资证据: 每年至少2种 (政府税单/3张工资单/社保记录/银行流水显示雇主名+工资入账)
- 自雇: 营业执照、年检、客户发票、银行流水、会计师证明
- 非英文材料: 境内NAATI认证翻译；境外官方认证翻译+盖章
- 必须decision-ready，缺料直接拒且不退费

## 流程与时限
文件评估(材料审核) → 技术面试(技师面试，可在线: 笔记本/台式+10Mbps，**不允许翻译**) → 结果信
- TSS/OSAP 全程约 **9周**；MSA 120天
- 失败: 28天内可申诉($700)，12个月内可重评一次($450-1,000)
- 经验要求: 申请前3年内必须有12个月全职相关经验；兼职按比例折算

## 检索技法: 官网被墙时用 Wayback (重要)
TRA官网直连/代理都超时，搜索引擎(DDG/Bing/Google)结果全污染。有效路径:
1. 走代理访问 web.archive.org (本机代理 127.0.0.1:7890)
2. CDX API 枚举存档URL: `web.archive.org/cdx/search/cdx?url=域名*&output=json&collapse=urlkey&filter=statuscode:200`
3. 抓原始文件必须加 `id_` 后缀: `web.archive.org/web/{timestamp}id_/{原始URL}`
4. PDF用 pdftotext -layout 提取
完整代码模式见 references/wayback-gov-site-research.md

## Pitfalls
- **别默认MSA** — 国别+职业矩阵决定程序，中国护照木工是OSAP
- Carpenter是non-licensed → 3年经验(有培训)不是4年；别照搬licensed标准
- 国内职业技能等级证书算"正式培训"但必须TRA可验证(发证机构能出电子验证)
- 2024-12起482被SID取代，但TSS评估程序仍存在 — 别给过时框架
- Wayback部分PDF存档404 → 从CDX列表换时间戳/版本号重试
- 技术面试全英文，不能带翻译；在线需电脑+稳定10Mbps

## 支持文件
- references/tra-skills-assessment.md — 费用表+材料清单+流程+来源URL存档时间戳
- references/wayback-gov-site-research.md — 被墙gov.au站点的Wayback抓取代码模式
