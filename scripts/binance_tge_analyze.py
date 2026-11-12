#!/usr/bin/env python3
"""币安 TGE/Alpha 公告 —— 事实提取（给 agent 做判断用的紧凑简报）。

读 pending 队列里 analyzed=false 的条目，抓公告正文 → 提取
合约地址/时间/百分比/关键数字，若有 CA 再补链上结构，输出紧凑简报。
处理完把条目标记为 analyzed。

用法：
  python3 binance_tge_analyze.py            # 处理全部待分析
  python3 binance_tge_analyze.py --peek     # 只看待分析数量（不处理）
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser("~")
STATE = os.path.join(HOME, ".hermes/cron/state/binance_tge.json")
GMGN = os.path.join(HOME, ".local/bin/gmgn-cli")
PROXY = "http://127.0.0.1:7890"
DETAIL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode="
CST = timezone(timedelta(hours=8))

RE_EVM = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
RE_SOL = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")


def load(p, d):
    try:
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return d


def save(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fetch_detail(code):
    req = urllib.request.Request(DETAIL + code, headers={"User-Agent": "Mozilla/5.0"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=40) as r:
        return json.loads(r.read().decode())


def lex_text(node, out):
    """从 Lexical 编辑器 JSON 里递归抽纯文本。"""
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            out.append(node["text"])
        for v in node.values():
            if isinstance(v, (dict, list)):
                lex_text(v, out)
    elif isinstance(node, list):
        for v in node:
            lex_text(v, out)


def body_text(detail):
    body = ((detail.get("data") or {}).get("body")) or ""
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return re.sub(r"<[^>]+>", " ", body)
    out = []
    lex_text(body, out)
    txt = " ".join(out)
    return re.sub(r"\s+", " ", txt)


def gmgn(args, timeout=120):
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        p = subprocess.run([GMGN] + args, capture_output=True, text=True, env=env, timeout=timeout)
        if p.returncode == 0 and p.stdout.strip():
            return json.loads(p.stdout)
    except Exception:  # noqa: BLE001
        pass
    return None


def onchain(ca, chain):
    j = gmgn(["token", "info", "--chain", chain, "--address", ca, "--raw"])
    if not j:
        return None
    px = float((j.get("price") or {}).get("price") or 0)
    sup = float(j.get("circulating_supply") or j.get("total_supply") or 0)
    return {
        "mc": px * sup if (px and sup) else 0,
        "lp": float(j.get("liquidity") or 0),
        "holders": j.get("holder_count") or 0,
        "top10": (j.get("stat") or {}).get("top_10_holder_rate"),
        "dev_n": (j.get("dev") or {}).get("creator_open_count"),
        "dev_status": (j.get("dev") or {}).get("creator_token_status"),
        "lock": j.get("locked_ratio"),
        "platform": j.get("launchpad_platform"),
    }


def main():
    st = load(STATE, {"seen": {}, "pending": []})
    pend = st.get("pending") or []
    todo = [p for p in pend if not p.get("analyzed")]
    if "--peek" in sys.argv:
        print("待分析: %d 条" % len(todo))
        return 0
    if not todo:
        return 0

    out = []
    for item in todo[:5]:
        title = item.get("title") or ""
        out.append("════ %s ════" % title[:90])
        out.append("发布: %s | 类目: %s" % (item.get("ts"), item.get("catalog")))
        out.append("链接: %s" % item.get("url"))
        try:
            d = fetch_detail(item.get("code") or "")
            txt = body_text(d)
        except Exception as e:  # noqa: BLE001
            out.append("正文抓取失败: %s" % str(e)[:80])
            item["analyzed"] = True
            continue

        # 关键片段：含时间/比例/供应/价格/池子的句子
        sents = re.split(r"(?<=[.!?。！？])\s+", txt)
        keys = ("utc", "time", "tge", "launchpool", "megadrop", "airdrop", "supply",
                "circulat", "allocation", "unlock", "price", "pool", "trading",
                "%", "epoch", "snapshot", "alpha")
        picked = [s.strip() for s in sents
                  if any(k in s.lower() for k in keys) and 15 < len(s) < 320][:8]
        if picked:
            out.append("正文要点:")
            for s in picked:
                out.append("  · " + s)
        # 数字/时间直方
        times = re.findall(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?", txt)[:4]
        pcts = re.findall(r"\d+(?:\.\d+)?%", txt)[:6]
        if times:
            out.append("时间点: " + " | ".join(times))
        if pcts:
            out.append("百分比: " + " | ".join(dict.fromkeys(pcts)))
        if len(txt) < 200:
            out.append("正文(节选): " + txt[:400])

        # 合约 + 链上
        evm = list(dict.fromkeys(RE_EVM.findall(txt)))[:3]
        sol = [a for a in dict.fromkeys(RE_SOL.findall(txt)) if not a.lower().startswith("0x")][:3]
        if evm or sol:
            out.append("疑似 CA: " + " ".join(evm + sol))
            for ca in (evm[:1] + sol[:1]):
                chain = "bsc" if ca.startswith("0x") else "sol"
                oc = onchain(ca, chain)
                if oc:
                    out.append("  ⛓️ %s 链上: MC $%s | LP $%s | 持币 %s | Top10 %s | dev发币 %s(%s) | 锁定 %s | %s"
                               % (chain, f"{oc['mc']:,.0f}", f"{oc['lp']:,.0f}", oc["holders"],
                                  oc["top10"], oc["dev_n"], oc["dev_status"], oc["lock"], oc["platform"]))
        else:
            out.append("正文未含合约地址（可能尚未公布）")
        out.append("")
        item["analyzed"] = True

    save(STATE, st)
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
