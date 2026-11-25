# -*- coding: utf-8 -*-
"""讲义 × 逐字稿 对照版：以课堂实录为骨架，在对应位置插入讲义原文。
输出 dist/GSE2026-讲义逐字稿对照.html
"""
import re, html as H, json, os

def bigrams(s):
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", s)
    return set(s[i:i+2] for i in range(len(s) - 1))

def sim(a, b):
    A, B = bigrams(a), bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / ((len(A) ** 0.5) * (len(B) ** 0.5))

def load_lecture(n):
    s = open(f"build/lectures/lect{n}.html", encoding="utf-8").read()
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", s)
    title = H.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else f"第 {n} 讲"
    parts = re.split(r"(<h2[^>]*>[\s\S]*?</h2>)", s)
    secs = []
    for i in range(1, len(parts), 2):
        t = H.unescape(re.sub(r"<[^>]+>", "", parts[i])).strip()
        raw = parts[i + 1]
        # 保留 HTML 供展示
        disp = raw.strip()
        disp = re.sub(r"</p>", "</p>\n", disp)
        body_text = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()
        secs.append({"title": t, "html": disp, "text": body_text})
    return title, secs

def load_captions(n):
    s = open(f"build/captions/{n}.html", encoding="utf-8").read()
    ps = re.findall(r"<p>([\s\S]*?)</p>", s)
    out = []
    for p in ps:
        t = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", p))).strip()
        if len(t) > 15:
            out.append(t)
    return out

def align(secs, paras):
    """单调对齐：dp[i][j] = 前 i 节匹配到前 j 段的最大总分。"""
    N, M = len(secs), len(paras)
    S = [[0.0] * M for _ in range(N)]
    for i, sec in enumerate(secs):
        q = sec["title"] + " " + sec["text"][:320]
        for j, p in enumerate(paras):
            S[i][j] = sim(q, p)
    NEG = -1e9
    dp = [[NEG] * (M + 1) for _ in range(N + 1)]
    back = [[0] * (M + 1) for _ in range(N + 1)]
    for j in range(M + 1):
        dp[0][j] = 0
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            # 跳过第 j 段
            best, arg = dp[i][j - 1], 0
            # 第 i 节匹配第 j 段
            cand = dp[i - 1][j - 1] + S[i - 1][j - 1] - 0.02  # 轻微惩罚，避免过度匹配
            if cand > best:
                best, arg = cand, 1
            dp[i][j] = best
            back[i][j] = arg
    # 回溯
    res = [None] * N
    i, j = N, M
    while i > 0 and j > 0:
        if back[i][j] == 1:
            res[i - 1] = (j - 1, S[i - 1][j - 1])
            i -= 1
        j -= 1
    return res

