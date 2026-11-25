# -*- coding: utf-8 -*-
"""精读标注版：在精读本基础上重排版 + 三层标注。
输出 dist/print/GSE2026-精读标注版-A4.docx
"""
import os, re, json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import build_docx as B
from overview import VIDEO, OVERVIEW

OUT = "dist/print"
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x88, 0x88, 0x88)
ACCENT = RGBColor(0x0F, 0x5E, 0x5A)
AMBER = RGBColor(0xB4, 0x53, 0x09)
SOFT = RGBColor(0x5C, 0x63, 0x6B)

KEYWORDS = {
    1: ["意图 · 规格 · 实现", "Agent 与 harness", "修改的局部性"],
    2: ["上下文工程", "注意力预算", "把「完成」写清楚"],
    3: ["快照", "原子变更", "worktree 分房间"],
    4: ["变化的身份", "先分后合 / 先上锁", "从 MVP 起步"],
    5: ["软件危机", "设计契约", "图与模型"],
    6: ["需求泥潭", "事件溯源", "CQRS 与 DDD"],
    7: ["尊重「小脑袋」", "设计解空间", "计算正确性"],
    8: ["Let it fail", "状态迁移与门禁", "Agent Native"],
    9: ["150 行起步", "Everything is plugin", "Session = Event"],
    10: ["理解版本迁移", "经得起时间", "蒸馏自己"],
    11: ["fault → failure", "测试金字塔", "差分与模糊"],
    12: ["不变式", "证明助手", "携带证明的软件"],
    13: ["保留与遗忘", "概率分布采样", "三个正确性"],
}

# 段级标注规则
RE_CAUTION = re.compile(r"(最容易混淆|常见误区|容易误|不要把它|误以为|并不是说|不等于|容易把|恰恰是错|陷阱|并不能|不代表|不一定|别把)")
RE_INSIGHT = re.compile(r"(真正稀缺|本质上|反过来|恰恰|核心矛盾|不是.{0,14}而是|唯一的|关键不在|决定性|只会|根本|真正的)")
# 句级加粗规则：判断句 / 结论句
RE_CORE = re.compile(r"(不是.{0,14}而是|真正的|关键是|判据是|本质|唯一|必须|只会|恰恰|意味着|说明|证明|换句话说|也就是说|问题在于|核心|不能|无法)")


def underline_run(run, color="0F5E5A"):
    rPr = run._element.get_or_add_rPr()
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    u.set(qn("w:color"), color)
    rPr.append(u)


def space_run(run, val=40):
    rPr = run._element.get_or_add_rPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:val"), str(val))
    rPr.append(sp)


