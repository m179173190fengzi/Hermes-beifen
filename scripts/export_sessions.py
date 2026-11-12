#!/usr/bin/env python3
"""export_sessions.py — 把会话导出成可读 Markdown（脱敏、去工具噪音）。

只导出 user / assistant 的正文：
  · 跳过 role=tool 的输出（占体积 80%，对"学习"没价值）
  · 跳过 system prompt（含注入模板，不是知识）
  · 脱敏：sk-xxx / bot token / gh token
  · 单条消息截断到 --max-chars

用法：
  python3 export_sessions.py                        # 全部，默认到 ~/.hermes/docs/conversations
  python3 export_sessions.py --min-messages 6       # 只导有实质内容的会话
  python3 export_sessions.py --since 2026-11-01     # 只要最近的
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

DB = os.path.expanduser("~/.hermes/state.db")
OUT_DIR = os.path.expanduser("~/.hermes/docs/conversations")

SECRET_PATTERNS = [
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "sk-REDACTED"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}"), "sk-ant-REDACTED"),
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"), "<TELEGRAM_BOT_TOKEN>"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"), "<GITHUB_TOKEN>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<AWS_KEY>"),
]


def redact(text: str) -> str:
    for rx, repl in SECRET_PATTERNS:
        text = rx.sub(repl, text)
    return text


def clean(text: str, max_chars: int) -> str:
    text = redact(text or "")
    # 折叠超长代码块/日志，保留结构
    text = re.sub(r"```[^\n]*\n(.{3000})[^`]{200,}```", r"```\1 …(截断)```", text, flags=re.S)
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n…（截断，原长 {len(text)} 字符）"
    return text


def slug(s: str, n: int = 40) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", (s or "session")).strip("-")
    return s[:n] or "session"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="")
    ap.add_argument("--min-messages", type=int, default=4)
    ap.add_argument("--max-chars", type=int, default=6000)
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    q = ("SELECT id, title, started_at, message_count, model, source "
         "FROM sessions WHERE message_count >= ? ORDER BY started_at")
    rows = con.execute(q, (args.min_messages,)).fetchall()

    since_ts = None
    if args.since:
        since_ts = datetime.strptime(args.since, "%Y-%m-%d").replace(
            tzinfo=timezone.utc).timestamp()
        rows = [r for r in rows if (r["started_at"] or 0) >= since_ts]

    written = 0
    total_bytes = 0
    for r in rows:
        msgs = con.execute(
            "SELECT role, content, timestamp FROM messages "
            "WHERE session_id = ? AND role IN ('user','assistant') "
            "ORDER BY timestamp, id", (r["id"],)).fetchall()
        if not msgs:
            continue
        dt = datetime.fromtimestamp(r["started_at"] or 0, tz=timezone.utc)
        date = dt.strftime("%Y-%m-%d")
        title = (r["title"] or "(无标题)").strip()
        fname = f"{date}-{slug(title)}-{r['id'][-6:]}.md"
        path = os.path.join(args.out, fname)

        lines = [f"# {title}", "",
                 f"- 会话 ID：`{r['id']}`",
                 f"- 时间：{dt.strftime('%Y-%m-%d %H:%M UTC')}",
                 f"- 来源：{r['source'] or '-'} ｜ 模型：{r['model'] or '-'}",
                 f"- 消息数：{r['message_count']}", "", "---", ""]
        for m in msgs:
            who = "**用户**" if m["role"] == "user" else "**助手**"
            body = clean(m["content"], args.max_chars)
            if not body:
                continue
            lines.append(f"### {who}")
            lines.append("")
            lines.append(body)
            lines.append("")
        text = "\n".join(lines)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        written += 1
        total_bytes += len(text.encode("utf-8"))

    con.close()
    print(f"导出 {written} 个会话 → {args.out}")
    print(f"总大小 {total_bytes/1024/1024:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
