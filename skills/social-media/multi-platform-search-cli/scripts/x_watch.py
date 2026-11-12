#!/usr/bin/env python3
"""X 账号监控（Hermes no_agent cron 用，零 LLM 成本）。

盯一份账号名单，只推送「新推 + 命中条件」的推文；没有命中就完全静默。

为什么是「盯账号」而不是「关键词搜索」：
  1. twitter-cli 的 search 端点常因 X 前端改版返回 404（transaction id 算不出），
     而 user-posts 稳定可用；
  2. 催化剂/公告/喊单总是**从某个具体账号先发**——盯账号才是正确的原语。

三种账号模式（配置见 x_watchlist.json）：
  keyword —— 正文命中关键词才推
  viral   —— 点赞数 >= min_likes 就推（**正文只有 t.co 链接的账号必须用这个**，
             例如特朗普的推文正文常只有一个链接，关键词匹配完全无效）
  all     —— 任何新推都推

min_likes > 0 时与 keyword 是「或」关系（高互动也算命中）。

用法：
  python3 x_watch.py           # 正常跑（cron 用）
  python3 x_watch.py --test    # 忽略去重状态，打印所有命中（调关键词/阈值）
  python3 x_watch.py --all     # 忽略过滤，打印每个账号最新一条（验证抓取链路）

部署：复制到 ~/.hermes/scripts/，名单放 ~/.hermes/cron/x_watchlist.json，
挂 no_agent cron（建议 */20 * * * *）。stdout 空 = 静默不推送。
"""
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
COOKIE_ENV = os.path.join(HOME, ".hermes/secrets/x_cookies.env")
CONFIG = os.path.join(HOME, ".hermes/cron/x_watchlist.json")
STATE = os.path.join(HOME, ".hermes/cron/state/x_watch.json")
PROXY = "http://127.0.0.1:7890"
TWITTER_BIN = os.path.join(HOME, ".local/bin/twitter")

STATE_KEEP = 40  # 每个账号保留最近多少条已见 ID
MAX_BLOCKS = 8   # 单次最多推几条，防止刷屏


def load_env():
    """组装环境：代理 + cookie（从 env 文件读，不要写死在脚本里）。"""
    env = dict(os.environ)
    env["HTTPS_PROXY"] = PROXY
    env["HTTP_PROXY"] = PROXY
    if os.path.exists(COOKIE_ENV):
        with open(COOKIE_ENV, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\s*export\s+([A-Z_]+)=(.*)", line.strip())
                if m:
                    env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    env["PATH"] = os.path.join(HOME, ".local/bin") + ":" + env.get("PATH", "")
    return env


def fetch(handle, n, env):
    """拉某账号最新推文，返回 (list[dict], None) 或 (None, 错误说明)。

    ⚠️ twitter-cli 会在 JSON **之前**打印一行 WARNING（ClientTransaction 初始化失败），
    所以必须定位第一个 '[' 再解析，不能直接 json.loads(stdout)。
    """
    try:
        p = subprocess.run(
            [TWITTER_BIN, "--compact", "user-posts", handle, "-n", str(n), "--json"],
            capture_output=True, text=True, timeout=120, env=env,
        )
    except subprocess.TimeoutExpired:
        return None, "超时"
    out = p.stdout or ""
    start = out.find("[")
    if start < 0:
        return None, (out.strip().splitlines() or ["无输出"])[-1][:80]
    try:
        return json.loads(out[start:]), None
    except json.JSONDecodeError as exc:
        return None, "JSON解析失败: %s" % exc


def load_state():
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1)


def kw_regex(keywords):
    """ASCII 关键词用**词边界**匹配，CJK 用子串。

    ⚠️ 别用 `kw in text`：'star' 会命中 'started'、'eth' 会命中 'whether'，
    实测这种误报会直接把信噪比打崩。
    """
    parts = []
    for k in keywords:
        esc = re.escape(k)
        parts.append(r"\b%s\b" % esc if k.isascii() else esc)
    return re.compile("|".join(parts), re.IGNORECASE) if parts else None


def hit(tw, acc, kw_pat):
    text = (tw.get("text") or "")
    m = kw_pat.search(text) if kw_pat else None
    kw_hit = m.group(0) if m else None
    likes = tw.get("likes") or 0
    viral = likes >= (acc.get("min_likes") or 0)
    mode = acc.get("mode", "keyword")
    if mode == "all":
        return True, "全部模式"
    if kw_hit:
        return True, "关键词「%s」" % kw_hit
    if viral:
        return True, "高互动 %s赞" % f"{likes:,}"
    return False, None


def main():
    test = "--test" in sys.argv
    show_all = "--all" in sys.argv
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)
    kw_pat = kw_regex(cfg.get("keywords", []))
    n = cfg.get("max_per_account", 10)
    env = load_env()
    state = load_state()

    hits = []  # (likes, block) —— 先收集再按热度排序截断
    errors = []
    for acc in cfg["accounts"]:
        handle = acc["handle"]
        label = acc.get("label", handle)
        tweets, err = fetch(handle, n, env)
        if tweets is None:
            errors.append("%s(@%s): %s" % (label, handle, err))
            continue
        seen = state.get(handle, [])
        new_ids = []
        for tw in tweets:
            tid = str(tw.get("id"))
            if tid in new_ids:
                continue
            new_ids.append(tid)
            # ⚠️ --test 必须绕过去重，否则调参时永远看到空输出（踩过的坑）
            if not show_all and not test and tid in seen:
                continue
            ok, why = hit(tw, acc, kw_pat)
            if show_all or ok:
                text = (tw.get("text") or "").strip() or "(仅图片/视频，无正文)"
                hits.append((tw.get("likes") or 0,
                    "🔥 %s @%s%s\n%s\n❤️ %s赞 | 🔁 %s转 | 🕐 %s\nhttps://x.com/%s/status/%s"
                    % (label, handle, "" if show_all else " — %s" % why, text,
                       f"{tw.get('likes', 0):,}", f"{tw.get('rts', 0):,}",
                       tw.get("time", "?"), handle, tid)))
        merged = new_ids + [i for i in seen if i not in new_ids]
        state[handle] = merged[:STATE_KEEP]

    output = []
    # ⚠️ 按点赞降序再截断：否则名单里靠前的账号会把单次额度吃光，后面的永远推不出来
    hits.sort(key=lambda x: x[0], reverse=True)
    blocks = [b for _, b in (hits if show_all else hits[:MAX_BLOCKS])]
    if blocks:
        header = "📡 X 监控 — %d 条新动态" % len(blocks)
        if len(blocks) >= MAX_BLOCKS:
            header += "（已达单次上限 %d，其余下次推）" % MAX_BLOCKS
        output.append(header)
        output.append("")
        output.extend(blocks)
    if errors:
        output.append("")
        output.append("⚠️ 抓取失败: " + " | ".join(errors))
    if output:
        print("\n".join(output))
    elif errors and not test:
        # 全挂时必须出声，否则监控会静默失效（比刷屏更糟）
        print("⚠️ X 监控异常: " + " | ".join(errors))
    if not test:
        save_state(state)


if __name__ == "__main__":
    sys.exit(main())
