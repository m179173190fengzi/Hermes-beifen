#!/usr/bin/env python3
"""redact_keys.py — 推送前把真密钥替换成占位符（只处理指定文件，避免误伤代码）。

规则：sk- 后接 20 位以上字母数字 → sk-REDACTED
      Telegram bot token 格式 → <TELEGRAM_BOT_TOKEN>
"""
import os
import re
import sys

PATTERNS = [
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "sk-REDACTED"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}"), "sk-ant-REDACTED"),
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"), "<TELEGRAM_BOT_TOKEN>"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"), "<GITHUB_TOKEN>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<AWS_KEY>"),
]

total = 0
for path in sys.argv[1:]:
    p = os.path.expanduser(path)
    if not os.path.isfile(p):
        print(f"跳过（不存在）: {path}")
        continue
    with open(p, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    orig = text
    n = 0
    for rx, repl in PATTERNS:
        text, k = rx.subn(repl, text)
        n += k
    if text != orig:
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已脱敏 {n} 处: {os.path.basename(p)}")
        total += n
    else:
        print(f"无需处理: {os.path.basename(p)}")

print(f"\n合计替换 {total} 处")
