#!/usr/bin/env python3
"""挖 fomo.family 的 API 端点：抓前端 HTML → 找 JS 包 → 在包里搜 API 域名/路径。

用法：python3 ~/.hermes/scripts/fomo_api_discover.py
"""
import json
import os
import re
import urllib.request

PROXY = "http://127.0.0.1:7890"
SEC = os.path.expanduser("~/.hermes/secrets/fomo_cookies.json")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/155.0.0.0 Safari/537.36")

cfg = json.load(open(SEC, encoding="utf-8"))
COOKIE = cfg["header"]
OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Cookie": COOKIE,
        "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://fomo.family/",
    })
    with OPENER.open(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "ignore")


print("=== 1. 首页(带cookie) ===")
try:
    st, html = get("https://fomo.family/")
    print("status:", st, "len:", len(html))
except Exception as exc:  # noqa: BLE001
    print("失败:", exc)
    raise SystemExit(1)

scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html) + \
          re.findall(r'href="([^"]+\.js[^"]*)"', html)
chunks = [s if s.startswith("http") else "https://fomo.family" + ("" if s.startswith("/") else "/") + s
          for s in scripts]
print("JS 包数量:", len(chunks))

pat = re.compile(
    r'https://[a-zA-Z0-9.-]+\.(?:com|io|app|xyz|dev|net|ai)(?:/[a-zA-Z0-9/_.-]*)?|'
    r'"(/[a-zA-Z0-9_-]*api[a-zA-Z0-9/_-]*)"|'
    r'"(/(?:v[0-9]|trpc|graphql)[a-zA-Z0-9/_-]*)"')
found = {}
for url in chunks[:8]:
    try:
        st, js = get(url)
    except Exception:  # noqa: BLE001
        continue
    for m in pat.findall(js):
        for g in (m if isinstance(m, tuple) else (m,)):
            if not g:
                continue
            if any(x in g for x in ("googleapis", "gstatic", "googletagmanager",
                                    "facebook", "sentry", "walletconnect", "privy.io",
                                    "schema.org", "w3.org")):
                continue
            found[g] = found.get(g, 0) + 1

print("\n=== 2. 挖到的候选端点 ===")
for k, v in sorted(found.items(), key=lambda x: -x[1])[:30]:
    print("  %-70s x%d" % (k, v))
