#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把讲义 HTML 按 H2 切分为小节，抽出每节首段作为摘要线索。"""
import re, json, html as htmlmod, os

meta = json.load(open("build/heads.json", encoding="utf-8"))
out = []
for m in meta:
    n = m["n"]
    h = open(f"build/lectures/lect{n}.html", encoding="utf-8").read()
    # 按 h2 切分
    parts = re.split(r"(<h2[^>]*>[\s\S]*?</h2>)", h)
    # parts[0] 是 h1 + 引言
    intro = parts[0]
    h1m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", intro)
    title = htmlmod.unescape(re.sub(r"<[^>]+>", "", h1m.group(1))).strip() if h1m else ""
    intro_body = re.sub(r"<h1[\s\S]*?</h1>", "", intro)
    sections = []
    for i in range(1, len(parts), 2):
        sec_title = htmlmod.unescape(re.sub(r"<[^>]+>", "", parts[i])).strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        fm = re.search(r"<p[^>]*>([\s\S]*?)</p>", body)
        first = htmlmod.unescape(re.sub(r"<[^>]+>", "", fm.group(1))).strip() if fm else ""
        sections.append({"title": sec_title, "first": first, "body": body})
    out.append({"n": n, "title": title, "intro": intro_body, "sections": sections})
    print(f"\n### 第{n}讲 {title}")
    for s in sections:
        print(f"  - {s['title']} ｜ {s['first'][:90]}")

json.dump(out, open("build/sections.json", "w", encoding="utf-8"), ensure_ascii=False)
