# Super Hermes 元推理层 — 让结构化prompt反思自身盲区

安装：`bash ~/super-hermes/install.sh`
已装技能：`prism-scan` `prism-full` `prism-3way` `prism-discover` `prism-reflect`
已装prism（7个）：`error_resilience.md` `l12.md` `optimize.md` `identity.md` `deep_scan.md` `claim.md` `simulation.md`

## 和trading-prompt-optimizer的关系

两个工具的作用互补：

| 阶段 | 工具 | 产出 |
|:----|:----|:-----|
| **优化** | trading-prompt-optimizer | 结构化prompt（Role/Workflow/Risk/Output） |
| **反思** | Super Hermes prism | 指出这个prompt漏了什么、哪里可能失效 |
| **迭代** | 两者结合 | 根据反思优化 → 再反思 → 再优化 |

## 最佳实践：先优化再反思

1. 先用 `trading-prompt-optimizer` 把prompt结构化
2. 再用 `/prism-reflect` 让结构化的prompt自我反思盲区
3. 根据反思结果回到步骤1迭代

## 使用示例

```
优化后prompt → 加载 prism-full
                ↓
Super Hermes输出:
  "这份分析最大化了【结构深度】。
   它没有检查【时态退化】或【安全面】。
   那些方面建议: /prism-reflect"
```

## Prism文件位置

7个proven prism文件在 `~/.hermes/prisms/`，可以当system prompt用。
