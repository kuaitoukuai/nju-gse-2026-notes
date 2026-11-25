# -*- coding: utf-8 -*-
"""极简 Markdown -> HTML，用于把 Argon 重写版正文注入阅读器。
支持：标题、段落、粗斜体、行内码、代码围栏、引用、有序/无序列表、表格、图片占位、行内公式。"""
import re, html as H


def _inline(t):
    t = H.escape(t)
    # 图片 -> 占位
    t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
               lambda m: '<span class="md-fig">［图］' + (m.group(1) or m.group(2)) + "</span>", t)
    # 链接
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               lambda m: '<a href="' + m.group(2) + '" target="_blank" rel="noopener">' + m.group(1) + "</a>", t)
    # 行内码
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    # 粗体 / 斜体
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    # 行内公式
    t = re.sub(r"\$([^$\n]{1,120})\$", r'<span class="math">\1</span>', t)
    return t


def md2html(md, drop_first_h1=True):
    lines = md.split("\n")
    out, para, list_tag = [], [], None
    in_code, code_buf, dropped = False, [], False

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para = []

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append("</%s>" % list_tag)
            list_tag = None

    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.rstrip()

        # 代码围栏
        if s.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + H.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf, in_code = [], False
            else:
                flush_para(); close_list()
                in_code = True
                code_buf = []
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # 空行
        if not s.strip():
            flush_para(); close_list()
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush_para(); close_list()
            lvl = len(m.group(1))
            txt = _inline(m.group(2).strip())
            if lvl == 1:
                if drop_first_h1 and not dropped:
                    dropped = True
                    i += 1
                    continue
                lvl = 2
            out.append("<h%d>%s</h%d>" % (lvl, txt, lvl))
            i += 1
            continue

        # 表格：本行以 | 开头且下一行是分隔行
        if s.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:\-\|]+\|\s*$", lines[i + 1]):
            flush_para(); close_list()
            header = [c.strip() for c in s.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join("<th>" + _inline(c) + "</th>" for c in header)
            tb = "".join("<tr>" + "".join("<td>" + _inline(c) + "</td>" for c in r) + "</tr>" for r in rows)
            out.append("<table><thead><tr>" + th + "</tr></thead><tbody>" + tb + "</tbody></table>")
            continue

        # 分隔线
        if re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", s):
            flush_para(); close_list()
            out.append("<hr>")
            i += 1
            continue

        # 引用
        if s.lstrip().startswith(">"):
            flush_para(); close_list()
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = []
            for x in buf:
                if x.strip():
                    inner.append("<p>" + _inline(x.strip()) + "</p>")
            out.append("<blockquote>" + "".join(inner) + "</blockquote>")
            continue

        # 列表
        m_ul = re.match(r"^\s*[-*+]\s+(.*)$", s)
        m_ol = re.match(r"^\s*\d+[.)]\s+(.*)$", s)
        if m_ul or m_ol:
            flush_para()
            tag = "ul" if m_ul else "ol"
            if list_tag != tag:
                close_list()
                out.append("<%s>" % tag)
                list_tag = tag
            out.append("<li>" + _inline((m_ul or m_ol).group(1)) + "</li>")
            i += 1
            continue

        # 普通段落
        close_list()
        para.append(s.strip())
        i += 1

    if in_code and code_buf:
        out.append("<pre><code>" + H.escape("\n".join(code_buf)) + "</code></pre>")
    flush_para(); close_list()
    return "\n".join(out)
