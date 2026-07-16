# Trading Prompt Optimizer — Pitfalls & 使用贴士

## Twitter搜索注意事项
- `twitter search "from:用户名"` 在访客模式下不可靠，可能返回空
- 降级方案：`twitter search "用户名 crypto" -n 5` 或 `twitter search "用户名" -n 5`
- 管道命令被安全系统拦截时：`twitter search "xxx" 2>/dev/null | head -40` 直接看原始JSON
- 避免 `| python3 -c` 管道模式，改为写入 `.py` 文件再执行

## Cron合并要点
- 同一时间跑多个cron → 合并为一条Alpha合成简报（参考 daily-alpha-synthesis.md）
- 合并后prompt必须自包含，不加载任何skill（防上下文溢出）
- 每个分析阶段独立成section，LLM按顺序执行不易漏

## 人物Skill蒸馏（女娲18n）
- 安装女娲后，自带的15个蒸馏人物在 `~/.hermes/skills/` 下
- 安装时注意 `huashu-nuwa/examples/` 内的重复副本会导致名称冲突，需删除
- 自己蒸馏可用 `skill_view name=huashu-nuwa` 加载后直接说"蒸馏@用户名"
- 币圈KOL蒸馏重点：交易模式(入场/止盈/止损) + 叙事判断 + 社区影响力