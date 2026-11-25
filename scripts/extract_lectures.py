#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 jyywiki 返回的 Next.js HTML 中提取讲义正文，输出清洗后的 HTML 片段 + 标题索引。"""
import re, os, json, html as htmlmod

SRC = "source/lectures"
OUT = "build/lectures"
os.makedirs(OUT, exist_ok=True)

def clean(fragment):
    # 去掉 script/style
    fragment = re.sub(r"<script[\s\S]*?</script>", "", fragment)
    fragment = re.sub(r"<style[\s\S]*?</style>", "", fragment)
    fragment = re.sub(r"<!--[\s\S]*?-->", "", fragment)
    # 相对链接转绝对
    fragment = fragment.replace('href="/', 'href="https://jyywiki.cn/')
    fragment = fragment.replace('src="/', 'src="https://jyywiki.cn/')
    # 去掉 next.js 内部属性
    fragment = re.sub(r'\sdata-n-[a-z-]+="[^"]*"', "", fragment)
    # 压缩多余空行
    fragment = re.sub(r"\n{3,}", "\n\n", fragment)
    return fragment.strip()

meta = []
for i in range(1, 14):
    p = os.path.join(SRC, f"lect{i}.md")
    raw = open(p, encoding="utf-8", errors="ignore").read()
    start = raw.find('<div class="wiki')
    if start < 0:
        print(f"!! lect{i} 未找到 wiki 容器")
        continue
    end = raw.find('<div class="bg-neutral-100 text-center', start)
    if end < 0:
        end = raw.find("</body>", start)
    frag = raw[start:end]
    # 去掉最外层 div 开标签
    frag = re.sub(r'^<div class="wiki[^"]*">', "", frag, count=1)
    # 去掉可能多余的尾部闭合 div
    frag = frag.rstrip()
    if frag.endswith("</div>"):
        frag = frag[: -len("</div>")]
    frag = clean(frag)
    open(os.path.join(OUT, f"lect{i}.html"), "w", encoding="utf-8").write(frag)

    # 提取标题
    heads = []
    for m in re.finditer(r"<h([1-6])[^>]*>([\s\S]*?)</h\1>", frag):
        lvl = int(m.group(1))
        txt = re.sub(r"<[^>]+>", "", m.group(2))
        txt = htmlmod.unescape(txt).strip()
        if txt:
            heads.append({"level": lvl, "text": txt})
    # 正文纯文本字数（中文按字符）
    plain = re.sub(r"<[^>]+>", "", frag)
    plain = htmlmod.unescape(plain)
    plain = re.sub(r"\s+", "", plain)
    meta.append({"n": i, "heads": heads, "chars": len(plain), "h2": sum(1 for h in heads if h["level"] == 2)})
    print(f"lect{i}: {len(plain)} 字, H1={sum(1 for h in heads if h['level']==1)}, H2={sum(1 for h in heads if h['level']==2)}, H3={sum(1 for h in heads if h['level']==3)}")

json.dump(meta, open("build/heads.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n总字数:", sum(m["chars"] for m in meta))
