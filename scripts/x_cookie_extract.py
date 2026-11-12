#!/usr/bin/env python3
"""从本机 Chrome 抽取 x.com 的 auth_token / ct0，写入 ~/.hermes/secrets/x_cookies.env

用途：修复 Hermes 的 X/Twitter 抓取（twitter-cli 需要这两个 cookie）。
只在需要时手动运行；不会打印完整 cookie 值。
"""
import os
import stat
import sys

import browser_cookie3

OUT = os.path.expanduser("~/.hermes/secrets/x_cookies.env")


def main():
    try:
        cj = browser_cookie3.chrome(domain_name="x.com")
    except Exception as exc:  # noqa: BLE001
        print("抽取失败:", type(exc).__name__, str(exc)[:300])
        return 1

    at = ct = None
    for c in cj:
        if c.name == "auth_token":
            at = c.value
        elif c.name == "ct0":
            ct = c.value

    if not at or not ct:
        print("未找到 cookie。auth_token=%s ct0=%s" % (bool(at), bool(ct)))
        print("确认 Chrome 里已登录 x.com（并关掉其他占用 profile 的窗口后重试）")
        return 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("export TWITTER_AUTH_TOKEN=%s\n" % at)
        fh.write("export TWITTER_CT0=%s\n" % ct)
    os.chmod(OUT, stat.S_IRUSR | stat.S_IWUSR)  # 600

    print("OK 已写入 %s" % OUT)
    print("  auth_token: %s…%s (长度 %d)" % (at[:6], at[-4:], len(at)))
    print("  ct0:        %s…%s (长度 %d)" % (ct[:6], ct[-4:], len(ct)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
