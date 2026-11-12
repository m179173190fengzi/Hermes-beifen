#!/usr/bin/env python3
"""全量扫 fomo.family 的 JS 分片，提取所有 API 路径（/v1/ /v2/ /api/ 等）。"""
import json
import os
import re
import subprocess
import time

HOME = os.path.expanduser("~")
CK = json.load(open(os.path.join(HOME, ".hermes/secrets/fomo_cookies.json"), encoding="utf-8"))["header"]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
PROXY = "http://127.0.0.1:7890"
OUTDIR = "/tmp/fomojs2"
os.makedirs(OUTDIR, exist_ok=True)
ENV = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)


def curl(url, out, timeout=20):
    r = subprocess.run(["curl", "-s", "--http2", "--max-time", str(timeout), "-o", out,
                        "-w", "%{http_code}", "-H", "Cookie: " + CK, "-H", "User-Agent: " + UA,
                        url], capture_output=True, text=True, env=ENV)
    return r.stdout.strip()


man = os.path.join(OUTDIR, "manifest.js")
curl("https://fomo.family/assets/manifest-1463ef71.js", man)
chunks = sorted(set(re.findall(r"/assets/([a-zA-Z0-9._-]+\.js)",
                               open(man, encoding="utf-8").read())))
print("分片总数:", len(chunks))

PAT = re.compile(r'[`"\'](/(?:v[0-9]|api)[a-zA-Z0-9/_{}$.-]{2,60})[`"\']')
found, ok = {}, 0
for i, c in enumerate(chunks, 1):
    f = os.path.join(OUTDIR, c)
    if curl("https://fomo.family/assets/" + c, f) == "200":
        ok += 1
        js = open(f, encoding="utf-8", errors="ignore").read()
        for m in PAT.findall(js):
            found.setdefault(m, set()).add(c)
    if i % 50 == 0:
        print("  进度 %d/%d（成功%d）" % (i, len(chunks), ok))
    time.sleep(0.15)

print("\n下载成功 %d 个分片" % ok)
print("=== 提取到的 API 路径 ===")
for p, srcs in sorted(found.items()):
    print("  %-46s ← %s" % (p, list(srcs)[0][:38]))
