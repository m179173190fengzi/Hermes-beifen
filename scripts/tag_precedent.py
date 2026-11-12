#!/usr/bin/env python3
"""tag_precedent.py — 给先例库里的币补叙事标签。"""
import os
import sqlite3

DB = os.path.expanduser("~/.hermes/data/precedent.db")

TAGS = {
    "0x2a06ddb8f82b2926ccd852d8cdc2348246857777": "BSC 老盘复活",
    "FZxHLUGiGchY5uvvoeqh1EKiXTrGdN67WUBhUc1fLoat": "猫/性暗示 meme",
    "4CxjZyMNoF1p6eXHXHv1TWpS2X47CuUmLwtGe18spump": "中文猫 meme",
    "5qaP7oKUqKffwwo5DaEqDoTtsBLMpdbQTxEkCDaTpump": "发射台平台币",
    "0xba300df4c929eb137e266d17d1fe6db058837777": "BSC 无叙事冷盘",
    "SCGBBnSwnekytGFHgyeHHxPMiN7xDxsWFGg9JgFSTNK": "日语人名梗",
    "0x0c6302401aa5325c2e36f170f52c00b1d220b405": "BSC 平台币(gang.fun)",
    "CSocnzcRpgSCr1naKcNTieWZUxb6rABe45j844m7pump": "韩国食物梗",
    "0x7ffcf7b3b52adcc00c76f50ce2e37bf3c7e215dc": "AI 概念",
    "4kjruqGHDsSqkMdFfCjV7Vb62HPFhtXyWc2t6JpQzDnz": "名 IP 侵权(GTA6)",
}

con = sqlite3.connect(DB)
for ca, tag in TAGS.items():
    con.execute("UPDATE coins SET narrative=? WHERE address=?", (tag, ca))
con.commit()
n = con.execute("SELECT COUNT(*) FROM coins WHERE narrative IS NOT NULL").fetchone()[0]
con.close()
print(f"已打标签 {n} 个")
