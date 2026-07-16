# DashScope (阿里云百炼) API 配置

## 识别特征

| 特征 | 值 |
|------|-----|
| API Key前缀 | `sk-ws-` (workspace-level key) |
| 默认Endpoint | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 兼容协议 | OpenAI 兼容 (可以直接替换OpenAI URL) |
| 余额查询 | `https://dashscope.aliyuncs.com/api/v1/balance` (HTTP 404 可能) |

## 可用模型

DashScope 拥有**225+模型**，包括：

| 模型 | 用途 | ¥/1M输入 | ¥/1M输出 |
|------|------|---------|---------|
| `qwen-turbo` | 日常对话/性价比最高 | 0.3 | 0.6 |
| `qwen-plus` | 增强版 | 0.8 | 2.0 |
| `qwen-max` | 旗舰版 | 2.0 | 6.0 |
| `qwen3-30b-a3b` | Qwen3轻量MoE | 0.3 | 0.6 |
| `qwen3-235b-a22b` | Qwen3旗舰MoE | 1.5 | 3.0 |
| `qwen3-coder-plus` | 代码 | 1.0 | 3.0 |
| `qwq-plus` | 推理模型 | 2.0 | 6.0 |
| `deepseek-v4-flash` | DeepSeek V4 | — | — |
| `kimi/kimi-k2.5` | Moonshot Kimi | — | — |

## 测试key是否有效

```bash
curl -s https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer sk-ws-..." \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

## 配到Hermes config.yaml

```yaml
# 在config.yaml的providers段添加
providers:
  - name: dashscope
    api_base: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: sk-ws-...   # 从阿里云百炼控制台获取
    models:
      - qwen-turbo
      - qwen-plus
      - qwen3-30b-a3b
```

## 注意事项

- **sk-ws- 前缀 ≠ OpenRouter** — 之前误认为OpenRouter key，实际是阿里云百炼
- **10元充值非常实惠** — Qwen-Turbo ¥0.3/M输入，10元≈3000万tokens
- **可同时访问DeepSeek** — DashScope也提供DeepSeek模型的代理调用（deepseek-v3, deepseek-v4-flash等）
- **阿里云百炼控制台**: https://bailian.console.aliyun.com/
