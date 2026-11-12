代理127.0.0.1:7890: 外部网络命令(尤其gmgn-cli)必须带HTTPS_PROXY否则ECONNREFUSED; apt需-o Acquire::http::Proxy; node CLI(如baw)另需NODE_USE_ENV_PROXY=1。Ubuntu26.04 Wayland。GitHub m179173190fengzi。GMGN用Ed25519 key。
§
V4=B哥双均线密集→发散(6均线不变):密集(价差<3%)→突破确认→回踩MA20加仓,只跑4H。回踩占89%需趋势过滤;止损别太紧。仅日线及以下。脚本~/v4-strategy.py,文档~/v4-model-rules.txt(已含利弗莫尔20/20/20/40阶梯:满仓止损≈均价=保本)。靠回测验证不看理论。
§
链上打狗:6类过滤器(链创始人/KOL/政治/科技/社会/机构);风控-20%止损,meme绝不补仓;好叙事+大车头拿住不横跳。交易纪律skill=beidou-meme-hunter;复盘闭环trade_log.py。
§
@AIBullss: 策略靠市场假设不靠AI;EMA交叉=趋势市,RSI=震荡市;回测含佣金滑点;Walk-Forward 70/30(WFE>0.5才实盘);实盘前纸面模拟≥100笔。
§
链上日报cron fa0df7d27b24(5:40)+b4468ed62c8e(19:00)+均线告警55b9e5c9ad9f 均已暂停(用户说'全都错误/取消',勿自动恢复,要开等他说)。daily_scan.py已含robinhood三链。
§
Telegram: 用户ID 7706985861(CryptoFengzi)=ALLOWED_USERS/HOME_CHANNEL。
§
Hermes 已升 git v0.23.0(源码装~/.hermes/hermes-agent,venv py3.11;pipx 0.19.0保留可回滚,config已迁v52);升级只能官方installer(见部署技能)。网关重启只能用户/restart(内部与cron均被#30719拦)。TG适配器会'假活':进程active但polling已死→心跳cron 0247728744f2(5min静默)。
§
用户偏好: token成本敏感(嫌贵直接叫停)→LLM cron绝不挂重skill(gmgn-onchain-analysis 136KB≈4万tokens/次),一律脚本预消化(raw JSON不进上下文),能no_agent就no_agent;换版本留备份(暂停+prompt存档)不直删;拒装第三方面板/自进化插件(费钱+暴露终端)。
§
GMGN的fomo标签=用过该平台,非聪明钱。脚本:bsc_hard_filter(+449聪明钱)/daily_scan/trade_log/price_watch/binance_tge_analyze;X、BSC候选、TGE监控cron已停。
§
行为偏好:给新工具/权限前先风险清单+隐私实测再动手。审批常超时被拦(chat说'同意'不算);复杂/多段/`python3 -c`易被拦→写脚本文件再跑,批量改cron prompt也走脚本。会转发加密营销贴,要求先查真实数字再评价;转发交易心法则要求'学会它'=落成规则文档/脚本/标签。
§
Cookie提取(Chrome→~/.venvs/xmon+browser_cookie3):X=x_cookie_extract.py,fomo=fomo_cookie_extract.py。fomo API=prod-api.fomo.family,Bearer用privy-token(JWT轮换→401)。小黄人=Unipcs(钱包2heJbC32Tpfcb3nbUb5ER61K11FGZVfVGtVnDm6LDogF)。
§
⚠️备份仓库 m179173190fengzi/Hermes-beifen 曾公开且带明文密钥(需轮换+转私有), 已改为只导出key名。真实记忆目录 ~/.hermes/memories/(memory/ 是旧目录)。
§
盯盘规矩:只发CA=体检;明说'盯'才监控。TGE/Alpha不自动监控(费钱),他刷X看到发链接才分析(手动跑binance_tge_analyze.py)。
§
wawa中转已废(403 GROUP_DELETED);辅助模型compression/web_extract/approval全切deepseek,DeepSeek无视觉。
§
币安Agentic Wallet(baw)已登录: EVM 0xf78B3011b90b3c0EE6aa77f8692F9afb167C7c7E(RH链4663), SOL Hc9Zum8N55AFfsjWRBdqd34sn1u1pvgkU7QUAYBSPApA; 日限额$50K待App改小,单链无跨链桥,gas需BNB; 用户玩Farming Season(RH链链游,无中文UI)。
§
发CA必附叙事解读(什么梗/谁在做/机制/为何现在热)→结构→位置→结论;缺叙事=不合格。围猎>25%标红不给入场。
§
x