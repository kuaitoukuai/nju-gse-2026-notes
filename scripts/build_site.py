#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""组装数据、注入模板、生成阅读器与 Markdown 总目录/全文。"""
import re, json, html as htmlmod, os, sys
from overview import VIDEO, OVERVIEW
from md2html import md2html

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return htmlmod.unescape(s).strip()

def first_sentence(text, limit=42):
    text = re.sub(r"\s+", " ", text).strip()
    m = re.match(r"(.{4,60}?[。！？])", text)
    s = m.group(1) if m else text
    s = s.rstrip("。！？")
    if len(s) <= limit:
        return s
    cut = s[:limit]
    sp = cut.rfind(" ")
    if sp > limit * 0.6:
        cut = cut[:sp]
    return cut.rstrip("，、；：") + "…"

def paras_of(html):
    out = []
    for m in re.finditer(r"<p[^>]*>([\s\S]*?)</p>", html):
        t = strip_tags(m.group(1))
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 12:
            out.append(t)
    return out

sections = json.load(open("build/sections.json", encoding="utf-8"))
jmeta = {x["n"]: x for x in json.load(open("build/aux_heads.json", encoding="utf-8"))["jingdu"]}

# Argon 重写版（hqhq1025/ai-course-notes）：仅 1-8 讲
ARGON = {}
for i in range(1, 9):
    p = f"source/argon/lecture{i:02d}-notes.md"
    if not os.path.exists(p):
        continue
    md_txt = open(p, encoding="utf-8").read()
    rh = md2html(md_txt)
    plain = re.sub(r"<[^>]+>", "", rh)
    ARGON[i] = {
        "html": rh,
        "chars": len(re.sub(r"\s+", "", plain)),
        "h2": len(re.findall(r"<h2", rh)),
        "h3": len(re.findall(r"<h3", rh)),
        "pdf": f"https://github.com/hqhq1025/ai-course-notes/releases/download/nju-gse-2026-argon-v2/lecture{i:02d}-notes.pdf",
    }
print("Argon 讲次:", sorted(ARGON.keys()), "总字数:", sum(v["chars"] for v in ARGON.values()))

lectures = []
for sec in sections:
    n = sec["n"]
    bvid, date, dur, views = VIDEO[n]
    ov = OVERVIEW[n]
    jh = open(f"build/jingdu/{n}.html", encoding="utf-8").read()
    ch = open(f"build/captions/{n}.html", encoding="utf-8").read()
    jplain = strip_tags(jh)
    cplain = strip_tags(ch)
    sections_out = []
    for s in sec["sections"]:
        ps = paras_of(s["body"])
        points = []
        for p in ps[:6]:
            t = first_sentence(p)
            if t and t not in points:
                points.append(t)
        sections_out.append({"title": s["title"], "body": s["body"], "points": points})
    lectures.append({
        "n": n, "title": sec["title"], "date": date, "dur": dur, "views": views, "bvid": bvid,
        "one": ov["one"], "q": ov["q"], "points": ov["points"],
        "intro": sec["intro"], "sections": sections_out,
        "chars": sum(len(strip_tags(s["body"])) for s in sec["sections"]),
        "jingdu": {"html": jh, "chars": len(re.sub(r"\s+", "", jplain))},
        "captions": {"html": ch, "chars": len(re.sub(r"\s+", "", cplain))},
        "rewrite": ARGON.get(n),
    })

DATA = {"lectures": lectures}
payload = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))
payload = payload.replace("</script>", "<\\/script>")

tpl = open("template.html", encoding="utf-8").read()
html_out = tpl.replace("/*__DATA__*/", payload)
os.makedirs("dist", exist_ok=True)
open("dist/GSE2026-课程全集.html", "w", encoding="utf-8").write(html_out)
print("HTML:", round(len(html_out)/1024/1024, 2), "MB")

