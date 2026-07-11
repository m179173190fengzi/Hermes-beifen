---
name: esp32-voice-assistant
description: "ESP32 语音助手 — 通过 Hermes API Server 实现语音对话"
version: 1.2.0
author: Hermes Agent
tags: [esp32, hardware, voice, assistant, iot]
---

# ESP32 语音助手

将 ESP32 开发板变成 Hermes 的语音终端。按住说话 → 语音识别 → 发给 Hermes → 收到回复 → 喇叭播放。

## 两种通信方案

### 方案① 走 Telegram 桥接（最简单，推荐首次尝试）

```
ESP32 ──WiFi──→ Telegram Bot API ──→ Hermes Gateway ──→ 回复 → ESP32 轮询
```

- 不需要配置 API Server，复用你已有的 Telegram 通道
- ESP32 直接调 Telegram API 发消息/收消息
- 延迟 1-3 秒

### 方案② WebSocket/HTTP 直连（低延迟）

```
ESP32 ──WiFi──→ 你的电脑 :8642（Hermes API Server）
```

- 延迟 ~500ms
- 需要电脑开启 API Server 并局域网内可访问

## 电脑端配置（方案②）

```bash
# 启用 API Server
hermes config set gateway.api_server.enabled true
hermes config set gateway.api_server.port 8642

# 允许局域网访问
# 找到你电脑的局域网 IP（如 192.168.1.100）
# ESP32 用这个 IP 连接

# 重启 gateway
hermes gateway restart
```

## Hermes API Server 端点

API Server 运行在 `http://<电脑IP>:8642`，提供 OpenAI 兼容接口：

### 对话（最常用）

```
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "hermes-agent",
  "messages": [
    {"role": "user", "content": "语音转的文字"}
  ]
}
```

返回标准 OpenAI 格式：
```json
{
  "id": "chatcmpl-xxx",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "回复内容"
    }
  }]
}
```

### 流式对话（更低延迟）

```
POST /api/sessions/{session_id}/chat/stream
Content-Type: application/json

{"message": "语音转的文字"}
```

## ESP32 工作流程

```
┌─────────────────────────────────────────────────┐
│  1. 等待按钮按下                                   │
│  2. 开始录音（INMP441 I2S 麦克风）                   │
│  3. 按钮松开 → 停止录音                              │
│  4. 音频→文字（STT）                                 │
│     ├── 方案A: 本地 Edge TTS API（传录音文件）        │
│     └── 方案B: 用语音识别云服务（百度/阿里/讯飞）      │
│  5. HTTP POST 到 Hermes API / Telegram API          │
│  6. 收到回复文字                                     │
│  7. 文字→语音（TTS）                                  │
│     ├── 方案A: Edge TTS API（在线）                  │
│     └── 方案B: ESP32 本地 TTS（音质差）              │
│  8. MAX98357 喇叭播放                                  │
│  9. 回到 1                                          │
└─────────────────────────────────────────────────┘
```

## 硬件接线

### INMP441 I2S 麦克风

```
INMP441      ESP32-S3
───────      ────────
  LRC  →     GPIO4
  DOUT →     GPIO5
  BCLK →     GPIO6
  VDD  →     3.3V
  GND  →     GND
```

### MAX98357 I2S 音频放大 + 喇叭

```
MAX98357     ESP32-S3
────────     ────────
  BCLK →     GPIO10
  LRC  →     GPIO11
  DIN  →     GPIO12
  VIN  →     5V
  GND  →     GND
  OUT+ → 喇叭正极
  OUT- → 喇叭负极
```

### 按钮（按住说话）

```
按钮         ESP32-S3
────         ────────
  一端 →     GPIO0（内建上拉）
  另一端 →   GND
```

## 硬件清单

| 配件 | 型号 | 价格 |
|:----|:-----|:----:|
| 主控 | ESP32-S3-DevKitC | ¥35-50 |
| 麦克风 | INMP441 (I2S MEMS) | ¥5-10 |
| 音频放大 | MAX98357 + 小喇叭 3W | ¥15-20 |
| 按钮 | 轻触开关 (按住说话) | ¥2 |
| 连接线 | 杜邦线母对母 x10 | ¥3 |
| 电池 (可选) | 18650 + 充电模块 | ¥15 |
| **总计** | | **¥50-80** |

