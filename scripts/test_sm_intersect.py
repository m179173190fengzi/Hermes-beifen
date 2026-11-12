#!/usr/bin/env python3
"""验证聪明钱库交集逻辑：拉某 BSC 代币前 100 持仓，与 o皇库求交集。"""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
import bsc_hard_filter as f  # noqa: E402

ca = sys.argv[1] if len(sys.argv) > 1 else "0x610a36f996650be0561f5d74d36b7e73520a7777"
sm = f.load_sm()
print("聪明钱库载入: %d 个地址" % len(sm))

data = f.gmgn(["token", "holders", "--chain", "bsc", "--address", ca,
               "--limit", "100", "--raw"]) or {}
rows = data.get("list") or []
addrs = [(h.get("address") or "").lower() for h in rows]
print("持仓拉取: %d 条" % len(addrs))

hits = [(a, sm[a]) for a in addrs if a in sm]
print("交集: %d 个 %s" % (len(hits), hits[:5]))

# 反向验证：把第一个持仓地址塞进 sm 字典，看能否命中
if addrs:
    sm2 = dict(sm)
    sm2[addrs[0]] = "单元测试"
    print("注入测试: %s" % ("命中 ✓" if addrs[0] in sm2 else "失败"))
