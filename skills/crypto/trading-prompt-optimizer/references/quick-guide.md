# 交易提示词优化器 — 快速使用指南

借鉴 prompt-optimizer 的4个核心步骤：

## 1. 首次优化（对应 prompt-optimizer 的 general-optimize）

当你有新的交易prompt需要结构化时：

1. 加载 `trading-prompt-optimizer` 技能
2. 把你的prompt贴在user消息中
3. 我会自动输出结构化版本（Role → Profile → Analysis Framework → Risk Rules → Workflow → Output Format）

## 2. 深度分析（对应 prompt-optimizer 的 analytical-optimize）

如果当前prompt比较复杂（多流程+多条件判断）：

1. 加载 `trading-prompt-optimizer` 技能
2. 说"深度分析这个prompt"
3. 我会额外输出：Background分析、缺失功能诊断、改进建议

## 3. 迭代改进（对应 prompt-optimizer 的 iterate）

如果已有优化过的prompt，需要针对特定方向改进：

1. 加载 `trading-prompt-optimizer` 技能
2. 说"迭代这个prompt：[具体需求]"
3. 我会在保留原有核心逻辑和占位符的前提下，只做针对性修改

## 4. 评估对比（对应 prompt-optimizer 的 evaluation）

想对比优化前后的差异：

1. 加载 `trading-prompt-optimizer` 技能
2. 说"对比评估这个prompt的优化效果"
3. 我会分析两者在清晰度/完整性/可执行性/风控覆盖上的差异

---

## 常见场景

| 场景 | prompt类型 | 优化重点 |
|------|-----------|---------|
| 链上代币扫描 | 类型B | 6类过滤器硬性条件、评分表、静默模式 |
| V4策略信号 | 类型A | 6均线系统结构化、看大做小流程、熊市做空约束 |
| 推特KOL监控 | 类型C | 搜索策略、来源分级、噪音过滤规则 |
| 市场日报/周报 | 类型A | 输出格式固定化、数据面板设计 |
| 单个代币分析 | 类型B | 分析框架标准化、安全评估流程 |

---

## 查看完整案例

详细实战案例（链上打狗扫描prompt前后对比）：
```
skill_view name=trading-prompt-optimizer file_path=references/optimization-case-study.md
```
