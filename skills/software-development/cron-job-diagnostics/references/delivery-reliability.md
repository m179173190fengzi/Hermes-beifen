# 让 no_agent cron 自己投递（带重试）——脚本骨架

适用：备份、日报、告警等**丢了会让人真的受影响**的 `no_agent` 任务。
调度器只负责「跑脚本 + 投递 stdout」，投递失败**没有重试**，所以关键任务把投递搬进脚本。

## 骨架

```bash
#!/bin/bash
set -uo pipefail          # ⚠️ 不要 set -e：会让脚本在发送前就退出

LOG=""
log() { LOG="${LOG}$*"$'\n'; }        # 只累积，不 echo 到 stdout
PROXY="http://127.0.0.1:7890"
HERMES_HOME="$HOME/.hermes"

log "=== 任务开始: $(date '+%Y-%m-%d_%H:%M') ==="

# ... 干活，每一步自己保证不中断 ...
# cp / rsync / git 等都用  || true  或显式 if 判断

# git push 重试
PUSH_OK=0
for i in 1 2 3 4; do
    if git push origin main >/tmp/push.log 2>&1; then PUSH_OK=1; break; fi
    sleep $((i * 20))
done
[ "$PUSH_OK" = 1 ] && log "✅ 已推送" || log "⚠️ push 重试 4 次失败（数据已提交到本地仓库）"

# 自己发 Telegram，带重试
TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$HERMES_HOME/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' ')
CHAT=$(grep -E '^TELEGRAM_HOME_CHANNEL=' "$HERMES_HOME/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' ')

SENT=0
if [ -n "$TOKEN" ] && [ -n "$CHAT" ]; then
    for i in 1 2 3 4 5; do
        CODE=$(HTTPS_PROXY="$PROXY" HTTP_PROXY="$PROXY" curl -s --max-time 30 \
            -o /dev/null -w "%{http_code}" \
            -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
            -d "chat_id=${CHAT}" --data-urlencode "text=${LOG}")
        [ "$CODE" = "200" ] && { SENT=1; break; }
        sleep $((i * 15))
    done
fi

# 成功静默；彻底失败才打印一行，让调度器兜底
[ "$SENT" = "1" ] || echo "⚠️ 任务完成但推送重试 5 次失败（消息见 job 日志）"
exit 0
```

## 必须记住的几点

- **成功时 stdout 必须为空**，否则调度器还会再投递一遍（重复消息），而且又暴露在无重试的投递层上。
- **`set -e` 是这类脚本的头号杀手**：任何一步（比如某次 `cp`、某次 `grep` 无匹配）失败，
  脚本直接退出，`发送报告` 根本不会执行 —— 用户得到的是彻底的静默，而且 `last_status` 可能是 error 也可能不是。
- **凭据从 `~/.hermes/.env` 读，不要写进脚本**；脚本本身可能在备份仓库里，读 .env 而不是内嵌 token 才安全。
- 收尾 `exit 0`：让调度器认为脚本正常结束；真正的失败通过那行兜底提示暴露。
- 这个改造不是"可选修辞"——它同时修掉了本会话遇到的
  `delivery error: Telegram send failed: httpx.ConnectError: All connection attempts failed`
  （7:41 备份成功的消息丢过一次）和"任务静默失效无人知晓"两类问题。

## 自检

改完跑一次：`bash <script>; echo "stdout长度=$(bash <script> 2>/dev/null | wc -c)"`
期望 stdout 长度 = 0（说明脚本自己发成功了）。
