# Hermes API Server 端点参考

API Server 运行在 `http://<电脑IP>:8642`，默认端口 8642。

## 启用方式

```bash
hermes config set gateway.api_server.enabled true
hermes config set gateway.api_server.port 8642
hermes gateway restart
```

## 核心端点

### 1. 对话（OpenAI Chat Completions 格式）

```
POST http://<host>:8642/v1/chat/completions
```

请求体：
```json
{
  "model": "hermes-agent",
  "messages": [
    {"role": "user", "content": "你好"}
  ]
}
```

响应：
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1712345678,
  "model": "hermes-agent",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！有什么可以帮你的？"
      }
    }
  ]
}
```

### 2. 流式对话

```
POST http://<host>:8642/api/sessions/{session_id}/chat/stream
```

### 3. Runs API（异步任务）

| 端点 | 方法 | 说明 |
|:----|:----:|:-----|
| `/v1/runs` | POST | 启动一个 run，返回 run_id |
| `/v1/runs/{id}` | GET | 查询 run 状态 |
| `/v1/runs/{id}/events` | GET | SSE 事件流 |
| `/v1/runs/{id}/approval` | POST | 审批待处理的 run |
| `/v1/runs/{id}/stop` | POST | 中断 run |

### 4. Sessions API

| 端点 | 方法 | 说明 |
|:----|:----:|:-----|
| `/api/sessions` | GET | 列出会话 |
| `/api/sessions` | POST | 创建会话 |
| `/api/sessions/{id}` | GET | 查看会话 |
| `/api/sessions/{id}` | DELETE | 删除会话 |
| `/api/sessions/{id}/messages` | GET | 查看消息历史 |
| `/api/sessions/{id}/fork` | POST | 分叉会话 |

### 5. 其他

| 端点 | 方法 | 说明 |
|:----|:----:|:-----|
| `/v1/models` | GET | 列出可用模型 |
| `/v1/capabilities` | GET | 获取API能力信息 |

## ESP32 集成注意事项

- ESP32 的 HTTPClient 库可以直接调用 `/v1/chat/completions`
- 使用 WiFiClientSecure 时需要信任自签名证书（开发环境可跳过验证）
- 建议使用 JSON 解析库（如 ArduinoJson）解析响应
- 每次对话请求约 1-3KB 数据量，WiFi 传输延迟 ~50-200ms
- 如果 ESP32 和 Hermes 在同一局域网，直接用内网 IP 连接
