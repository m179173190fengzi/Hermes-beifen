#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three-chain new-token scanner for the 每日Alpha cron (新币监控 阶段).

用途：trenches 返回大量 $0 垃圾（漏 --min-marketcap）或空/全重发时，从 **trending** 侧
补齐新币候选（SKILL.md「新币段候选源不只 trenches…从 trending 6h 筛 <1D + MC≥$1M 补位」）。
alpha-report-parser.py 只做评分/TOP5/热搜交叉/trenches，不吐 trending 的新币年龄，故独立成脚本。

前置：三链 trending --raw 已落盘（时间戳后缀或固定名均可，内部走 latest() glob）
  HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
    gmgn-cli market trending --chain sol --interval 6h --limit 30 --raw > /tmp/alpha_sol_6h_<ts>.json
  （同理 bsc / robinhood；文件名前缀用短标签 sol/bsc/rh，与 --chain 全称无关）

用法：
  python3 scan-new-tokens.py            # 默认 <24h 段 + <48h 且 MC≥$1M 候选段
  python3 scan-new-tokens.py 12         # 自定义年龄阈值（小时）

输出：每链两段——① 所有 age<阈值的盘（含 MC<$1M 小盘，用于判断同名簇/情绪盘）；
      ② age<48h 且 MC≥$1M 的新币监控候选（下一步逐个 `token info --raw` 核 creation_timestamp）。
⚠️ trending 的 creation_timestamp 可能是重发/迁移时间——候选必须再过 token info 核验（见 SKILL.md）。
"""
import json, glob, re, sys, time


def latest(base):
    """取最新时间戳后缀文件；无则回落固定名。见 SKILL.md glob-latest 坑。"""
    stem = base[:-5] if base.endswith(".json") else base
    cands = [f for f in glob.glob(stem + "*") if re.search(r"_(\d{10})\.json$", f)]
    if cands:
        return sorted(cands, key=lambda p: int(re.search(r"_(\d{10})\.json$", p).group(1)))[-1]
    return base if glob.glob(base) else None


def mc_fmt(v):
    v = float(v or 0)
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.2f}M"
    if v >= 1e3:
        return f"${v/1e3:.1f}K"
    return f"${v:.0f}"


def main():
    max_age = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0
    now = time.time()
    for chain, path in [("SOL", "/tmp/alpha_sol_6h.json"),
                        ("BSC", "/tmp/alpha_bsc_6h.json"),
                        ("RH", "/tmp/alpha_rh_6h.json")]:
        f = latest(path)
        if not f:
            print(f"\n===== {chain}: 无 trending 文件（{path}） =====")
            continue
        d = json.load(open(f))
        rank = d.get("data", {}).get("rank", []) if isinstance(d, dict) else []
        print(f"\n===== {chain} ({f.split('/')[-1]}) =====")
        print(f"--- age < {max_age:.0f}h 全部新盘 ---")
        for t in rank:
            ct = t.get("creation_timestamp", 0) or 0
            age = (now - ct) / 3600 if ct else -1
            if 0 <= age < max_age:
                print(f"  {t.get('symbol'):<12} MC {mc_fmt(t.get('market_cap')):>9} | age {age:5.1f}h | "
                      f"6h {t.get('price_change_percent')} | SM {t.get('smart_degen_count')} | "
                      f"vol {mc_fmt(t.get('volume'))} | {t.get('launchpad_platform')} | CA {t.get('address')}")
        print(f"--- age < 48h 且 MC>=1M（新币监控候选，需 token info 核验创建时间）---")
        for t in rank:
            ct = t.get("creation_timestamp", 0) or 0
            age = (now - ct) / 3600 if ct else -1
            mc = t.get("market_cap") or 0
            hi = t.get("history_highest_market_cap") or 0
            if 0 <= age < 48 and mc >= 1e6:
                print(f"  * {t.get('symbol'):<12} MC {mc_fmt(mc)} 高点 {mc_fmt(hi)} | age {age:.1f}h | "
                      f"SM {t.get('smart_degen_count')} | 6h {t.get('price_change_percent')} | CA {t.get('address')}")


if __name__ == "__main__":
    main()
