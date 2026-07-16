# Prompt-Optimizer 上游架构参考

> 来源：https://github.com/linshenkx/prompt-optimizer (32K ⭐)
> 调研时间：2026-07-14

## 工程架构

Monorepo 6包：

| 包 | 技术栈 | 功能 |
|---|--------|------|
| `core/` | TypeScript | 核心逻辑：模板引擎、LLM适配器、评估服务 |
| `ui/` | Vue组件库 | 共享UI组件 |
| `web/` | Vite + Vue | Web应用 (prompt.always200.com) |
| `desktop/` | Electron | 桌面版（无CORS，可连本地Ollama） |
| `extension/` | Chrome Extension | 浏览器扩展 |
| `mcp-server/` | MCP协议 | 对外暴露3个工具：optimize-user-prompt, optimize-system-prompt, iterate-prompt |

## 核心设计模式

### 模板引擎 (TemplateProcessor)

- Mustache-like `{{variable_name}}` 占位符语法
- 模板指令：**保留占位符不替换成具体值** — 关键约束
- 输出不带引导词、不用代码块包裹

### 5种优化模板

| 模板 | 用途 |
|------|------|
| `general-optimize` | 通用 → 按 Role/Profile/Skills/Rules/Workflows 重组 |
| `analytical-optimize` | 深度分析原意 → 含 Background/Attention/Suggestions |
| `output-format-optimize` | 仅优化输出格式 |
| `soul-hermes-compose` | 特定风格组合 |

### 评估驱动重写 (Evaluation-Driven Rewriting)

```
优化 → 评估 → 不通过 → 重写 → 再评估 → ...
```

- 单结果评估 + 多结果对比评估
- 可配置评估维度（完整性/可执行性/一致性等）
- 自动根据评估结果触发重写

### 高级测试模式

1. **变量管理**：自定义变量 + 批量替换 + 实时预览
2. **多轮对话测试**：模拟对话流程
3. **Function Calling 测试**：验证工具调用格式
4. **上下文变量替换策略**：不同替换行为

## 与交易优化的适配映射

| prompt-optimizer 特性 | 交易场景适配 |
|------------------------|-------------|
| 模板引擎 + 占位符 | 策略模板保留 `{{chain}}` `{{interval}}` 参数 |
| 评估驱动重写 | 对比优化前后cron输出质量，迭代改进 |
| 多模式测试 | 回测环境用不同市场数据验证prompt一致性 |
| MCP Server | 可集成到Hermes MCP流水线中自动优化交易prompt |

## 安全架构

纯前端设计，API key不经中间服务器。Docker部署可通过环境变量预设key。

## 部署选项

| 方式 | 命令/链接 |
|------|----------|
| 在线版 | prompt.always200.com |
| Docker | `docker run -d -p 8081:80 linshen/prompt-optimizer` |
| Vercel | 一键部署 |
| Cloudflare | Workers + Pages |
| 桌面版 | Electron（推荐，无CORS限制） |
| Chrome扩展 | Chrome Web Store |
