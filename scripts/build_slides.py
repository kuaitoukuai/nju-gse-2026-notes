# -*- coding: utf-8 -*-
"""整理课件：幻灯片本地化 + 实验页清洗 + 索引页。"""
import os, re, shutil, html as H, json

SRC_S = "source/slides"
SRC_L = "source/labs"
OUT = "dist/课件"
os.makedirs(OUT + "/assets", exist_ok=True)

# 复制依赖
for f in ("mathjax-tex-svg.js", "highlight.min.js"):
    shutil.copy(os.path.join(SRC_S, "assets", f), os.path.join(OUT, "assets", f))

REPL = {
    "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js": "assets/mathjax-tex-svg.js",
    "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/highlight.min.js": "assets/highlight.min.js",
}

lectures = []
SEC = {x["n"]: x["title"] for x in json.load(open("build/sections.json", encoding="utf-8"))}
for i in range(1, 15):
    p = os.path.join(SRC_S, f"slides{i}.html")
    if not os.path.exists(p):
        continue
    s = open(p, encoding="utf-8", errors="ignore").read()
    for k, v in REPL.items():
        s = s.replace(k, v)
    # 指向课程主页的绝对路径改为在线地址，避免本地 404
    s = s.replace('href="/GSE/2026/"', 'href="https://jyywiki.cn/GSE/2026/"')
    out = os.path.join(OUT, f"slides-{i:02d}.html")
    open(out, "w", encoding="utf-8").write(s)
    m = re.search(r"<title>(.*?)</title>", s)
    raw_title = H.unescape(m.group(1)) if m else f"第 {i} 讲"
    raw_title = re.sub(r"^第\s*\d+\s*讲\s*·\s*", "", raw_title).strip()
    title = SEC.get(i) or raw_title
    lectures.append({"n": i, "title": title, "raw": raw_title, "size": os.path.getsize(out) // 1024})
    print(f"slides-{i:02d}.html  {title}  ({raw_title})  {len(s)//1024}KB")

# 实验页
labs = []
LAB_NAME = {1: "Lab1 · 个人数字助手", 2: "Lab2 · Deeper Research", 3: "Lab3 · 蒸馏你自己"}
for i in (1, 2, 3):
    p = os.path.join(SRC_L, f"lab{i}.md")
    if not os.path.exists(p):
        continue
    raw = open(p, encoding="utf-8", errors="ignore").read()
    start = raw.find('<div class="wiki')
    end = raw.find('<div class="bg-neutral-100 text-center', start)
    frag = raw[start:end] if start >= 0 else raw
    frag = re.sub(r'^<div class="wiki[^"]*">', "", frag, count=1)
    frag = re.sub(r"<script[\s\S]*?</script>", "", frag)
    frag = frag.rstrip()
    if frag.endswith("</div>"):
        frag = frag[: -len("</div>")]
    frag = frag.replace('href="/', 'href="https://jyywiki.cn/')
    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{LAB_NAME[i]}</title>
<style>
:root{{--ink:#1e2328;--ink2:#545b63;--line:#e6e2d8;--accent:#0f766e;--code:#f2efe8}}
*{{box-sizing:border-box}}
body{{margin:0;background:#fbfaf7;color:var(--ink);
font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
font-size:16px;line-height:1.95}}
.top{{position:sticky;top:0;background:rgba(251,250,247,.92);backdrop-filter:blur(10px);
border-bottom:1px solid var(--line);padding:12px 24px;font-size:13px;color:var(--ink2)}}
.top a{{color:var(--accent);text-decoration:none}}
.wrap{{max-width:780px;margin:0 auto;padding:40px 24px 100px}}
h1{{font-size:1.9rem;line-height:1.35;margin:0 0 1em}}
h2{{font-size:1.25rem;margin:2em 0 .6em;padding-left:12px;border-left:3px solid var(--accent)}}
h3{{font-size:1.05rem;margin:1.6em 0 .5em}}
p{{margin:0 0 1em;text-align:justify}}
code{{background:var(--code);padding:1px 5px;border-radius:4px;font-size:.88em;
font-family:ui-monospace,Consolas,monospace}}
pre{{background:#1d232b;color:#e6edf3;padding:14px 16px;border-radius:9px;overflow:auto;font-size:13px;line-height:1.7}}
pre code{{background:none;color:inherit;padding:0}}
blockquote{{margin:1.2em 0;padding:10px 16px;border-left:3px solid #b45309;
background:rgba(180,83,9,.05);color:var(--ink2);border-radius:0 8px 8px 0}}
table{{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:14px}}
th,td{{border:1px solid var(--line);padding:7px 10px;text-align:left}}
th{{background:var(--code)}}
a{{color:var(--accent)}}
img{{max-width:100%;border-radius:8px}}
</style></head><body>
<div class="top"><a href="index.html">← 课件目录</a>　|　{LAB_NAME[i]}<span style="float:right">南京大学《生成式软件工程》2026 秋</span></div>
<div class="wrap">{frag}</div></body></html>"""
    out = os.path.join(OUT, f"lab-{i}.html")
    open(out, "w", encoding="utf-8").write(page)
    labs.append({"n": i, "title": LAB_NAME[i]})
    print(f"lab-{i}.html 生成")

# 索引页
cards = ""
for L in lectures:
    cards += f"""<a class="card" href="slides-{L['n']:02d}.html">
      <div class="num">{L['n']:02d}</div>
      <div class="t">{H.escape(L['title'])}</div>
      <div class="m">幻灯片 · {L['size']} KB</div></a>"""
labcards = ""
for L in labs:
    labcards += f"""<a class="card lab" href="lab-{L['n']}.html">
      <div class="num">L{L['n']}</div>
      <div class="t">{H.escape(L['title'])}</div>
      <div class="m">实验说明</div></a>"""

index = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>课件与实验 · 生成式软件工程 2026</title>
<style>
:root{{--bg:#fbfaf7;--panel:#fff;--ink:#1e2328;--ink2:#5c636b;--ink3:#8b9098;
--line:#e7e3d8;--accent:#0f766e;--soft:#e6f4f1}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
-webkit-font-smoothing:antialiased}}
header{{padding:56px 24px 26px;max-width:1100px;margin:0 auto}}
h1{{margin:0 0 8px;font-size:2rem;letter-spacing:-.01em}}
.sub{{color:var(--ink3);font-size:13.5px;line-height:1.7}}
.tag{{display:inline-block;background:var(--soft);color:var(--accent);font-size:11.5px;
font-weight:600;padding:3px 10px;border-radius:20px;margin-bottom:14px}}
main{{max-width:1100px;margin:0 auto;padding:0 24px 80px}}
h2{{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink3);
margin:38px 0 14px;font-weight:600}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}}
.card{{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:16px 16px 14px;text-decoration:none;color:inherit;transition:.16s;position:relative;overflow:hidden}}
.card:hover{{border-color:var(--accent);box-shadow:0 8px 22px rgba(15,118,110,.10);transform:translateY(-2px)}}
.card .num{{font-size:11px;font-weight:700;color:var(--accent);letter-spacing:.05em;margin-bottom:6px}}
.card .t{{font-size:14.5px;font-weight:600;line-height:1.5;margin-bottom:5px}}
.card .m{{font-size:11px;color:var(--ink3)}}
.card.lab .num{{color:#b45309}}
.card.lab:hover{{border-color:#b45309;box-shadow:0 8px 22px rgba(180,83,9,.10)}}
.note{{margin-top:34px;padding:16px 18px;background:#f3f1ea;border-radius:10px;
font-size:12.5px;line-height:1.85;color:var(--ink2)}}
.note b{{color:var(--ink)}}
footer{{max-width:1100px;margin:0 auto;padding:0 24px 60px;font-size:11.5px;color:var(--ink3);line-height:1.8}}
</style></head><body>
<header>
  <div class="tag">离线可用 · 无需联网</div>
  <h1>课件与实验</h1>
  <div class="sub">南京大学《生成式软件工程》2026 秋 · 蒋炎岩<br>
  14 讲幻灯片（HTML 放映版）+ 3 个实验说明，已在本地补齐 MathJax 与代码高亮</div>
</header>
<main>
  <h2>幻灯片 · 14 讲</h2>
  <div class="grid">{cards}</div>
  <h2>实验 · Lab1–Lab3</h2>
  <div class="grid">{labcards}</div>
  <div class="note">
    <b>怎么用</b>：每个幻灯片都是完整的一页式 HTML，方向键 / 空格翻页，浏览器全屏（F11）即可当投影放。<br>
    <b>与讲义的关系</b>：幻灯片是课堂实际放映的版本，信息密度高、以图和短句为主；文字版推导见主阅读器的「讲义原文」。<br>
    <b>第 14 讲</b>：课件已发布，但讲义 <code>lect14.md</code> 尚未公开，所以主阅读器暂未收录这一讲。<br>
    <b>来源</b>：jyywiki.cn/GSE/2026/，CC BY-NC 4.0（署名 + 非商业）。
  </div>
</main>
<footer>整理：2026-11-25　|　幻灯片 © 蒋炎岩 / 南京大学　|　本目录仅作本地学习用</footer>
</body></html>"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(index)
print("index.html 生成")
json.dump({"lectures": lectures, "labs": labs}, open("build/slides_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
