# OpenCode CLI

## 描述
开源的命令行编码代理工具，提供与 Claude Code / Codex 类似的 AI 委托编码体验。支持多种 LLM 后端，可自托管。

## 用途
- 无需闭源服务的 AI 辅助编码
- 本地化、隐私安全的代码委托
- 自定义模型和工作流集成

## 使用示例
```bash
# 启动交互式编码会话
opencode

# 指定任务
opencode "重构这个模块，提取公共接口"

# 使用自定义模型
opencode --model llama-3 --provider ollama "分析代码质量"
```
