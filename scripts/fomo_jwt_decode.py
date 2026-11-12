#!/usr/bin/env python3
"""解码 fomo.family 的 Privy JWT，打印 claims（用于找 API 域名/用户ID）。"""
import base64
import json
import os

P = os.path.expanduser("~/.hermes/secrets/fomo_cookies.json")
data = json.load(open(P, encoding="utf-8"))


def dec(tok):
    try:
        parts = tok.split(".")
        if len(parts) < 2:
            return {"_raw": tok[:40], "_note": "不是 JWT"}
        pad = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(pad))
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc)[:80]}


for c in data["cookies"]:
    if c["name"] in ("privy-access-token", "privy-token"):
        print("=== %s (%s) ===" % (c["name"], c["domain"]))
        print(json.dumps(dec(c["value"]), indent=1, ensure_ascii=False)[:900])
        print()
    elif c["name"] == "privy-session":
        print("=== privy-session ===")
        print(c["value"])
        print()
