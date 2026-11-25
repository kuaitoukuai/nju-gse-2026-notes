# -*- coding: utf-8 -*-
"""把手册 Markdown 转成单文件 HTML，方便同事不装编辑器也能看。"""
import re, html as H
from md2html import md2html

md = open("dist/AI代码检查手册.md", encoding="utf-8").read()
# 任务清单转成方框字符，md2html 不认识 - [ ]
md = md.replace("- [ ] ", "- ☐ ")
body = md2html(md, drop_first_h1=True)
# 单独提取标题
m = re.search(r"^# (.+)$", md, re.M)
title = m.group(1) if m else "手册"

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(title)}</title>
<style>
:root{{--bg:#fbfaf7;--panel:#fff;--ink:#1e2328;--ink2:#545b63;--ink3:#8b9098;
--line:#e7e3d8;--accent:#0f766e;--amber:#b45309;--code:#f2efe8}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
font-size:16px;line-height:1.95;-webkit-font-smoothing:antialiased}}
.top{{position:sticky;top:0;z-index:9;background:rgba(251,250,247,.93);backdrop-filter:blur(12px);
border-bottom:1px solid var(--line);padding:11px 22px;font-size:12.5px;color:var(--ink3);
display:flex;justify-content:space-between}}
.top b{{color:var(--accent);font-weight:600}}
.wrap{{max-width:760px;margin:0 auto;padding:44px 24px 110px}}
h1{{font-size:2rem;line-height:1.3;margin:0 0 .3em;letter-spacing:-.01em}}
h2{{font-size:1.3rem;margin:2.4em 0 .7em;padding-left:13px;border-left:3px solid var(--accent);
line-height:1.5}}
h3{{font-size:1.08rem;margin:1.8em 0 .5em}}
h4{{font-size:1rem;margin:1.4em 0 .4em;color:var(--ink2)}}
p{{margin:0 0 1em;text-align:justify}}
blockquote{{margin:1.2em 0;padding:12px 18px;border-left:3px solid var(--amber);
background:rgba(180,83,9,.045);color:#3f3a33;border-radius:0 8px 8px 0}}
blockquote p:last-child{{margin-bottom:0}}
code{{background:var(--code);padding:1.5px 5px;border-radius:4px;font-size:.87em;
font-family:ui-monospace,SFMono-Regular,Consolas,monospace;border:1px solid #e9e5da}}
pre{{background:#1d232b;color:#e6edf3;padding:15px 17px;border-radius:10px;overflow:auto;
font-size:13px;line-height:1.75;margin:1.2em 0}}
pre code{{background:none;border:none;color:inherit;padding:0}}
ul,ol{{padding-left:1.4em;margin:.8em 0}}
li{{margin:.3em 0}}
table{{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:13.5px}}
th,td{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}
th{{background:var(--code);font-weight:600}}
hr{{border:none;border-top:1px solid var(--line);margin:2.4em 0}}
a{{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(15,118,110,.3)}}
strong{{font-weight:650}}
.md-fig{{display:inline-block;padding:1px 8px;border-radius:4px;background:var(--code);
color:var(--ink3);font-size:11.5px;border:1px solid var(--line)}}
.math{{font-family:ui-monospace,Consolas,monospace;background:var(--code);padding:1px 5px;
border-radius:4px;font-size:.9em}}
@media print{{
  .top{{display:none}}
  body{{background:#fff}}
  .wrap{{max-width:100%;padding:0}}
  h2{{page-break-after:avoid}}
  pre,table,blockquote{{page-break-inside:avoid}}
  a{{color:#000;border:none}}
}}
</style></head><body>
<div class="top"><span><b>AI 代码检查手册</b>　课程方法整理</span><span>南京大学《生成式软件工程》2026 秋</span></div>
<div class="wrap">
<h1>{H.escape(title)}</h1>
{body}
</div></body></html>"""
open("dist/AI代码检查手册.html", "w", encoding="utf-8").write(html)
print("HTML 已生成", len(html) // 1024, "KB")
