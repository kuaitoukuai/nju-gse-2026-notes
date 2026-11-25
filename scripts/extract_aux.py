#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提取精读正文（seplanet）与字幕校对稿，统一为 HTML 片段 + 目录索引。"""
import re, os, json, html as htmlmod, glob

# ---------- 精读 ----------
SRC_J = "source/jingdu"
OUT_J = "build/jingdu"
os.makedirs(OUT_J, exist_ok=True)

def tidy(frag):
    frag = re.sub(r"<script[\s\S]*?</script>", "", frag)
    frag = re.sub(r"<style[\s\S]*?</style>", "", frag)
    frag = re.sub(r"<!--[\s\S]*?-->", "", frag)
    # 去掉 svg 图（概念关系图是内联 svg，体积大，保留文字即可）
    frag = re.sub(r"<svg[\s\S]*?</svg>", '<div class="figure-placeholder">［概念关系图：见原文页］</div>', frag)
    frag = re.sub(r"<figure[\s\S]*?</figure>", "", frag) if False else frag
    frag = re.sub(r"\n{3,}", "\n\n", frag)
    return frag.strip()

jmeta = []
for i in range(1, 14):
    p = os.path.join(SRC_J, f"seplanet-{i:02d}.html")
    if not os.path.exists(p):
        continue
    h = open(p, encoding="utf-8", errors="ignore").read()
    m = re.search(r'<article[^>]*class="reader-body"[^>]*>([\s\S]*?)</article>', h)
    if not m:
        print(f"!! 精读 {i} 未找到 article")
        continue
    frag = tidy(m.group(1))
    open(os.path.join(OUT_J, f"{i}.html"), "w", encoding="utf-8").write(frag)
    heads = []
    for mm in re.finditer(r"<h([2-4])[^>]*>([\s\S]*?)</h\1>", frag):
        t = htmlmod.unescape(re.sub(r"<[^>]+>", "", mm.group(2))).strip()
        if t:
            heads.append({"level": int(mm.group(1)), "text": t})
    plain = re.sub(r"<[^>]+>", "", frag)
    plain = re.sub(r"\s+", "", htmlmod.unescape(plain))
    jmeta.append({"n": i, "heads": heads, "chars": len(plain)})
    print(f"精读{i:02d}: {len(plain)} 字, H2={sum(1 for x in heads if x['level']==2)}, H3={sum(1 for x in heads if x['level']==3)}")

# ---------- 字幕 ----------
SRC_C = "source/github/NinZeige-NJU-2026-GSE-Captions-3e981c2/release"
OUT_C = "build/captions"
os.makedirs(OUT_C, exist_ok=True)

dirs = sorted(glob.glob(os.path.join(SRC_C, "*")))
cmeta = []
for d in dirs:
    name = os.path.basename(d)
    num = int(re.match(r"(\d+)", name).group(1))
    f = os.path.join(d, "README.md")
    if not os.path.exists(f):
        continue
    txt = open(f, encoding="utf-8", errors="ignore").read()
    # 去掉 markdown 标题行与分隔线，段落化
    paras = []
    for line in txt.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or set(s) <= {"-", "=", " "} or s.startswith("![") or s.startswith("[!["):
            continue
        paras.append("<p>" + htmlmod.escape(s) + "</p>")
    frag = "\n".join(paras)
    open(os.path.join(OUT_C, f"{num}.html"), "w", encoding="utf-8").write(frag)
    plain = re.sub(r"<[^>]+>", "", frag)
    cmeta.append({"n": num, "chars": len(re.sub(r"\s+", "", plain)), "paras": len(paras)})
    print(f"字幕{num:02d}: {cmeta[-1]['chars']} 字, {len(paras)} 段")

json.dump({"jingdu": jmeta, "captions": cmeta}, open("build/aux_heads.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n精读总字数:", sum(x["chars"] for x in jmeta))
print("字幕总字数:", sum(x["chars"] for x in cmeta))
