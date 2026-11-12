#!/usr/bin/env python3
"""redact_keys.py — 推送前把真密钥替换成占位符。

只处理命令行显式指定的文件，避免误伤代码里的字符串模板。

用法：
    python3 redact_keys.py path/to/doc.md path/to/another.md
    grep -rl 'sk-' docs/conversations | xargs python3 redact_keys.py

    # 只检查不写，退出码 1 = 还有残留（适合放进推送前检查链）
    python3 redact_keys.py --check docs/conversations
"""
import os
import re
import sys

# 关键：字符类必须含 - 和 _，否则 sk-or-v1-… / sk-proj-… / sk-ant-… 全部漏网。
# 只写 [A-Za-z0-9] 会把最常见的带连字符 key 原样放行。
PATTERNS = [
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}"), "sk-ant-REDACTED"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "sk-REDACTED"),
    (re.compile(r"\b(?:xai|hf|nvapi|gsk|r8)_?[A-Za-z0-9_-]{20,}"), "<API_KEY>"),
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"), "<TELEGRAM_BOT_TOKEN>"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"), "<GITHUB_TOKEN>")
    ,
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<AWS_KEY>"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "<GOOGLE_KEY>"),
]


def iter_files(targets):
    for t in targets:
        p = os.path.expanduser(t)
        if os.path.isfile(p):
            yield p
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in
                           {".git", "node_modules", "__pycache__", ".venv", "venv"}]
                for f in files:
                    yield os.path.join(root, f)
        else:
            print(f"跳过（不存在）: {t}")


def main() -> int:
    args = sys.argv[1:]
    check_only = "--check" in args
    if check_only:
        args = [a for a in args if a != "--check"]
    if not args:
        print(__doc__)
        return 2

    total = 0
    dirty = 0
    for p in iter_files(args):
        try:
            if os.path.getsize(p) > 5_000_000:
                continue
            with open(p, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        new = text
        n = 0
        for rx, repl in PATTERNS:
            new, k = rx.subn(repl, new)
            n += k
        if not n:
            continue
        dirty += 1
        total += n
        if check_only:
            print(f"残留 {n} 处: {os.path.relpath(p)}")
            continue
        with open(p, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"已脱敏 {n} 处: {os.path.relpath(p)}")

    print(f"\n{'待脱敏' if check_only else '合计替换'} {total} 处，涉及 {dirty} 个文件")
    return 1 if (check_only and total) else 0


if __name__ == "__main__":
    sys.exit(main())
