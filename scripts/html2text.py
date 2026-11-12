#!/usr/bin/env python3
"""从本地 HTML 文件提取正文纯文本（去脚本/样式/标签）。

用法: python3 html2text.py <html文件> [起始关键词] [结束关键词]
"""
import html as htmllib
import re
import sys

path = sys.argv[1]
start_kw = sys.argv[2] if len(sys.argv) > 2 else None
end_kw = sys.argv[3] if len(sys.argv) > 3 else None

s = open(path, encoding="utf-8", errors="ignore").read()
s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
s = re.sub(r"<(br|/p|/div|/h[1-6]|/li)[^>]*>", "\n", s, flags=re.I)
s = re.sub(r"<[^>]+>", " ", s)
s = htmllib.unescape(s)
lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in s.split("\n")]
lines = [ln for ln in lines if ln]

text = "\n".join(lines)
if start_kw:
    i = text.find(start_kw)
    if i > 0:
        text = text[i:]
if end_kw:
    j = text.find(end_kw)
    if j > 0:
        text = text[:j]

# 去掉明显的导航噪声行
noise = ("Sign in", "Subscribe", "Share", "Follow", "Read more", "©", "Terms",
         "Privacy", "Cookie", "Paragraph", "Home", "Explore")
text = "\n".join(ln for ln in text.split("\n") if len(ln) > 1 and not ln.startswith(noise))
print(text)
