# -*- coding: utf-8 -*-
"""精读标注版 + PPT：在标注版讲义的小节后插入对应幻灯片。
输出 dist/print/GSE2026-精读标注版与PPT-A4.docx
"""
import os, re, json, html as H
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
import build_docx as B
import build_annotated as A
from overview import OVERVIEW

GREY = RGBColor(0x77, 0x77, 0x77)
ACCENT = RGBColor(0x0F, 0x5E, 0x5A)

def bigrams(s):
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", s)
    return set(s[i:i + 2] for i in range(len(s) - 1))

def sim(a, b):
    A_, B_ = bigrams(a), bigrams(b)
    if not A_ or not B_:
        return 0.0
    return len(A_ & B_) / ((len(A_) ** 0.5) * (len(B_) ** 0.5))

def split_by_h2(blocks):
    groups, cur = [], {"head": None, "blocks": []}
    for b in blocks:
        if b["kind"] == "h2":
            if cur["head"] or cur["blocks"]:
                groups.append(cur)
            cur = {"head": b, "blocks": []}
        else:
            cur["blocks"].append(b)
    groups.append(cur)
    return groups

def match(pages, groups):
    """每页 PPT 匹配到一个讲义小节（单调）。返回 {sec_idx: [page,...]}"""
    secs = []
    for g in groups:
        t = "".join(r[0] for r in g["head"]["runs"]).strip() if g["head"] else ""
        body = " ".join("".join(r[0] for r in b["runs"]) for b in g["blocks"] if b["kind"] == "p")
        secs.append(t + " " + body[:300])
    N, M = len(pages), len(secs)
    S = [[sim(p["text"], s) for s in secs] for p in pages]
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
    out = {}
    for k, sec in enumerate(res):
        out.setdefault(sec, []).append(pages[k])
    return out

def add_slide(doc, pg, total):
    ip = doc.add_paragraph()
    ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ip.paragraph_format.space_before = Pt(8)
    ip.paragraph_format.space_after = Pt(2)
    ip.paragraph_format.keep_with_next = True
    ip.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    ip.add_run().add_picture(pg["img"], width=Cm(15.2))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(9)
    B.set_run(cap.add_run("课件 第 %d / %d 页" % (pg["i"], total)), size=8, color=GREY)

def main():
    meta = json.load(open("build/slides_pages.json", encoding="utf-8"))
    data = B.load_data()
    doc = Document()
    B.base_style(doc)
    B.setup_section(doc, "生成式软件工程 · 2026 秋", "精读标注版 × PPT")
    A.cover_better(doc)

    # 目录
    doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(14)
    B.set_run(p.add_run("目　录"), size=16, bold=True, ea_font="黑体", color=B.INK)
    for L in data:
        q = doc.add_paragraph()
        q.paragraph_format.space_before = Pt(6)
        q.paragraph_format.space_after = Pt(1)
        q.paragraph_format.keep_with_next = True
        B.set_run(q.add_run("第 %02d 讲" % L["n"]), size=8.5, bold=True, color=ACCENT)
        B.set_run(q.add_run("　" + L["title"]), size=10.5, bold=True, ea_font="黑体")
        r = doc.add_paragraph()
        r.paragraph_format.left_indent = Pt(16)
        r.paragraph_format.space_after = Pt(4)
        B.set_run(r.add_run(" / ".join(A.KEYWORDS[L["n"]])), size=8, color=GREY)

    stat = {"insight": 0, "caution": 0, "bold": 0}
    total_img = 0
    for L in data:
        n = L["n"]
        pages = meta[str(n)]["pages"]
        groups = split_by_h2(L["blocks"])
        smap = match(pages, groups)
        ov = OVERVIEW[n]
        B.h1_page(doc, "第 %02d 讲　%s" % (n, L["title"]),
                  "%s · %d 分钟 · %d 页课件" % (L["date"], L["dur"], len(pages)))

        # 关键词 + 导读卡
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        for i, kw in enumerate(A.KEYWORDS[n]):
            if i:
                B.set_run(p.add_run("　·　"), size=8, color=RGBColor(0xC0, 0xC0, 0xC0))
            B.set_run(p.add_run(kw), size=8.5, color=ACCENT)

        q = doc.add_paragraph()
        qf = q.paragraph_format
        qf.space_before = Pt(2)
        qf.space_after = Pt(5)
        qf.left_indent = Pt(11)
        qf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        B.shade(q._p.get_or_add_pPr(), "EEF5F3")
        B.para_border(q, "left", "0F5E5A", 20, 9)
        B.set_run(q.add_run(ov["one"]), size=10.5, ea_font="楷体", color=RGBColor(0x11, 0x3A, 0x37))

        # 分组渲染
        for gi, g in enumerate(groups):
            if g["head"]:
                txt = "".join(r[0] for r in g["head"]["runs"]).strip()
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.space_before = Pt(13)
                pf.space_after = Pt(4)
                pf.keep_with_next = True
                B.set_run(p.add_run("%d.%d" % (n, gi)), size=9, bold=True,
                          color=RGBColor(0x9A, 0xA5, 0xA3))
                B.set_run(p.add_run("  " + txt), size=13, bold=True, ea_font="黑体", color=ACCENT)
                B.para_border(p, "bottom", "D8E4E1", 4, 2)
            for b in g["blocks"]:
                k = b["kind"]
                if k == "p":
                    A.annot_body(doc, b["runs"], stat)
                elif k in ("h3", "h4"):
                    B.h3(doc, "".join(r[0] for r in b["runs"]).strip())
                elif k == "li":
                    B.bullet(doc, b["runs"])
                elif k == "pre":
                    B.code_block(doc, b["runs"][0][0] if b["runs"] else "")
                elif k == "quote":
                    B.quote_block(doc, b["runs"])
                elif k == "table":
                    B.table_block(doc, b["rows"])
            # 插该节对应的课件
            for pg in smap.get(gi, []):
                add_slide(doc, pg, len(pages))
                total_img += 1
        print(f"L{n:02d}：{len(groups)} 节，插 {sum(len(v) for v in smap.values())} 页")

    path = "dist/print/GSE2026-精读标注版与PPT-A4.docx"
    doc.save(path)
    print("保存", path, "图片", total_img, "张")

if __name__ == "__main__":
    main()
