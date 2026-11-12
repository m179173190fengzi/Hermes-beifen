#!/usr/bin/env python3
"""抽取本机 Chrome 里 fomo.family 的全部 cookie → ~/.hermes/secrets/fomo_cookies.json
（含 Cookie 头字符串，方便 curl / urllib 直接带）。

用法：/home/wei/.venvs/xmon/bin/python ~/.hermes/scripts/fomo_cookie_extract.py
"""
import json
import os
import stat
import sys

import browser_cookie3

OUT = os.path.expanduser("~/.hermes/secrets/fomo_cookies.json")


def main():
    try:
        cj = browser_cookie3.chrome()
    except Exception as exc:  # noqa: BLE001
        print("读取 Chrome cookie 失败:", type(exc).__name__, str(exc)[:200])
        return 1

    rows = []
    for c in cj:
        dom = (c.domain or "").lstrip(".")
        if "fomo" in dom:
            rows.append({"name": c.name, "value": c.value, "domain": c.domain,
                         "path": c.path, "secure": bool(c.secure)})

    if not rows:
        print("没找到 fomo.family 的 cookie。确认 Chrome 已登录 fomo.family 后重试。")
        return 1

    header = "; ".join("%s=%s" % (r["name"], r["value"]) for r in rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"cookies": rows, "header": header}, fh, ensure_ascii=False, indent=1)
    os.chmod(OUT, stat.S_IRUSR | stat.S_IWUSR)

    print("OK 已写入 %s（%d 个 cookie）" % (OUT, len(rows)))
    for r in rows:
        v = r["value"]
        print("  %-26s %s…%s (长度 %d) [%s]" % (r["name"], v[:8], v[-4:], len(v), r["domain"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
