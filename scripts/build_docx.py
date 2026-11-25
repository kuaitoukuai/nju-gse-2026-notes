# -*- coding: utf-8 -*-
"""把课程 HTML 转成紧凑排版的 Word 文档。
输出：
  GSE2026-速览手册-A4.docx   13 讲各 1-2 页，快速通读
  GSE2026-精读本-A4.docx     速览卡 + 讲义全文，带节要点
  GSE2026-细读本-上册/下册   讲义全文 + 逐讲精读全文
"""
import os, re, json, html as H
from html.parser import HTMLParser
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from overview import VIDEO, OVERVIEW

OUT = "dist/print"
os.makedirs(OUT, exist_ok=True)
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x77, 0x77, 0x77)
ACCENT = RGBColor(0x0F, 0x5E, 0x5A)

# ---------------- HTML -> blocks ----------------
BLOCK_OPEN = {"p", "h1", "h2", "h3", "h4", "li", "blockquote", "pre", "tr"}


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.cur = None
        self.inline = []
        self.in_pre = False
        self.pre_buf = []
        self.table = None
        self.row = None

    def _flush(self):
        if self.cur is not None:
            txt = "".join(r[0] for r in self.cur["runs"]).strip()
            if txt:
                self.blocks.append(self.cur)
            self.cur = None

    def _start(self, kind):
        self._flush()
        self.cur = {"kind": kind, "runs": []}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("strong", "b"):
            self.inline.append("b")
        elif tag in ("em", "i"):
            self.inline.append("i")
        elif tag == "code":
            self.inline.append("code")
        elif tag == "a":
            self.inline.append("a")
        elif tag in ("h1", "h2", "h3", "h4"):
            self._start(tag)
        elif tag == "p":
            if not self.in_pre and self.cur is None:
                self._start("p")
        elif tag == "li":
            self._start("li")
        elif tag == "blockquote":
            self._start("quote")
        elif tag == "pre":
            self._flush()
            self.in_pre = True
            self.pre_buf = []
        elif tag == "table":
            self._flush()
            self.table = {"kind": "table", "rows": []}
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.row.append([[], tag == "th"])

    def handle_endtag(self, tag):
        if tag in ("strong", "b", "em", "i", "code", "a"):
            if self.inline:
                self.inline.pop()
        elif tag in ("h1", "h2", "h3", "h4", "p", "li", "blockquote"):
            self._flush()
        elif tag == "pre":
            self.in_pre = False
            txt = "".join(self.pre_buf).strip("\n")
            if txt.strip():
                self.blocks.append({"kind": "pre", "runs": [(txt, {})]})
            self.pre_buf = []
        elif tag == "table" and self.table is not None:
            if self.table["rows"]:
                self.blocks.append(self.table)
            self.table = None
        elif tag == "tr" and self.table is not None and self.row is not None:
            if any("".join(r[0] for r in c[0]).strip() for c in self.row):
                self.table["rows"].append(self.row)
            self.row = None
        elif tag in ("td", "th") and self.row is not None and self.row:
            pass

    def handle_data(self, data):
        if self.in_pre:
            self.pre_buf.append(data)
            return
        if self.row is not None and self.row:
            cell = self.row[-1]
            fmt = {}
            if "b" in self.inline: fmt["b"] = True
            if "code" in self.inline: fmt["code"] = True
            cell[0].append((data, fmt))
            return
        if self.cur is None:
            if not data.strip():
                return
            self._start("p")
        fmt = {}
        if "b" in self.inline: fmt["b"] = True
        if "i" in self.inline: fmt["i"] = True
        if "code" in self.inline: fmt["code"] = True
        if "a" in self.inline: fmt["link"] = True
        self.cur["runs"].append((data, fmt))


def parse_html(path):
    s = open(path, encoding="utf-8").read()
    p = Extractor()
    p.feed(s)
    p._flush()
    out = []
    for b in p.blocks:
        if b["kind"] == "p":
            txt = "".join(r[0] for r in b["runs"]).strip()
            tight = re.sub(r"\s+", "", txt)
            # 丢掉概念图边缘被拆散的碎词（如「查　看　原　图」）
            if len(tight) <= 6 and not re.search(r"[。，、：；！？]", tight):
                continue
        out.append(b)
    return out


# ---------------- docx helpers ----------------
def set_run(run, size=10.5, bold=False, italic=False, color=None,
            ascii_font="Times New Roman", ea_font="宋体", mono=False):
    if mono:
        ascii_font = ea_font = "Consolas"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.name = ascii_font
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rPr.append(rf)
    rf.set(qn("w:ascii"), ascii_font)
    rf.set(qn("w:hAnsi"), ascii_font)
    rf.set(qn("w:eastAsia"), ea_font)
    if color is not None:
        run.font.color.rgb = color
    return run


