#!/usr/bin/env python3
"""输出「推特热议 项目/代币」纯文本块，供链上日报直接嵌入。

内容：
  1) 首页时间线（≈用户实际刷到的内容）里出现频率最高的热议词
  2) 这些热议与 fomo热门榜 / GMGN热搜榜 的交叉命中（X 有讨论 + 链上在热）

复用 x_watch.py 的抓取与匹配逻辑（同目录导入）。

用法：python3 x_hot_brief.py
"""
import os
import re
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x_watch as xw  # noqa: E402

# 热议词统计时排除的通用词
BUZZ_STOP = set("""The This That These Those And But With Not You Your Our His Her She Was
Were Are Has Have Had Will Would Can Could Should One Two Three More Most Some Any Get Got
Make Made Like Look Looks Good Great Best First Last Next Today Tomorrow Yesterday LATEST
Breaking Update After Before Over Under Into Out About Only Also Even Much Many Very Still
Back Come Came Said Says Say Who Whom Which While Here Him Man Men Day Days Week Month Year
Time Video Watch Read Full Story Source Via Photo Photos Image Clip New Now Just All For
Subscribe Follow Give Away Link Below Click Http Https Com Www Am Pm Etc The""".split())


def buzz_keywords(tweets, topn=5):
    cnt = Counter()
    for tw in tweets:
        text = tw.get("text") or ""
        # 交易代号 $XXX 权重最高
        for w in re.findall(r"\$([A-Za-z][A-Za-z0-9]{1,9})\b", text):
            cnt["$" + w.upper()] += 3
        # 拉丁字母开头的项目名（跳过链接/句首常见词），要求纯 ASCII 且长度 >= 4
        for w in re.findall(r"\b[A-Z][a-zA-Z]{3,18}\b", text):
            if w.lower() in {s.lower() for s in BUZZ_STOP}:
                continue
            cnt[w] += 1
    # 只保留出现 >= 2 次的（$代号 >= 1 次即可），避免一次性噪声
    out = []
    for w, c in cnt.most_common(60):
        if w.startswith("$") or c >= 2:
            out.append(w)
        if len(out) >= topn:
            break
    return out


def main():
    env = xw.load_env()
    cfg = xw.load_json(xw.CONFIG, {"accounts": []})

    # feed 端点在 X 侧不稳定（CLI 算不出 transaction id），重试 3 次后回退到账号轮询
    tweets, src = None, ""
    for attempt in range(3):
        tweets, err = xw.twitter_json(["feed"], env)
        if tweets:
            src = "首页时间线"
            break
        time.sleep(5)
    if not tweets:
        agg = []
        for acc in cfg.get("accounts", []):
            tw, _ = xw.twitter_json(["user-posts", acc["handle"], "-n", "10", "--json"], env)
            if tw:
                agg.extend(tw)
        if agg:
            tweets, src = agg, "关注账号轮询(备用源)"
    if not tweets:
        print("━━━ 🐦 推特热议 项目/代币 ━━━")
        print("⚠️ 推特数据获取失败（feed 与账号轮询都不可用）")
        return 0

    fomo = xw.fetch_fomo()
    gmgn, _ = xw.fetch_hot()
    pool = xw.dedupe_pool(fomo, gmgn)

    # 交叉命中（X 有讨论 + 链上在热）
    hits, seen = [], set()
    for tw in tweets:
        for t in xw.match_hot(tw.get("text") or "", pool):
            key = (t["sym"], t["ca"])
            if key in seen:
                continue
            seen.add(key)
            hits.append((t, tw))
    hits.sort(key=lambda x: x[0]["vol"], reverse=True)

    words = buzz_keywords(tweets)

    print("━━━ 🐦 推特热议 项目/代币 ━━━")
    print("📡 数据源: %s（%d 条）" % (src, len(tweets)))
    if words:
        print("🔎 热议词: " + " / ".join(words))
    if hits:
        print("")
        for t, tw in hits[:5]:
            tag = "fomo热门" if t.get("src") == "fomo" else "GMGN热搜"
            print("  • %s (%s) %s#%s | MC $%s | 24h %s%% | 量 $%s | 持币 %s"
                  % (t["sym"], t["chain"], tag, t["rank"], f"{t['mc']:,.0f}",
                     f"{t['chg']:+.1f}", f"{t['vol']:,.0f}", f"{t['holders']:,}"))
            print("     CA: %s" % t["ca"])
            print("     ↳ 热议来源: @%s %s" % ((tw.get("author") or "?").lstrip("@"),
                                               tw.get("time") or "?"))
    else:
        print("⚡ 交叉命中: 今日首页热议与链上热度榜无重合（无 X 讨论 + 链上双热的标的）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
