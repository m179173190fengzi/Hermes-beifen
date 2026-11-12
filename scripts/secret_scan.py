#!/usr/bin/env python3
"""secret_scan.py — 提交前扫描：找出待推送文件里的密钥/私钥/助记词。

只报告「文件名 + 行号 + 命中类型」，绝不打印密钥本身。
"""
import os
import re
import sys

ROOT = os.path.expanduser("~/.hermes")
TARGETS = ["skills", "scripts", "memories", "docs"]

PATTERNS = [
    ("Telegram Bot Token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b")),
    ("OpenAI/DeepSeek Key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Anthropic Key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("GitHub Token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("AWS Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("EVM Private Key", re.compile(r"\b(?:0x)?[0-9a-fA-F]{64}\b")),
    ("API key assignment", re.compile(
        r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|bot[_-]?token|"
        r"private[_-]?key|mnemonic|seed[_-]?phrase)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})")),
    ("Hardcoded bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}")),
]

SKIP_EXT = {".db", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz", ".pdf",
            ".woff", ".woff2", ".ttf", ".ico", ".mp3", ".mp4", ".pyc"}


def main() -> int:
    hits = 0
    scanned = 0
    for target in TARGETS:
        base = os.path.join(ROOT, target)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in
                           {".git", "node_modules", "__pycache__", ".venv", "venv"}]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(path) > 2_000_000:
                        continue
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, 1):
                            if len(line) > 4000:
                                continue
                            for name, rx in PATTERNS:
                                if rx.search(line):
                                    rel = os.path.relpath(path, ROOT)
                                    print(f"{rel}:{lineno}  <{name}>")
                                    hits += 1
                                    break
                    scanned += 1
                except Exception:
                    continue
    print(f"\n扫描 {scanned} 个文件，命中 {hits} 处", file=sys.stderr)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
