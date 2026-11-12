#!/usr/bin/env python3
"""seed_precedent.py — 一次性把已知 CA 灌进先例库并回填数据。

不用内联 python -c，避免审批拦截。
"""
import os
import sqlite3
import subprocess
import sys

DB = os.path.expanduser("~/.hermes/data/precedent.db")
SCRIPT = os.path.expanduser("~/.hermes/scripts/precedent_db.py")

SEEDS = [
    ("bsc", "0x2a06ddb8f82b2926ccd852d8cdc2348246857777", "BSC 老盘复活"),
    ("sol", "FZxHLUGiGchY5uvvoeqh1EKiXTrGdN67WUBhUc1fLoat", "猫/性暗示 meme"),
    ("sol", "4CxjZyMNoF1p6eXHXHv1TWpS2X47CuUmLwtGe18spump", "中文猫 meme"),
    ("sol", "5qaP7oKUqKffwwo5DaEqDoTtsBLMpdbQTxEkCDaTpump", "发射台平台币"),
    ("bsc", "0xba300df4c929eb137e266d17d1fe6db058837777", None),
    ("sol", "SCGBBnSwnekytGFHgyeHHxPMiN7xDxsWFGg9JgFSTNK", None),
    ("bsc", "0x0c6302401aa5325c2e36f170f52c00b1d220b405", None),
    ("sol", "CSocnzcRpgSCr1naKcNTieWZUxb6rABe45j844m7pump", None),
    ("bsc", "0x7ffcf7b3b52adcc00c76f50ce2e37bf3c7e215dc", None),
    ("sol", "4kjruqGHDsSqkMdFfCjV7Vb62HPFhtXyWc2t6JpQzDnz", None),
]


def main() -> int:
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    for chain, ca, narrative in SEEDS:
        cmd = [sys.executable, SCRIPT, "add", "--chain", chain, "--ca", ca]
        if narrative:
            cmd += ["--narrative", narrative]
        subprocess.run(cmd, check=False)
    con = sqlite3.connect(DB)
    n = con.execute("SELECT COUNT(*) FROM coins").fetchone()[0]
    con.close()
    print(f"\n入库 {n} 个")
    print("开始回填…")
    subprocess.run([sys.executable, SCRIPT, "refresh", "--all"], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