## 开发环境设置（推荐 PlatformIO）

```bash
# 安装 PlatformIO（推荐，比 Arduino IDE 更现代）
pipx install platformio

# 创建项目
mkdir esp32-hermes && cd esp32-hermes
cat > platformio.ini << 'EOF'
[env:esp32-s3-devkitc-1]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
monitor_speed = 115200
lib_deps =
    bblanchon/ArduinoJson @ ^7.0.0
EOF

# 编译
pio run

# 刷写（端口权限不够时加 sudo）
pio run --target upload
# 或手动：
sudo esptool --port /dev/ttyACM0 write-flash 0x0 .pio/build/esp32-s3-devkitc-1/firmware.bin

# 查看串口输出
pio device monitor
```

## 已知问题和注意事项

- **录音格式**：INMP441 输出 PCM 原始音频，需要通过 I2S 接口读取
- **WiFi 稳定性**：ESP32 WiFi 在密集信号环境可能断连，添加重连逻辑
- **STT 延迟**：本地 STT（如 Edge TTS 服务）延迟 ~1-2s，云服务更快但需要网络
- **电源**：MAX98357 需要 5V 输入，不能接 3.3V
- **音量**：喇叭不要太大功率，3W 足够桌面使用
- **API Server 配置后需重启 Gateway**：`hermes config set` 改完配置后必须 `hermes gateway restart` 才生效
- **Gemini API Key 配置**：vision 功能需要 GEMINI_API_KEY，但 .env 文件被 Hermes 安全保护，无法通过工具写入。需要用户手动编辑 `~/.hermes/.env`

## 故障排查

### ESP32 刷写后从 lsusb 消失（检测不到）
**现象**：刷写完成后，ESP32 从 `lsusb` 和 `/dev/ttyACM0` 消失。
**原因**：这不是固件问题。ESP32-S3 的 USB/JTAG 控制器是芯片内置硬件，不依赖 Flash 内容。
**排查步骤**：
1. 拔掉 USB 线，等 5 秒重新插回
2. 换一根 USB **数据线**（不是充电线）
3. 换一个 USB 口试试
4. 按住 BOOT 按钮再插 USB（强制进入下载模式）

### Gemini Key 测试
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=KEY" -H "Content-Type: application/json" -d '{"contents":[{"parts":[{"text":"hi"}]}]}'
```

## 编译踩坑（PlatformIO）

### 1. 函数顺序问题
PlatformIO 把 `.ino` 当 `.cpp` 编译，不会像 Arduino IDE 那样自动生成前向声明。
**必须**在 `loop()` / `setup()` 之前手动声明所有函数：
```cpp
// 前向声明
void playTone(int freq);
void playTTS(String text);
String sendToHermes(String message);
```

### 2. ArduinoJson 7.x API 变化
ArduinoJson v7 废弃了以下 API：
- ~~`StaticJsonDocument<N>`~~ → `JsonDocument`（动态分配）
- ~~`doc.createNestedArray("key")`~~ → `doc["key"].to<JsonArray>()`
- ~~`array.createNestedObject()`~~ → `array.add<JsonObject>()`

正确写法：
```cpp
JsonDocument doc;
doc["model"] = "hermes-agent";
JsonArray messages = doc["messages"].to<JsonArray>();
JsonObject msg = messages.add<JsonObject>();
msg["role"] = "user";
msg["content"] = message;
```

### 3. 串口权限
ESP32-S3 显示为 `/dev/ttyACM0`。需要用户属于 `dialout` 组：
```bash
sudo usermod -a -G dialout $USER
# 重新登录生效，或临时用 sudo 刷写
```

### 4. 直接 esptool 刷写（绕过 PIO upload）
```bash
sudo esptool --port /dev/ttyACM0 write-flash 0x0 /path/to/firmware.bin
```

## 相关文件

| 文件 | 说明 |
|:----|:------|
| `templates/esp32_sketch.ino` | Arduino 完整固件代码模板 |
| `references/api_endpoints.md` | Hermes API Server 端点文档 |