def shade(el, color):
    pPr = el.get_or_add_pPr() if hasattr(el, "get_or_add_pPr") else el
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), color)
    pPr.append(sh)


def para_border(p, side="left", color="0F5E5A", sz=12, space=6):
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:" + side)
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), str(sz))
    b.set(qn("w:space"), str(space))
    b.set(qn("w:color"), color)
    pbdr.append(b)
    pPr.append(pbdr)


def note_line(p, color="C8C3B6"):
    """笔记横线：同时设 bottom 与 between，避免相邻段落边框被 Word 合并。"""
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    for side in ("between", "bottom"):
        b = OxmlElement("w:" + side)
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "1")
        b.set(qn("w:color"), color)
        pbdr.append(b)
    pPr.append(pbdr)


def add_page_field(p, size=8.5, color=GREY):
    r = p.add_run()
    set_run(r, size=size, color=color)
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    r._r.append(f1); r._r.append(it); r._r.append(f2)


def setup_section(doc, header_left, header_right):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(1.75), Cm(1.65)
    sec.left_margin, sec.right_margin = Cm(1.9), Cm(1.9)
    sec.header_distance, sec.footer_distance = Cm(0.9), Cm(0.9)

    hp = sec.header.paragraphs[0]
    hp.text = ""
    hp.paragraph_format.space_after = Pt(2)
    # 清掉 Header 样式自带的 center/right 制表位，只保留右对齐到版心右边界
    pPr = hp._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    for pos in ("4680", "9360"):
        t = OxmlElement("w:tab")
        t.set(qn("w:val"), "clear")
        t.set(qn("w:pos"), pos)
        tabs.append(t)
    t = OxmlElement("w:tab")
    t.set(qn("w:val"), "right")
    t.set(qn("w:pos"), "9752")
    tabs.append(t)
    pPr.append(tabs)
    r = hp.add_run(header_left + "\t" + header_right)
    set_run(r, size=8, color=GREY)
    para_border(hp, "bottom", "CCCCCC", 4, 2)

    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("— ")
    set_run(r, size=8.5, color=GREY)
    add_page_field(fp)
    r = fp.add_run(" —")
    set_run(r, size=8.5, color=GREY)


def base_style(doc):
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(10.5)
    rPr = st.element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rPr.append(rf)
    rf.set(qn("w:eastAsia"), "宋体")
    pf = st.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(15)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2.5)


def h1_page(doc, text, kicker=None):
    doc.add_page_break()
    if kicker:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        set_run(p.add_run(kicker), size=8.5, color=GREY)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(30)
    set_run(p.add_run(text), size=21, bold=True, ea_font="黑体", color=INK)
    return p