def main():
    data = []
    stats = []
    for n in range(1, 14):
        title, secs = load_lecture(n)
        paras = load_captions(n)
        res = align(secs, paras)
        matched = sum(1 for r in res if r and r[1] >= 0.09)
        stats.append((n, len(secs), matched))
        data.append({"n": n, "title": title, "secs": secs, "paras": paras, "res": res})
        print(f"第{n:02d}讲 {title}: {len(secs)} 节，已对齐 {matched}")

    # 生成 HTML
    style = """
:root{--bg:#fbfaf7;--panel:#fff;--ink:#1e2328;--ink2:#545b63;--ink3:#8b9098;
--line:#e7e3d8;--accent:#0f766e;--soft:#e9f4f1;--amber:#b45309}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
font-size:16px;line-height:1.9;-webkit-font-smoothing:antialiased}
.top{position:sticky;top:0;z-index:20;background:rgba(251,250,247,.93);backdrop-filter:blur(12px);
border-bottom:1px solid var(--line);padding:10px 22px;display:flex;justify-content:space-between;
font-size:12.5px;color:var(--ink3)}
.top b{color:var(--accent)}
.wrap{max-width:760px;margin:0 auto;padding:38px 24px 110px}
h1{font-size:1.9rem;margin:0 0 .1em}
.meta{color:var(--ink3);font-size:12.5px;margin-bottom:34px}
h2{font-size:1.15rem;margin:2.6em 0 .8em;padding:8px 0 8px 14px;border-left:4px solid var(--accent);
background:linear-gradient(90deg,var(--soft),transparent);line-height:1.5}
.talk{font-size:15px;color:#3b4249;margin:0 0 .75em;text-align:justify}
.talk::before{content:"讲";display:inline-block;font-size:9.5px;font-weight:700;color:#b9b3a5;
border:1px solid #ddd8cb;border-radius:3px;padding:0 4px;margin-right:7px;vertical-align:2px}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:0 10px 10px 0;padding:14px 18px 6px;margin:16px 0 20px}
.note h4{margin:0 0 .5em;font-size:12.5px;font-weight:700;color:var(--accent);letter-spacing:.02em}
.note h4 span{color:var(--ink3);font-weight:400;margin-left:6px;letter-spacing:0}
.note p{font-size:14.5px;line-height:1.85;margin:0 0 .7em;color:#2a3138;text-align:justify}
.note code{background:var(--soft);padding:1px 5px;border-radius:4px;font-size:.88em}
.note pre{background:#1d232b;color:#e6edf3;padding:12px 14px;border-radius:8px;overflow:auto;font-size:12.5px}
.note pre code{background:none;padding:0}
.note ul,.note ol{padding-left:1.3em;margin:.5em 0 .8em}
.note li{font-size:14.5px;margin:.2em 0}
.tail{margin-top:26px;padding:14px 18px;background:#f3f1ea;border-radius:10px;font-size:12.5px;color:var(--ink2);line-height:1.8}
.toc{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin:24px 0 40px}
.toc a{display:block;padding:9px 12px;background:var(--panel);border:1px solid var(--line);
border-radius:8px;color:var(--ink);text-decoration:none;font-size:13px}
.toc a:hover{border-color:var(--accent);color:var(--accent)}
.toc a small{display:block;color:var(--ink3);font-size:10.5px;margin-top:2px}
@media print{.top{display:none}.wrap{max-width:100%}.note{page-break-inside:avoid}}
"""
    # 目录
    toc = "".join(
        f'<a href="#l{d["n"]}"><b>第 {d["n"]:02d} 讲</b> {H.escape(d["title"])}'
        f'<small>{d["n"] and len(d["paras"])} 段实录</small></a>' for d in data)

    body = []
    for d in data:
        body.append(f'<h1 id="l{d["n"]}">第 {d["n"]:02d} 讲　{H.escape(d["title"])}</h1>')
        body.append(f'<div class="meta">课堂实录 {len(d["paras"])} 段 ｜ 讲义 {len(d["secs"])} 节 ｜ 绿色块为讲义原文，插入在讲述到该主题的位置</div>')
        # 按段落遍历，命中的插入
        ins = {}
        weak = 0
        for idx, r in enumerate(d["res"]):
            if r:
                ins.setdefault(r[0], []).append((idx, r[1]))
                if r[1] < 0.09:
                    weak += 1
        for j, p in enumerate(d["paras"]):
            if j in ins:
                for idx, score in sorted(ins[j]):
                    sec = d["secs"][idx]
                    if score >= 0.10:
                        tag = f'对应实录第 {j+1} 段'
                    elif score >= 0.06:
                        tag = f'对应实录第 {j+1} 段 · 对应较弱'
                    else:
                        tag = f'对应实录第 {j+1} 段 · 课堂讲述较简略'
                    note = (f'<div class="note"><h4>讲义原文 · {idx+1}. {H.escape(sec["title"])}'
                            f'<span>{tag}</span></h4>{sec["html"]}</div>')
                    body.append(note)
            body.append(f'<p class="talk">{H.escape(p)}</p>')
        if weak:
            body.append(f'<div class="tail">本讲有 {weak} 个讲义小节与实录对应较弱或课堂仅简略带过，'
                        f'已按讲述顺序就近插入，标题后已标注。</div>')

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>讲义 × 逐字稿 对照版 · 生成式软件工程 2026</title>
<style>{style}</style></head><body>
<div class="top"><span><b>讲义 × 逐字稿 对照版</b>　南京大学《生成式软件工程》2026 秋</span>
<span>灰色「讲」为课堂实录，绿色块为讲义原文</span></div>
<div class="wrap">
<h1>讲义 × 逐字稿 对照版</h1>
<div class="meta">以课堂实录为骨架，把讲义对应小节插到讲述该主题的位置。绿色块是讲义原文，灰色文字是老师的口头讲述。</div>
<div class="toc">{toc}</div>
{''.join(body)}
</div></body></html>"""
    open("dist/GSE2026-讲义逐字稿对照.html", "w", encoding="utf-8").write(html)
    print("已生成 dist/GSE2026-讲义逐字稿对照.html", len(html)//1024, "KB")

if __name__ == "__main__":
    main()
