# Silent adapter death — "active 但收不到消息"（2026-10-19 实测）

## 症状

用户："tg 又连不上了"。但系统角度一切正常：

- `systemctl --user is-active hermes-gateway` → **active**
- `hermes gateway status` → running，MainPID 存在，内存正常
- 代理正常，`getMe` 经代理 http=200 / 1.2s
- **出站也正常**：凌晨 05:47 的 cron 日报照样投递到 TG

唯一异常：从 00:31 起 journald 里再没有 telegram 相关日志，用户发的消息永远没人处理。静默失联 9 小时。

## 日志证据（journald，不是 gateway.log）

```
00:31:49 telegram.error.TimedOut: Pool timeout: All connections in the connection
         pool are occupied. Request was *not* sent to Telegram.
00:31:49 WARNING ...adapter: [Telegram] Telegram polling reconnect failed: Pool timeout ...
00:31:49 ERROR   ...adapter: [Telegram] Telegram polling could not reconnect after
         10 network error retries. Restarting gateway. Last error: Pool timeout ...
00:31:49 ERROR   gateway.run: Fatal telegram adapter error (telegram_network_error):
         Telegram polling could not reconnect after 10 network error retries. Restarting gateway.
（之后 9 小时：无任何 telegram 日志；进程 PID 未变）
```

关键点：**日志说 "Restarting gateway"，但进程没有重启**（PID 与 14 小时的 etime 都没变），polling 就此永久停止，systemd 仍报 active。这是最容易误判成"网络问题"的一条。

## 判别流程

```bash
# 1. 进程是不是很久没换过（etime 远大于本次故障时间 → 没真重启）
systemctl --user show -p MainPID -p ActiveEnterTimestamp --value hermes-gateway
ps -eo pid,etime,cmd | grep "gateway run" | grep -v grep

# 2. 近 30 分钟有没有 telegram 日志（没有 = 适配器已经不在工作）
journalctl --user -u hermes-gateway --since "30 min ago" --no-pager | grep -i telegram

# 3. 致命标记（决定性证据）
journalctl --user -u hermes-gateway --until "now" --no-pager \
  | grep -iE "could not reconnect after|Fatal .*adapter error|polling could not reconnect" | tail -3
```

不要只看 `~/.hermes/logs/gateway.log`：这台机器上它最后一次写入是 2026-08-20，日志早已只进 journald。查它会得到"一切正常"的假象。

## 恢复

重启网关即可（历史积累的坏连接随进程一起清掉）：

```bash
bash ~/.hermes/scripts/restart_gateway.sh     # 内容就是 systemctl --user restart hermes-gateway
```

验证：新 PID、`ActiveEnterTimestamp` 变新、`ss -tnp | grep pid=<新PID>` 能看到指向 `127.0.0.1:7890` 的 ESTAB 长连接（通常是 2 条）、`getWebhookInfo` 的 `pending_update_count` 为 0。最终确认仍要真人发一条消息。

## 根因倾向

代理（FlClash）瞬时抖动 + httpx 连接池被 getUpdates 长轮询占满 → 10 次重连全撞在池满上。不是 Telegram 侧故障，也不是 token/白名单问题。缓解手段是监控 + 重启，而不是改 config。
