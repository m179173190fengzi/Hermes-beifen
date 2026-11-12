# Wayback Machine 抓取被墙/超时的政府站点 (gov.au 验证)

## 背景
澳洲政府站 (如 tradesrecognitionaustralia.gov.au) 从国内网络直连和走代理都超时；
搜索引擎(DDG/Bing/Google)对这类查询返回污染结果。web.archive.org 走代理可用，
且 .au 域名被 National Library of Australia domain crawl 覆盖，存档齐全。

## 代码模式 (Python, 走 FLClash 代理 127.0.0.1:7890)

```python
import urllib.request, ssl, socket, json, re, time

socket.setdefaulttimeout(40)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

proxy_handler = urllib.request.ProxyHandler({
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
})
# 注意: context 要传给 HTTPSHandler，不能传给 opener.open()
opener = urllib.request.build_opener(
    proxy_handler,
    urllib.request.HTTPSHandler(context=ctx)
)

# 1) CDX API 枚举存档 (collapse 去重, filter 只要200)
cdx = ("https://web.archive.org/cdx/search/cdx"
       "?url=tradesrecognitionaustralia.gov.au*"
       "&output=json&limit=500&filter=statuscode:200&collapse=urlkey")
req = urllib.request.Request(cdx, headers={"User-Agent": "Mozilla/5.0"})
rows = json.loads(opener.open(req, timeout=60).read().decode())[1:]
# 每行: [原URL, 时间戳, 存档URL, ...]

# 2) 抓原始文件 — 必须加 id_ 后缀，否则返回HTML包装页
url = f"https://web.archive.org/web/{timestamp}id_/{original_url}"
data = opener.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read()

# 3) PDF 提取文本
# pdftotext -layout file.pdf file.txt
```

## 关键要点
- **抓PDF/docx必须 `id_`**: `web/20230604000000id_/https://...` — 不带id_拿到的是存档HTML包装
- 有的下载URL在CDX有记录但内容404 (存档不完整) → 从CDX列表换其他时间戳/版本号(id数字)重试
- CDX有 rate limit: 429 Too Many Requests → 请求间 sleep 2-3s，间隔查询
- `collapse=urlkey` 按URL去重；`filter=statuscode:200` 只留成功的
- 官网有时用代理直连也会超时，但 archive.org 通过同一代理通常正常 — 先测 archive.org 判断代理是否通
- execute_code 沙箱里 urllib 可用；terminal 里 curl 需要 `-x http://127.0.0.1:7890` 且注意超时
- 页面HTML文本提取: 正则去 script/style/标签后 \s+ 压缩

## 通用性
适用于任何被墙/超时的政府或官方站点: immi.homeaffairs.gov.au, homeaffairs.gov.au 等。
先试直连 → 试代理 → 都不行就上 Wayback。政府站点通常被 NLA/Common Crawl 收录，存档比商业站全。