def h2(doc, text, first=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(2 if first else 11)
    pf.space_after = Pt(3.5)
    pf.keep_with_next = True
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(18)
    set_run(p.add_run(text), size=13, bold=True, ea_font="黑体", color=ACCENT)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(7)
    pf.space_after = Pt(2)
    pf.keep_with_next = True
    set_run(p.add_run(text), size=11, bold=True, ea_font="黑体", color=INK)
    return p


def body(doc, runs, indent=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if indent:
        pf.first_line_indent = Pt(21)
    for txt, f in runs:
        r = p.add_run(txt)
        set_run(r, size=10.5, bold=f.get("b", False), italic=f.get("i", False),
                mono=f.get("code", False), color=(RGBColor(0x0A,0x50,0x8C) if f.get("link") else INK))
        if f.get("code"):
            r.font.size = Pt(9.5)
    return p


def bullet(doc, runs):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Pt(18)
    pf.first_line_indent = Pt(-9)
    pf.space_after = Pt(1.5)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_run(p.add_run("· "), size=10.5, color=ACCENT)
    for txt, f in runs:
        r = p.add_run(txt)
        set_run(r, size=10.5, bold=f.get("b", False), mono=f.get("code", False),
                color=(RGBColor(0x0A,0x50,0x8C) if f.get("link") else INK))
    return p


def code_block(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Pt(10)
    pf.space_before = Pt(3)
    pf.space_after = Pt(5)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(11.5)
    shade(p._p.get_or_add_pPr(), "F2F2F0")
    for i, line in enumerate(text.split("\n")):
        r = p.add_run(line)
        set_run(r, size=8.5, mono=True, color=RGBColor(0x22, 0x22, 0x22))
        if i < len(text.split("\n")) - 1:
            r.add_break()
    return p


def quote_block(doc, runs):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Pt(16)
    pf.right_indent = Pt(8)
    pf.space_before = Pt(4)
    pf.space_after = Pt(4)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    para_border(p, "left", "B45309", 14, 8)
    for txt, f in runs:
        r = p.add_run(txt)
        set_run(r, size=10, bold=f.get("b", False), ea_font="楷体", mono=f.get("code", False),
                color=RGBColor(0x44, 0x40, 0x38))
    return p


def table_block(doc, rows):
    ncol = max(len(r) for r in rows)
    t = doc.add_table(rows=len(rows), cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(rows):
        for ci in range(ncol):
            cell = t.cell(ri, ci)
            cell.paragraphs[0].paragraph_format.space_after = Pt(0)
            cell.paragraphs[0].paragraph_format.line_spacing = Pt(12)
            if ci < len(row):
                runs, is_head = row[ci]
                for txt, f in runs:
                    r = cell.paragraphs[0].add_run(txt)
                    set_run(r, size=8.5, bold=(is_head or f.get("b")), mono=f.get("code"))
                if is_head:
                    shade(cell._tc.get_or_add_tcPr(), "EFF3F2")
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def render(doc, blocks):
    for b in blocks:
        k = b["kind"]
        if k == "h1":
            h2(doc, "".join(r[0] for r in b["runs"]).strip(), first=True)
        elif k == "h2":
            h2(doc, "".join(r[0] for r in b["runs"]).strip())
        elif k in ("h3", "h4"):
            h3(doc, "".join(r[0] for r in b["runs"]).strip())
        elif k == "p":
            body(doc, b["runs"])
        elif k == "li":
            bullet(doc, b["runs"])
        elif k == "pre":
            code_block(doc, b["runs"][0][0] if b["runs"] else "")
        elif k == "quote":
            quote_block(doc, b["runs"])
        elif k == "table":
            table_block(doc, b["rows"])


def cover(doc, title, subtitle, meta_lines):
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    set_run(p.add_run("南京大学 2026 年秋季课程"), size=11, ea_font="黑体", color=GREY)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = Pt(46)
    set_run(p.add_run(title), size=30, bold=True, ea_font="黑体", color=INK)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(28)
    set_run(p.add_run(subtitle), size=13, ea_font="楷体", color=ACCENT)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(40)
    para_border(p, "top", "0F5E5A", 8, 10)
    for line in meta_lines:
        q = doc.add_paragraph()
        q.paragraph_format.space_after = Pt(3)
        set_run(q.add_run(line), size=9.5, color=GREY)


def toc_page(doc, lectures, with_sections=True, title="目 录"):
    doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(12)
    set_run(p.add_run(title), size=16, bold=True, ea_font="黑体", color=INK)
    for L in lectures:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(5)
        pf.space_after = Pt(1.5)
        pf.keep_with_next = True
        set_run(p.add_run("第 %02d 讲　%s" % (L["n"], L["title"])), size=10.5, bold=True, ea_font="黑体")
        set_run(p.add_run("　　%s · %d 分钟" % (L["date"], L["dur"])), size=9, color=GREY)
        if with_sections:
            txt = "　".join("%d.%d %s" % (L["n"], i + 1, s) for i, s in enumerate(L["sec_titles"]))
            q = doc.add_paragraph()
            q.paragraph_format.left_indent = Pt(14)
            q.paragraph_format.space_after = Pt(3)
            q.paragraph_format.line_spacing = Pt(13)
            set_run(q.add_run(txt), size=8.5, color=GREY)


# ---------------- data ----------------
def load_data():
    meta = json.load(open("build/heads.json", encoding="utf-8"))
    L = []
    for m in meta:
        n = m["n"]
        bvid, date, dur, views = VIDEO[n]
        blocks = parse_html(f"build/lectures/lect{n}.html")
        secs = [b for b in blocks if b["kind"] == "h2"]
        title = next((b for b in blocks if b["kind"] == "h1"), None)
        t = "".join(r[0] for r in title["runs"]).strip() if title else f"第 {n} 讲"
        blocks = [b for b in blocks if b["kind"] != "h1"]
        L.append({
            "n": n, "title": t, "bvid": bvid, "date": date, "dur": dur, "views": views,
            "blocks": blocks,
            "sec_titles": ["".join(r[0] for r in b["runs"]).strip() for b in secs],
            "jingdu": (parse_html(f"build/jingdu/{n}.html") if os.path.exists(f"build/jingdu/{n}.html") else []),
            "ov": OVERVIEW[n],
        })
    return L


def fmt_views(v):
    return ("%.1f 万" % (v / 10000)).replace(".0 万", " 万") if v >= 10000 else str(v)


# ---------------- 1. 速览手册 ----------------
def build_quick(L):
    doc = Document()
    base_style(doc)
    setup_section(doc, "生成式软件工程 · 2026 秋", "速览手册")
    cover(doc, "生成式软件工程", "速览手册 · 13 讲骨架与要点",
          ["主讲：蒋炎岩（南京大学计算机学院副教授、博导）",
           "课程：2026 年秋季 · 每周二 10:00–12:00 · B 站「绿导师原谅你了」",
           "整理：2026-11-24　|　讲义 CC BY-NC 4.0",
           "用途：每讲 1–2 页，适合打印后快速通读、课前预习与复试复习"])
    toc_page(doc, L, with_sections=False, title="讲次一览")

    for Lx in L:
        ov = Lx["ov"]
        h1_page(doc, "第 %02d 讲　%s" % (Lx["n"], Lx["title"]),
                "%s · %d 分钟 · %s 播放 · %s" % (Lx["date"], Lx["dur"], fmt_views(Lx["views"]), Lx["bvid"]))
        # 一句话
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(8)
        pf.space_after = Pt(7)
        pf.left_indent = Pt(10)
        pf.right_indent = Pt(6)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        shade(p._p.get_or_add_pPr(), "EEF5F3")
        para_border(p, "left", "0F5E5A", 16, 8)
        set_run(p.add_run(ov["one"]), size=11.5, ea_font="楷体", color=RGBColor(0x11, 0x3A, 0x37))
        # 核心问题
        q = doc.add_paragraph()
        qf = q.paragraph_format
        qf.space_after = Pt(9)
        qf.left_indent = Pt(10)
        qf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        set_run(q.add_run("本讲要回答："), size=9.5, bold=True, color=RGBColor(0xB4, 0x53, 0x09))
        set_run(q.add_run(ov["q"]), size=10.5, color=RGBColor(0x33, 0x33, 0x33))
        # 要点
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
        set_run(p.add_run("核心要点"), size=9.5, bold=True, ea_font="黑体", color=GREY)
        for i, (t, d) in enumerate(ov["points"], 1):
            pp = doc.add_paragraph()
            pf = pp.paragraph_format
            pf.left_indent = Pt(21)
            pf.first_line_indent = Pt(-21)
            pf.space_after = Pt(4.5)
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            set_run(pp.add_run("%d " % i), size=9.5, bold=True, color=ACCENT)
            set_run(pp.add_run("　" + t + "　"), size=10.5, bold=True, ea_font="黑体")
            set_run(pp.add_run(d), size=10, color=RGBColor(0x33, 0x33, 0x33))
        # 结构
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        set_run(p.add_run("讲义结构（共 %d 节）" % len(Lx["sec_titles"])), size=9.5, bold=True, ea_font="黑体", color=GREY)
        for i, s in enumerate(Lx["sec_titles"], 1):
            q = doc.add_paragraph()
            qf = q.paragraph_format
            qf.left_indent = Pt(16)
            qf.space_after = Pt(1)
            qf.line_spacing = Pt(14.5)
            set_run(q.add_run("%d.%d　" % (Lx["n"], i)), size=9, color=ACCENT)
            set_run(q.add_run(s), size=9.5, color=RGBColor(0x33, 0x33, 0x33))
        # 笔记区：按本讲实际占用行数估算剩余空间，最多 4 条
        used = 2.6 + 1.4 + 2.0 + 1.6 + 1.0
        for t, d in ov["points"]:
            used += max(1.0, (len(t) + len(d) + 8) / 37.0) + 0.35
        used += 1.0 + len(Lx["sec_titles"]) * 0.95
        nlines = int(max(0, min(4, (45 - used) // 3)))
        if nlines:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            set_run(p.add_run("笔　记"), size=8.5, color=RGBColor(0xB5, 0xB2, 0xAA))
            for _ in range(nlines):
                q = doc.add_paragraph()
                q.paragraph_format.space_before = Pt(0)
                q.paragraph_format.space_after = Pt(21)
                note_line(q)
    doc.save(f"{OUT}/GSE2026-速览手册-A4.docx")
    print("速览手册 OK")


# ---------------- 2. 精读本 ----------------
def build_study(L):
    doc = Document()
    base_style(doc)
    setup_section(doc, "生成式软件工程 · 2026 秋", "精读本")
    cover(doc, "生成式软件工程", "精读本 · 讲义全文 + 每讲要点",
          ["主讲：蒋炎岩（南京大学计算机学院副教授、博导）",
           "收录：第 1–13 讲讲义全文，137 节，约 10.9 万字",
           "每讲前置「一句话 / 核心问题 / 核心要点」，正文为官方讲义原文",
           "整理：2026-11-24　|　CC BY-NC 4.0"])
    toc_page(doc, L, with_sections=True)

    for Lx in L:
        ov = Lx["ov"]
        h1_page(doc, "第 %02d 讲　%s" % (Lx["n"], Lx["title"]),
                "%s · %d 分钟 · %s 播放" % (Lx["date"], Lx["dur"], fmt_views(Lx["views"])))
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(6)
        pf.space_after = Pt(4)
        pf.left_indent = Pt(10)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        shade(p._p.get_or_add_pPr(), "EEF5F3")
        para_border(p, "left", "0F5E5A", 16, 8)
        set_run(p.add_run(ov["one"]), size=10.5, ea_font="楷体", color=RGBColor(0x11, 0x3A, 0x37))
        q = doc.add_paragraph()
        q.paragraph_format.left_indent = Pt(10)
        q.paragraph_format.space_after = Pt(6)
        q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        set_run(q.add_run("问："), size=9, bold=True, color=RGBColor(0xB4, 0x53, 0x09))
        set_run(q.add_run(ov["q"]), size=9.5, color=RGBColor(0x33, 0x33, 0x33))
        for i, (t, d) in enumerate(ov["points"], 1):
            pp = doc.add_paragraph()
            pf = pp.paragraph_format
            pf.left_indent = Pt(20)
            pf.first_line_indent = Pt(-20)
            pf.space_after = Pt(2)
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            set_run(pp.add_run("%d " % i), size=8.5, bold=True, color=ACCENT)
            set_run(pp.add_run("　" + t + "　"), size=9.5, bold=True, ea_font="黑体")
            set_run(pp.add_run(d), size=9, color=RGBColor(0x3A, 0x3A, 0x3A))
        # 分隔
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        para_border(p, "bottom", "DDD8CC", 6, 1)
        tag = doc.add_paragraph()
        tag.paragraph_format.space_after = Pt(1)
        set_run(tag.add_run("讲义原文"), size=8.5, bold=True, ea_font="黑体", color=ACCENT)
        render(doc, Lx["blocks"])
    doc.save(f"{OUT}/GSE2026-精读本-A4.docx")
    print("精读本 OK")


# ---------------- 3. 细读本 ----------------
def build_deep(L, part, fname):
    doc = Document()
    base_style(doc)
    setup_section(doc, "生成式软件工程 · 2026 秋", "细读本 · " + ("上册" if part == 1 else "下册"))
    cover(doc, "生成式软件工程", "细读本 · %s（第 %d–%d 讲）" % ("上册" if part == 1 else "下册", L[0]["n"], L[-1]["n"]),
          ["主讲：蒋炎岩（南京大学计算机学院副教授、博导）",
           "本册内容：讲义原文 + 逐讲精读（软工星球，非官方）",
           "对照读法：先读讲义原文，再看精读如何拆解案例与边界",
           "整理：2026-11-24　|　CC BY-NC 4.0"])
    toc_page(doc, L, with_sections=False, title="本册讲次")

    for Lx in L:
        h1_page(doc, "第 %02d 讲　%s" % (Lx["n"], Lx["title"]),
                "%s · %d 分钟 · %s 播放" % (Lx["date"], Lx["dur"], fmt_views(Lx["views"])))
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        set_run(p.add_run("一、讲义原文"), size=10, bold=True, ea_font="黑体", color=ACCENT)
        render(doc, Lx["blocks"])

        if Lx["jingdu"]:
            doc.add_page_break()
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            set_run(p.add_run("二、逐讲精读（软工星球 · 非官方）"), size=10, bold=True, ea_font="黑体", color=ACCENT)
            q = doc.add_paragraph()
            q.paragraph_format.space_after = Pt(6)
            set_run(q.add_run("本文为第三方学习笔记，由 AI 辅助整理，概念图已省略；表述与讲义不一致时以讲义为准。"),
                    size=8.5, color=GREY)
            render(doc, Lx["jingdu"])
    doc.save(f"{OUT}/{fname}")
    print(fname, "OK")


if __name__ == "__main__":
    data = load_data()
    build_quick(data)
    build_study(data)
    build_deep([x for x in data if x["n"] <= 7], 1, "GSE2026-细读本-上册-A4.docx")
    build_deep([x for x in data if x["n"] >= 8], 2, "GSE2026-细读本-下册-A4.docx")
