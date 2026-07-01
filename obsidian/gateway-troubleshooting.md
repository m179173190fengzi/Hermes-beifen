# Gateway 故障诊断

## 描述
Hermes Gateway 的连接故障排查指南。Gateway 负责处理 Telegram、Discord、Slack 等平台的入站消息路由。

## 用途
- 快速定位平台连接中断原因
- 恢复 Gateway 与各平台的通信
- 诊断 Webhook、Bot Token、Rate Limit 等问题

## 常见问题与解决

**Telegram 连接失败**
- 检查 Bot Token 是否有效
- 确认 Webhook URL 是否正确注册
- 验证 SSL 证书是否有效

**Discord 断连**
- 检查 Bot Token 和 Intents 配置
- 确认 Gateway Intents 已正确启用
- 验证 Rate Limit 是否被触发

**Slack 消息丢失**
- 检查 Event Subscriptions URL
- 验证 OAuth Token 作用域
- 确认 Socket Mode 配置正确

```bash
# 检查 Gateway 状态
hermes gateway status

# 重启 Gateway 连接
hermes gateway reconnect --platform telegram

# 查看日志
tail -f ~/.hermes/logs/gateway.log
```