# ---------- Markdown: 讲义全文 ----------
def h2md(frag):
    """极简 HTML -> Markdown"""
    s = frag
    s = re.sub(r"<pre[^>]*><code[^>]*>([\s\S]*?)</code></pre>", lambda m: "\n```\n" + htmlmod.unescape(m.group(1)).strip() + "\n```\n", s)
    s = re.sub(r"<pre[^>]*>([\s\S]*?)</pre>", lambda m: "\n```\n" + htmlmod.unescape(strip_tags(m.group(1))).strip() + "\n```\n", s)
    s = re.sub(r"<h1[^>]*>([\s\S]*?)</h1>", lambda m: "\n# " + strip_tags(m.group(1)) + "\n", s)
    s = re.sub(r"<h2[^>]*>([\s\S]*?)</h2>", lambda m: "\n## " + strip_tags(m.group(1)) + "\n", s)
    s = re.sub(r"<h3[^>]*>([\s\S]*?)</h3>", lambda m: "\n### " + strip_tags(m.group(1)) + "\n", s)
    s = re.sub(r"<h4[^>]*>([\s\S]*?)</h4>", lambda m: "\n#### " + strip_tags(m.group(1)) + "\n", s)
    s = re.sub(r"<li[^>]*>([\s\S]*?)</li>", lambda m: "- " + strip_tags(m.group(1)) + "\n", s)
    s = re.sub(r"<blockquote[^>]*>([\s\S]*?)</blockquote>", lambda m: "\n> " + strip_tags(m.group(1)) + "\n", s)
    s = re.sub(r"<strong[^>]*>([\s\S]*?)</strong>", lambda m: "**" + strip_tags(m.group(1)) + "**", s)
    s = re.sub(r"<em[^>]*>([\s\S]*?)</em>", lambda m: "*" + strip_tags(m.group(1)) + "*", s)
    s = re.sub(r"<code[^>]*>([\s\S]*?)</code>", lambda m: "`" + htmlmod.unescape(strip_tags(m.group(1))) + "`", s)
    s = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)</a>', lambda m: "[" + strip_tags(m.group(2)) + "](" + m.group(1) + ")", s)
    s = re.sub(r"<p[^>]*>([\s\S]*?)</p>", lambda m: "\n" + strip_tags(m.group(1)) + "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

md = ["# 南京大学《生成式软件工程》2026 秋 · 讲义全文",
      "",
      "> 主讲：蒋炎岩（南京大学计算机学院）｜课程站点：https://jyywiki.cn/GSE/2026/",
      "> 许可：CC BY-NC 4.0（署名 + 非商业性使用）",
      "> 本文由课程公开讲义整理合并，共 13 讲。整理时间：2026-11-24。",
      ""]
for L in lectures:
    md.append("\n---\n")
    md.append(f"\n# 第 {L['n']:02d} 讲　{L['title']}\n")
    md.append(h2md(L["intro"]))
    for s in L["sections"]:
        md.append("\n## " + s["title"] + "\n")
        md.append(h2md(s["body"]))
out_md = "\n".join(md)
out_md = re.sub(r"\n{3,}", "\n\n", out_md)
open("dist/GSE2026-讲义全文.md", "w", encoding="utf-8").write(out_md)
print("讲义全文 MD:", round(os.path.getsize("dist/GSE2026-讲义全文.md")/1024, 1), "KB")

# ---------- Markdown: 总目录 ----------
md = ["# 《生成式软件工程》2026 秋 · 三级目录与速览",
      "",
      "- **课程**：南京大学《生成式软件工程》（Generative Software Engineering, GSE），2026 年秋季学期",
      "- **主讲**：蒋炎岩（南京大学计算机学院副教授、博导）｜B 站「绿导师原谅你了」",
      "- **时间**：每周二 10:00–12:00｜共 18 讲大纲，已上线 14 讲视频（截至 2026-11-24）",
      "- **课程主页**：https://jyywiki.cn/GSE/2026/",
      "- **视频合集**：https://space.bilibili.com/202224425/lists?sid=8942017",
      "- **许可**：讲义 CC BY-NC 4.0（署名 + 非商业）",
      "",
      "> 目录层级：**讲 → 讲义小节 → 本节要点**。要点由讲义段落首句压缩而成，用于快速定位原文。",
      "",
      "## 总目录",
      ""]
for L in lectures:
    md.append(f"- **第 {L['n']:02d} 讲　{L['title']}**（{L['date']}·{L['dur']} 分钟）")
    for i, s in enumerate(L["sections"], 1):
        md.append(f"  - {L['n']}.{i}　{s['title']}")
        for p in s["points"][:3]:
            md.append(f"    - {p}")
md += ["", "---", "", "# 分讲速览", ""]
for L in lectures:
    md += [f"## 第 {L['n']:02d} 讲　{L['title']}", "",
           f"`{L['date']}` · `{L['dur']} 分钟` · `{L['views']} 播放` · [`{L['bvid']}`](https://www.bilibili.com/video/{L['bvid']})", "",
           f"**一句话**：{L['one']}", "",
           f"**本讲要回答**：{L['q']}", "",
           "**核心要点**", ""]
    for i, p in enumerate(L["points"], 1):
        md.append(f"{i}. **{p[0]}** — {p[1]}")
    md += ["", "**本讲结构**", ""]
    for i, s in enumerate(L["sections"], 1):
        md.append(f"- `{L['n']}.{i}` **{s['title']}**")
        for p in s["points"][:4]:
            md.append(f"  - {p}")
    md += ["", f"> 原文：https://jyywiki.cn/GSE/2026/lect{L['n']}.md ｜ 视频：https://www.bilibili.com/video/{L['bvid']}", ""]
open("dist/GSE2026-总目录.md", "w", encoding="utf-8").write("\n".join(md))
print("总目录 MD:", round(os.path.getsize("dist/GSE2026-总目录.md")/1024, 1), "KB")

# ---------- 附：延伸材料索引 ----------
md = ["# 延伸材料索引", "",
      "除官方讲义外，本课程还有四套第三方整理。它们不是官方内容，许可与准确性各有边界，",
      "但组织方式不同，交叉对照时最容易看出哪些是重点。", "",
      "## 1. Argon 系统重写版（`hqhq1025/ai-course-notes`）", "",
      "- **覆盖**：第 1–8 讲，445 页，单讲 4–5 万字",
      "- **方法**：据官方讲义、全部 290 页课件、课堂字幕与 GitHub 案例重写；正文 Gemini Argon，配图编校 Codex",
      "- **形态**：PDF（单讲 7–22 MB）+ Markdown + LaTeX 源码 + 课件图 `slides-images/`",
      "- **入口**：https://github.com/hqhq1025/ai-course-notes/tree/main/nju-generative-software-engineering-2026/argon-rewrite",
      "- **PDF**：https://github.com/hqhq1025/ai-course-notes/releases/tag/nju-gse-2026-argon-v2",
      "- **本目录**：已把 8 讲纯文字版注入阅读器的「系统重写」视图（课件图转为占位）",
      "",
      "## 2. Video2Book 模块全书（`LINJIANG12/video2book-courses`）", "",
      "- **覆盖**：P01–P07，5 册模块全书 + 5 篇复习笔记 + 12 份逐字稿",
      "- **方法**：从课程音频重构，按主题重新分册（册=书、章≈50 分钟讲课）",
      "- **特点**：不是按讲次，而是按知识主题重组；笔记标题层级可直接生成脑图",
      "- **本目录**：`参考资料/Video2Book/`（Markdown，含索引 README）",
      "",
      "## 3. 逐讲精读（微信公众号「软工星球」/ seplanet.cn）", "",
      "- **覆盖**：13 篇，与 13 讲一一对应",
      "- **特点**：每篇含「一页导读 / 概念关系图 / 贯穿案例 / 完整学习笔记 / 自测」",
      "- **本目录**：已注入阅读器的「逐讲精读」视图",
      "",
      "## 4. 教案库（`LvGitHub-9/lesson-plans`）", "",
      "- **覆盖**：第 1–6 讲",
      "- **特点**：原子知识点编号（S1、S2…）+ 依赖图 + 11 字段体例（定义/为什么/怎么用/例子/边界/误区/关联…）",
      "- **本目录**：`参考资料/教案库-gse-2026/`",
      "",
      "## 未收录", "",
      "- **微信公众号「AI4L」**：把第 1 讲拆成 6 篇个人笔记，仅见 P1/6，碎片化，未收录。",
      "- **前两讲图文实录**：Argon 仓库 `lecture01|02` 下有带时间戳与课堂画面的 `course.md`，需要时可直接取。",
      ""]
open("dist/参考资料/延伸材料索引.md", "w", encoding="utf-8").write("\n".join(md))
print("延伸材料索引已写入")