def label_para(doc, text, color, bg=None, left_bar=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(4)
    if left_bar:
        B.para_border(p, "left", "0F5E5A" if color == ACCENT else "B45309", 18, 8)
        pf.left_indent = Pt(12)
    if bg:
        B.shade(p._p.get_or_add_pPr(), bg)
    set_r = B.set_run(p.add_run(text), size=7.8, bold=True, color=color, ea_font="黑体")
    return p


def kv_row(doc, k, v):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(2)
    pf.left_indent = Pt(12)
    B.set_run(p.add_run(k + "　"), size=8, color=GREY)
    B.set_run(p.add_run(v), size=9, color=SOFT)


def sentence_split(t):
    parts = re.split(r"(?<=[。！？])", t)
    return [x for x in parts if x]


def annot_body(doc, runs, stat):
    """段落渲染：先判定段级标注，再对纯文本段做句级加粗。"""
    text = "".join(r[0] for r in runs)
    plain = len(runs) == 1 and not runs[0][1]
    kind = None
    if RE_CAUTION.search(text):
        kind = "caution"
    elif RE_INSIGHT.search(text):
        kind = "insight"

    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Pt(21)
    pf.space_after = Pt(2.5)
    if kind == "caution":
        B.para_border(p, "left", "B45309", 12, 7)
        pf.left_indent = Pt(10)
        B.set_run(p.add_run("⚠ 易混　"), size=7.5, bold=True, color=AMBER, ea_font="黑体")
        stat["caution"] += 1
    elif kind == "insight":
        B.para_border(p, "left", "0F5E5A", 12, 7)
        pf.left_indent = Pt(10)
        B.set_run(p.add_run("◆ 判断　"), size=7.5, bold=True, color=ACCENT, ea_font="黑体")
        stat["insight"] += 1

    if plain:
        marked = False
        for s in sentence_split(text):
            hit = (not marked) and 18 <= len(s) <= 62 and bool(RE_CORE.search(s))
            r = p.add_run(s)
            B.set_run(r, size=10.5, bold=bool(hit), color=INK)
            if hit:
                underline_run(r)
                marked = True
                stat["bold"] += 1
    else:
        for txt, f in runs:
            r = p.add_run(txt)
            B.set_run(r, size=10.5, bold=f.get("b", False), italic=f.get("i", False),
                      mono=f.get("code", False),
                      color=(RGBColor(0x0A, 0x50, 0x8C) if f.get("link") else INK))
            if f.get("code"):
                r.font.size = Pt(9.5)
    return p


def render_annotated(doc, blocks, stat, lec_n=1):
    sec_no = 0
    for b in blocks:
        k = b["kind"]
        if k == "h2":
            sec_no += 1
            txt = "".join(r[0] for r in b["runs"]).strip()
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.space_before = Pt(13)
            pf.space_after = Pt(4)
            pf.keep_with_next = True
            pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            pf.line_spacing = Pt(19)
            r = p.add_run("%d.%d" % (lec_n, sec_no))
            B.set_run(r, size=9, bold=True, color=RGBColor(0x9A, 0xA5, 0xA3))
            space_run(r, 30)
            B.set_run(p.add_run("  "), size=9)
            B.set_run(p.add_run(txt), size=13, bold=True, ea_font="黑体", color=ACCENT)
            B.para_border(p, "bottom", "D8E4E1", 4, 2)
        elif k in ("h3", "h4"):
            B.h3(doc, "".join(r[0] for r in b["runs"]).strip())
        elif k == "p":
            annot_body(doc, b["runs"], stat)
        elif k == "li":
            B.bullet(doc, b["runs"])
        elif k == "pre":
            B.code_block(doc, b["runs"][0][0] if b["runs"] else "")
        elif k == "quote":
            B.quote_block(doc, b["runs"])
        elif k == "table":
            B.table_block(doc, b["rows"])


def jingdu_notes(blocks):
    """从精读里抽「最容易混淆的边界」+「阅读路线」，作为每讲补记。"""
    out, grab, buf = [], False, []
    for b in blocks:
        if b["kind"] in ("h2", "h3"):
            t = "".join(r[0] for r in b["runs"]).strip()
            if re.search(r"最容易混淆|边界|阅读路线|本课在回答", t):
                grab = True
                buf = [("H", t)]
                continue
            elif grab:
                if buf:
                    out.append(buf)
                grab, buf = False, []
        elif grab and b["kind"] in ("p", "li"):
            t = "".join(r[0] for r in b["runs"]).strip()
            if 8 < len(t) < 220:
                buf.append(("P", t))
    if buf:
        out.append(buf)
    return out[:4]


def cover_better(doc):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    B.set_run(p.add_run("NANJING UNIVERSITY · 2026 FALL"), size=8, color=GREY)
    space_run(p.add_run(""), 80)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(50)
    B.set_run(p.add_run("生成式软件工程"), size=32, bold=True, ea_font="黑体", color=INK)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(18)
    B.set_run(p.add_run("精读标注版"), size=14, ea_font="楷体", color=ACCENT)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(24)
    B.para_border(p, "top", "0F5E5A", 10, 8)
    for t in ["主讲　蒋炎岩（南京大学计算机学院副教授、博导）",
              "内容　第 1–13 讲讲义全文 + 逐讲要点 + 三层标注 + 精读补记",
              "排版　A4 双面 · 宋体五号 · 行距 15pt",
              "整理　2026-11-24　|　讲义 CC BY-NC 4.0"]:
        q = doc.add_paragraph()
        q.paragraph_format.space_after = Pt(4)
        B.set_run(q.add_run(t), size=9.5, color=SOFT)
    # 标注说明
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(26)
    p.paragraph_format.space_after = Pt(6)
    B.set_run(p.add_run("怎么读这些标注"), size=9, bold=True, ea_font="黑体", color=GREY)
    rows = [("◆ 判断", "左侧青线：反直觉论断、作者的核心判断，值得停下来想"),
            ("⚠ 易混", "左侧橙线：容易混淆或误读的地方，读快了会栽跟头"),
            ("加粗", "句内加粗：作者本人强调的判断句，多为一句可摘的结论"),
            ("补记", "每讲末尾：从第三方精读里摘的辨析与阅读路线")]
    for k, v in rows:
        q = doc.add_paragraph()
        q.paragraph_format.space_after = Pt(2)
        q.paragraph_format.left_indent = Pt(6)
        B.set_run(q.add_run(k + "　"), size=8.5, bold=True, color=ACCENT if "判断" in k else AMBER)
        B.set_run(q.add_run(v), size=8.5, color=SOFT)


def main():
    data = B.load_data()
    doc = Document()
    B.base_style(doc)
    B.setup_section(doc, "生成式软件工程 · 2026 秋", "精读标注版")
    cover_better(doc)

    # 目录（带关键词）
    doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(14)
    B.set_run(p.add_run("目　录"), size=16, bold=True, ea_font="黑体", color=INK)
    for L in data:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(6)
        pf.space_after = Pt(1)
        pf.keep_with_next = True
        B.set_run(p.add_run("第 %02d 讲" % L["n"]), size=8.5, bold=True, color=ACCENT)
        B.set_run(p.add_run("　" + L["title"]), size=10.5, bold=True, ea_font="黑体")
        q = doc.add_paragraph()
        q.paragraph_format.left_indent = Pt(16)
        q.paragraph_format.space_after = Pt(4)
        B.set_run(q.add_run(" / ".join(KEYWORDS[L["n"]])), size=8, color=GREY)

    stat = {"insight": 0, "caution": 0, "bold": 0}
    for L in data:
        ov = L["ov"]
        B.h1_page(doc, "第 %02d 讲　%s" % (L["n"], L["title"]),
                  "%s · %d 分钟 · %s 播放 · %s" % (L["date"], L["dur"], B.fmt_views(L["views"]), L["bvid"]))

        # 关键词条
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        for i, kw in enumerate(KEYWORDS[L["n"]]):
            if i:
                B.set_run(p.add_run("　·　"), size=8, color=RGBColor(0xC0, 0xC0, 0xC0))
            B.set_run(p.add_run(kw), size=8.5, color=ACCENT)

        # 导读卡
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(2)
        pf.space_after = Pt(5)
        pf.left_indent = Pt(11)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        B.shade(p._p.get_or_add_pPr(), "EEF5F3")
        B.para_border(p, "left", "0F5E5A", 20, 9)
        B.set_run(p.add_run(ov["one"]), size=10.5, ea_font="楷体", color=RGBColor(0x11, 0x3A, 0x37))

        q = doc.add_paragraph()
        q.paragraph_format.left_indent = Pt(11)
        q.paragraph_format.space_after = Pt(6)
        q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        B.set_run(q.add_run("问　"), size=9, bold=True, color=AMBER)
        B.set_run(q.add_run(ov["q"]), size=9.5, color=RGBColor(0x33, 0x33, 0x33))

        for i, (t, d) in enumerate(ov["points"], 1):
            pp = doc.add_paragraph()
            pf = pp.paragraph_format
            pf.left_indent = Pt(20)
            pf.first_line_indent = Pt(-20)
            pf.space_after = Pt(2)
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            B.set_run(pp.add_run("%d " % i), size=8.5, bold=True, color=ACCENT)
            B.set_run(pp.add_run("　" + t + "　"), size=9.5, bold=True, ea_font="黑体")
            B.set_run(pp.add_run(d), size=9, color=RGBColor(0x3A, 0x3A, 0x3A))

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(4)
        B.para_border(p, "bottom", "DDD8CC", 6, 1)
        tag = doc.add_paragraph()
        tag.paragraph_format.space_after = Pt(1)
        B.set_run(tag.add_run("讲义原文"), size=8.5, bold=True, ea_font="黑体", color=ACCENT)

        render_annotated(doc, L["blocks"], stat, L["n"])

        notes = jingdu_notes(L["jingdu"])
        if notes:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(5)
            B.para_border(p, "top", "D8E4E1", 6, 8)
            B.set_run(p.add_run("精读补记"), size=9.5, bold=True, ea_font="黑体", color=ACCENT)
            B.set_run(p.add_run("　摘自「软工星球」精读，非官方"), size=7.8, color=GREY)
            for group in notes[:3]:
                for typ, t in group:
                    if typ == "H":
                        q = doc.add_paragraph()
                        q.paragraph_format.space_before = Pt(4)
                        q.paragraph_format.space_after = Pt(2)
                        q.paragraph_format.keep_with_next = True
                        B.set_run(q.add_run("· " + t), size=9, bold=True, ea_font="黑体", color=SOFT)
                    else:
                        q = doc.add_paragraph()
                        q.paragraph_format.left_indent = Pt(18)
                        q.paragraph_format.first_line_indent = Pt(-9)
                        q.paragraph_format.space_after = Pt(2)
                        q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        B.set_run(q.add_run("· "), size=8.8, color=RGBColor(0x9A, 0x9A, 0x9A))
                        B.set_run(q.add_run(t), size=8.8, color=RGBColor(0x44, 0x44, 0x44))

    path = f"{OUT}/GSE2026-精读标注版-A4.docx"
    doc.save(path)
    print("保存", path)
    print("标注统计：判断段", stat["insight"], "｜易混段", stat["caution"], "｜加粗句", stat["bold"])


if __name__ == "__main__":
    main()
