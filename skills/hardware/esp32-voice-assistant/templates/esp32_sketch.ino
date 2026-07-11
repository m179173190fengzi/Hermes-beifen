/*
 * Hermes Voice Assistant — ESP32 固件模板
 *
 * 功能: 按住按钮说话 → 录音 → 发到 Hermes → 喇叭播放回复
 * 
 * 接线:
 *   INMP441:   LRC=GPIO4, DOUT=GPIO5, BCLK=GPIO6
 *   MAX98357:  BCLK=GPIO10, LRC=GPIO11, DIN=GPIO12
 *   按钮:      GPIO0 → GND（按住说话）
 *
 * 使用前需要修改:
 *   1. WIFI_SSID / WIFI_PASSWORD
 *   2. HERMES_HOST（电脑的局域网 IP）
 *
 * 编译注意（PlatformIO）:
 *   函数必须前向声明（本文件已包含），ArduinoJson 使用 7.x API
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "driver/i2s.h"

// ============ 用户配置 ============
// TODO: 改成你的 WiFi
const char* WIFI_SSID = "你的WiFi名称";
const char* WIFI_PASSWORD = "你的WiFi密码";

// TODO: 改成电脑的局域网 IP
const char* HERMES_HOST = "192.168.1.100";
const int HERMES_PORT = 8642;

// ============ 引脚定义 ============
#define BUTTON_PIN      GPIO_NUM_0
#define I2S_MIC_LRC     GPIO_NUM_4   // INMP441 LRCLK/WS
#define I2S_MIC_DOUT    GPIO_NUM_5   // INMP441 DATA
#define I2S_MIC_BCLK    GPIO_NUM_6   // INMP441 BCLK/SCK
#define I2S_SPK_BCLK    GPIO_NUM_10  // MAX98357 BCLK
#define I2S_SPK_LRC     GPIO_NUM_11  // MAX98357 LRC/WS
#define I2S_SPK_DIN     GPIO_NUM_12  // MAX98357 DATA

// ============ 录音参数 ============
#define SAMPLE_RATE     16000

// ============ 前向声明（PlatformIO 需要） ============
void playTone(int freq);
void playTTS(String text);
String sendToHermes(String message);

// ============ 状态 ============
bool isRecording = false;
bool buttonWasPressed = false;

// ============ 初始化 ============
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Hermes Voice Assistant ===");

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // 初始化 I2S 麦克风
  i2s_config_t i2s_mic_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false
  };
  i2s_pin_config_t i2s_mic_pins = {
    .bck_io_num = I2S_MIC_BCLK,
    .ws_io_num = I2S_MIC_LRC,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_MIC_DOUT
  };
  i2s_driver_install(I2S_NUM_0, &i2s_mic_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &i2s_mic_pins);

  // 初始化 I2S 喇叭
  i2s_config_t i2s_spk_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false
  };
  i2s_pin_config_t i2s_spk_pins = {
    .bck_io_num = I2S_SPK_BCLK,
    .ws_io_num = I2S_SPK_LRC,
    .data_out_num = I2S_SPK_DIN,
    .data_in_num = I2S_PIN_NO_CHANGE
  };
  i2s_driver_install(I2S_NUM_1, &i2s_spk_config, 0, NULL);
  i2s_set_pin(I2S_NUM_1, &i2s_spk_pins);

  Serial.println("Ready! Hold button to speak.");
}

// ============ 主循环 ============
void loop() {
  bool buttonPressed = (digitalRead(BUTTON_PIN) == LOW);

  // 检测按钮按下（开始录音）
  if (buttonPressed && !buttonWasPressed) {
    isRecording = true;
    Serial.println("🎤 Recording...");
    playTone(500);
  }

  // 检测按钮松开（结束录音 + 发送）
  if (!buttonPressed && buttonWasPressed && isRecording) {
    isRecording = false;
    Serial.println("⏹ Recording done. Sending...");
    playTone(1000);

    // TODO: 替换成 STT 结果
    String text = "测试消息";
    String reply = sendToHermes(text);
    Serial.print("Reply: ");
    Serial.println(reply);

    if (reply.length() > 0) {
      playTTS(reply);
    }
  }

  buttonWasPressed = buttonPressed;
  delay(50);
}

// ============ 发送到 Hermes API Server ============
String sendToHermes(String message) {
  if (WiFi.status() != WL_CONNECTED) return "WiFi disconnected";

  HTTPClient http;
  String response;

  String url = "http://";
  url += HERMES_HOST;
  url += ":";
  url += HERMES_PORT;
  url += "/v1/chat/completions";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  // ArduinoJson 7.x API（注意：不要用废弃的 StaticJsonDocument）
  JsonDocument doc;
  doc["model"] = "hermes-agent";
  JsonArray messages = doc["messages"].to<JsonArray>();
  JsonObject msg = messages.add<JsonObject>();
  msg["role"] = "user";
  msg["content"] = message;
  String body;
  serializeJson(doc, body);

  int httpCode = http.POST(body);
  if (httpCode == 200) {
    response = http.getString();
    JsonDocument respDoc;
    DeserializationError error = deserializeJson(respDoc, response);
    if (!error) {
      response = respDoc["choices"][0]["message"]["content"].as<String>();
    }
  } else {
    response = "HTTP error: " + String(httpCode);
  }

  http.end();
  return response;
}

// ============ 简易 TTS ============
void playTTS(String text) {
  Serial.print("🔊 Playing: ");
  Serial.println(text);
  playTone(2000);
  delay(text.length() * 50);
}

// ============ 播放提示音 ============
void playTone(int freq) {
  int samples = SAMPLE_RATE / 4;
  int16_t* buf = (int16_t*)malloc(samples * 2);
  if (buf == NULL) return;
  for (int i = 0; i < samples; i++) {
    buf[i] = (int16_t)(sin(2 * PI * freq * i / SAMPLE_RATE) * 8000);
  }
  size_t bytes_written;
  i2s_write(I2S_NUM_1, buf, samples * 2, &bytes_written, portMAX_DELAY);
  free(buf);
}
