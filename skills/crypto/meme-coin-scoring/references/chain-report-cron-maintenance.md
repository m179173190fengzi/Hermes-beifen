# 链上合成日报 cron（fa0df7d27b24）维护手册

## Job 概况

- **id**: `fa0df7d27b24`，名称「链上合成报告」
- **调度**: `0 6,11,19,22 * * *`（固定时刻，用户偏好，不是 interval）
- **投递**: `origin` → Telegram 7706985861（CryptoFengzi）
- **关联 skills**: gmgn-onchain-analysis, gmgn-market, gmgn-token, okx-dex-signal, okx-dex-token, okx-dex-trenches
- **定义文件**: `~/.hermes/cron/jobs.json`（所有 job 都在这一个 JSON 里）

## 报告结构（2026-08-01 版）

```
━━━ 📡 每日Alpha合成简报 ━━━
━━━ 💰 三链TVL ━━━
━━━ 💥 三链成交量TOP5 ━━━      ← 2026-08-01 新增
━━━ 🔥 链上优质标的 ━━━
━━━ 🆕 新币监控（1D内 MC稳定≥$1M）━━━
━━━ 🧠 交叉验证 & Alpha ━━━
```

## ⚠️ 修改 cron prompt 的正确姿势（踩过坑）

`cronjob action=update` 需要**完整的新 prompt**，而 `cronjob list` / `update` 返回的 `prompt_preview` 是**截断**的。直接把截断的 preview 传回去会丢内容。

正确流程：
1. 读 `~/.hermes/cron/jobs.json`（用 execute_code + json.load，或 read_file 但注意大文件截断）
2. 取出目标 job 的完整 `prompt` 字段
3. 在完整文本上做增量修改（patch/新增段落）
4. `cronjob action=update job_id=fa0df7d27b24 prompt=<完整新prompt>`

```python
import json
with open('/home/wei/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for job in data['jobs']:
    if job['id'] == 'fa0df7d27b24':
        print(job['prompt'])
```

## 三链成交量TOP5 板块实现

数据源：`gmgn-cli market trending --chain <sol|bsc|robinhood> --interval 6h --limit 30 --raw`。

关键：trending 的 rank 项里有 `volume` 字段 = **该 interval 的美元成交额**（非代币数量），直接按它降序排序取前5即可。不需要 `--order-by volume`（prompt 里让 agent 自己用 python 排序，raw JSON 更灵活）。

- 每链 top5，三链共 15 条
- 展示格式：`排名 | ${SYMBOL} | MC $X | LP $X | 6h ±X% | 量 $X`
- 链数据缺失 → 标注"数据缺失"，不硬编
- 格式化成 $X.XM / $XXXK（volume 单位是美元）

```bash
HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 gmgn-cli market trending --chain sol --interval 6h --limit 30 --raw
```

## 其他注意事项

- **网络命令必须带代理前缀** `HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890`（本机所有外部 API 都走 FLClash 代理，否则 ECONNREFUSED）
- prompt 里已内置网络要求章节，改 prompt 时别删
- 输出约束：**纯文本 Markdown 直发 TG**，绝不生成 HTML 文件 / MEDIA 附件（用户只看 TG 纯文本）
- 三链都无 ≥70 分 + 无热点 → 回复 `[SILENT]` 不推送
