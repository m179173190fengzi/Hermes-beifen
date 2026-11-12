#!/usr/bin/env python3
"""下载 fomo.family 相关 JS 分片，从代码里提取真实 API 路径。

用法：python3 ~/.hermes/scripts/fomo_find_paths.py
"""
import json
import os
import re
import subprocess
import time

HOME = os.path.expanduser("~")
CK = json.load(open(os.path.join(HOME, ".hermes/secrets/fomo_cookies.json"), encoding="utf-8"))["header"]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
PROXY = "http://127.0.0.1:7890"
OUTDIR = "/tmp/fomojs"
os.makedirs(OUTDIR, exist_ok=True)

KEY = re.compile(r"feed|token|leaderboard|home|trending|discover|market|rank|hot|list",
                 re.IGNORECASE)


def curl(url, out, timeout=25):
    r = subprocess.run(["curl", "-s", "--http2", "--max-time", str(timeout), "-o", out,
                        "-w", "%{http_code}", "-H", "Cookie: " + CK, "-H", "User-Agent: " + UA,
                        url], capture_output=True, text=True,
                       env=dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY))
    return r.stdout.strip()


man = os.path.join(OUTDIR, "manifest.js")
print("拉 manifest:", curl("https://fomo.family/assets/manifest-1463ef71.js", man))
chunks = sorted(set(re.findall(r"/assets/([a-zA-Z0-9._-]+\.js)", open(man, encoding="utf-8").read())))
picked = [c for c in chunks if KEY.search(c)]
# 数量太多只取前 40 个（优先名字短的，通常是核心模块）
picked = sorted(picked, key=len)[:40]
print("候选分片:", len(chunks), "→ 抓取", len(picked))

paths = {}
for i, c in enumerate(picked, 1):
    f = os.path.join(OUTDIR, c)
    if curl("https://fomo.family/assets/" + c, f) != "200":
        continue
    js = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.findall(r'[`"\'](/[a-zA-Z][a-zA-Z0-9/_-]{2,50})[`"\']', js):
        if m.startswith("/assets/") or m.startswith("/images/"):
            continue
        paths.setdefault(m, set()).add(c)
    time.sleep(0.4)

print("\n=== 提取到的路径 ===")
for p, srcs in sorted(paths.items(), key=lambda x: -len(x[1])):
    print("  %-42s  (%d 个文件: %s)" % (p, len(srcs), list(srcs)[0][:34]))
print("\n共 %d 个唯一路径" % len(paths))
