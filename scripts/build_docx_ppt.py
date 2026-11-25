# -*- coding: utf-8 -*-
"""逐字稿 × PPT 对照 Word：逐字稿为骨架，插入对应 PPT 页，适合打印批注。
输出 dist/print/GSE2026-逐字稿与PPT-A4.docx
"""
import os, re, json, html as H
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
import build_docx as B

OUT = "dist/print"
GREY = RGBColor(0x77, 0x77, 0x77)
SOFT = RGBColor(0x3B, 0x42, 0x49)
ACCENT = RGBColor(0x0F, 0x5E, 0x5A)

def bigrams(s):
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", s)
    return set(s[i:i + 2] for i in range(len(s) - 1))

def sim(a, b):
    A, Bg = bigrams(a), bigrams(b)
    if not A or not Bg:
        return 0.0
    return len(A & Bg) / ((len(A) ** 0.5) * (len(Bg) ** 0.5))

def load_cap(n):
    s = open(f"build/captions/{n}.html", encoding="utf-8").read()
    ps = [re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", x))).strip()
          for x in re.findall(r"<p>([\s\S]*?)</p>", s)]
    return [p for p in ps if len(p) > 15]

def align(pages, paras):
    N, M = len(pages), len(paras)
    S = [[sim(p["text"], q) for q in paras] for p in pages]
    NEG = -1e9
    dp = [[NEG] * (M + 1) for _ in range(N + 1)]
    bk = [[0] * (M + 1) for _ in range(N + 1)]
    for j in range(M + 1):
        dp[0][j] = 0
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            best, arg = dp[i][j - 1], 0
            c = dp[i - 1][j - 1] + S[i - 1][j - 1]
            if c > best:
                best, arg = c, 1
            dp[i][j] = best
            bk[i][j] = arg
    res = [None] * N
    i, j = N, M
    while i > 0 and j > 0:
        if bk[i][j] == 1:
            res[i - 1] = j - 1
            i -= 1
        j -= 1
    last = 0
    for k in range(N):
        if res[k] is None:
            res[k] = last
        else:
            last = res[k]
    return res

TITLES = {1: "欢迎来到未来", 2: "提示词与上下文工程", 3: "版本管理", 4: "版本管理 (2)",
          5: "软件工程的来龙去脉", 6: "需求和架构 (1)", 7: "需求和架构 (2)",
          8: "Agent Native 开发", 9: "DeepSeek Harness", 10: "软件的演化",
          11: "软件质量保障 (1)", 12: "软件质量保障 (2)", 13: "软件分析工具"}

def main(ns):
    meta = json.load(open("build/slides_pages.json", encoding="utf-8"))
    doc = Document()
    B.base_style(doc)
    B.setup_section(doc, "生成式软件工程 · 2026 秋", "逐字稿 × PPT")
    B.cover(doc, "生成式软件工程", "逐字稿 × PPT 对照",
            ["主讲：蒋炎岩（南京大学计算机学院副教授、博导）",
             "内容：课堂实录逐字稿 + 对应幻灯片，按讲述位置插入",
             "用途：边听边看、纸上批注；图片下方标注该页 PPT 序号",
             "整理：2026-11-25　|　逐字稿 CC BY-NC 4.0"])

    # 目录
    doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(12)
    B.set_run(p.add_run("目　录"), size=16, bold=True, ea_font="黑体", color=B.INK)
    for n in ns:
        pg = meta[str(n)]["pages"]
        q = doc.add_paragraph()
        q.paragraph_format.space_after = Pt(3)
        B.set_run(q.add_run("第 %02d 讲　%s" % (n, TITLES[n])), size=10.5, bold=True, ea_font="黑体")
        B.set_run(q.add_run("　　%d 页 PPT" % len(pg)), size=9, color=GREY)

    total_img = 0
    for n in ns:
        pages = meta[str(n)]["pages"]
        paras = load_cap(n)
        res = align(pages, paras)
        ins = {}
        for k, j in enumerate(res):
            ins.setdefault(j, []).append(k)

        B.h1_page(doc, "第 %02d 讲　%s" % (n, TITLES[n]),
                  "课堂实录 %d 段 · 幻灯片 %d 页" % (len(paras), len(pages)))

        for j, text in enumerate(paras):
            if j in ins:
                for k in ins[j]:
                    pg = pages[k]
                    ip = doc.add_paragraph()
                    ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    ip.paragraph_format.space_before = Pt(6)
                    ip.paragraph_format.space_after = Pt(2)
                    ip.paragraph_format.keep_with_next = True
                    ip.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    ip.add_run().add_picture(pg["img"], width=Cm(15.2))
                    cap = doc.add_paragraph()
                    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cap.paragraph_format.space_after = Pt(7)
                    B.set_run(cap.add_run("PPT 第 %d / %d 页" % (pg["i"], len(pages))),
                              size=8, color=GREY)
                    total_img += 1
            tp = doc.add_paragraph()
            tp.paragraph_format.space_after = Pt(5)
            tp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            tp.paragraph_format.first_line_indent = Pt(16)
            B.set_run(tp.add_run(text), size=10, color=SOFT)
        print(f"L{n:02d} 完成：{len(paras)} 段 / {len(pages)} 页")

    path = f"{OUT}/GSE2026-逐字稿与PPT-A4.docx"
    doc.save(path)
    print("保存", path, "图片", total_img, "张")

if __name__ == "__main__":
    import sys
    ns = [int(x) for x in sys.argv[1:]] or list(range(1, 14))
    main(ns)
