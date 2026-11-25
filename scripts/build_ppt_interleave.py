# -*- coding: utf-8 -*-
"""讲义/PPT × 逐字稿 图文对照版：逐页 PPT 截图按讲述位置插入逐字稿。
输出 dist/图文对照/index.html + images/
"""
import re, html as H, json, os, shutil

def bigrams(s):
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", s)
    return set(s[i:i+2] for i in range(len(s) - 1))

def sim(a, b):
    A, B = bigrams(a), bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / ((len(A) ** 0.5) * (len(B) ** 0.5))

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
            res[i - 1] = (j - 1, S[i - 1][j - 1])
            i -= 1
        j -= 1
    # 未匹配的页沿用前一个位置
    last = 0
    for k in range(N):
        if res[k]:
            last = res[k][0]
        else:
            res[k] = (last, 0.0)
    return res

def main():
    meta = json.load(open("build/slides_pages.json", encoding="utf-8"))
    OUT = "dist/图文对照"
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT + "/images", exist_ok=True)

    blocks = []
    total_imgs = 0
    for n in range(1, 14):
        pages = meta[str(n)]["pages"]
        paras = load_cap(n)
        res = align(pages, paras)
        ins = {}
        for k, r in enumerate(res):
            ins.setdefault(r[0], []).append(k)
        # 复制图片
        for p in pages:
            src = p["img"]
            dst = OUT + "/images/" + os.path.basename(src)
            if not os.path.exists(dst):
                shutil.copy(src, dst)
            p["web"] = "images/" + os.path.basename(src)
            total_imgs += 1
        blocks.append({"n": n, "pages": pages, "paras": paras, "ins": ins})
        print(f"L{n:02d}: {len(pages)} 页 / {len(paras)} 段")

    style = """
:root{--bg:#fbfaf7;--panel:#fff;--ink:#1e2328;--ink2:#545b63;--ink3:#8b9098;
--line:#e7e3d8;--accent:#0f766e;--amber:#b45309}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
font-size:16px;line-height:1.9;-webkit-font-smoothing:antialiased}
.top{position:sticky;top:0;z-index:20;background:rgba(251,250,247,.94);backdrop-filter:blur(12px);
border-bottom:1px solid var(--line);padding:10px 22px;display:flex;justify-content:space-between;
font-size:12.5px;color:var(--ink3)}
.top b{color:var(--accent)}
.wrap{max-width:780px;margin:0 auto;padding:36px 22px 110px}
h1{font-size:1.9rem;margin:0 0 .15em}
.meta{color:var(--ink3);font-size:12.5px;margin-bottom:30px;line-height:1.8}
h2{font-size:1.12rem;margin:2.8em 0 .9em;padding:9px 0 9px 14px;border-left:4px solid var(--accent);
background:linear-gradient(90deg,#e9f4f1,transparent);line-height:1.5}
.talk{font-size:15px;color:#3b4249;margin:0 0 .8em;text-align:justify}
.talk::before{content:"讲";display:inline-block;font-size:9.5px;font-weight:700;color:#b9b3a5;
border:1px solid #ddd8cb;border-radius:3px;padding:0 4px;margin-right:7px;vertical-align:2px}
.slide{margin:18px 0 22px;background:var(--panel);border:1px solid var(--line);border-radius:12px;
overflow:hidden;box-shadow:0 2px 10px rgba(30,35,40,.05)}
.slide .cap{display:flex;justify-content:space-between;align-items:center;padding:8px 14px;
font-size:11px;color:var(--ink3);border-bottom:1px solid var(--line);background:#faf9f5}
.slide .cap b{color:var(--accent);font-weight:600}
.slide img{display:block;width:100%;height:auto;cursor:zoom-in}
.toc{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;margin:22px 0 38px}
.toc a{display:block;padding:9px 12px;background:var(--panel);border:1px solid var(--line);
border-radius:8px;color:var(--ink);text-decoration:none;font-size:12.5px}
.toc a:hover{border-color:var(--accent);color:var(--accent)}
.toc a small{display:block;color:var(--ink3);font-size:10px;margin-top:2px}
#lb{position:fixed;inset:0;background:rgba(15,20,25,.92);display:none;z-index:99;
align-items:center;justify-content:center;padding:24px;cursor:zoom-out}
#lb.on{display:flex}
#lb img{max-width:96vw;max-height:92vh;border-radius:8px;box-shadow:0 10px 40px rgba(0,0,0,.5)}
@media print{.top{display:none}.wrap{max-width:100%}.slide{page-break-inside:avoid}}
"""
    toc = "".join(f'<a href="#l{d["n"]}"><b>第 {d["n"]:02d} 讲</b> {len(d["pages"])} 页 PPT'
                  f'<small>{len(d["paras"])} 段实录</small></a>' for d in blocks)
    titles = {1:"欢迎来到未来",2:"提示词与上下文工程",3:"版本管理",4:"版本管理 (2)",
              5:"软件工程的来龙去脉",6:"需求和架构 (1)",7:"需求和架构 (2)",
              8:"Agent Native 开发",9:"DeepSeek Harness",10:"软件的演化",
              11:"软件质量保障 (1)",12:"软件质量保障 (2)",13:"软件分析工具"}
    body = []
    for d in blocks:
        n = d["n"]
        body.append(f'<h2 id="l{n}">第 {n:02d} 讲　{H.escape(titles[n])}</h2>')
        for j, p in enumerate(d["paras"]):
            if j in d["ins"]:
                for k in d["ins"][j]:
                    pg = d["pages"][k]
                    body.append(
                        f'<div class="slide"><div class="cap"><span>PPT · <b>第 {pg["i"]} / {len(d["pages"])} 页</b></span>'
                        f'<span>对应实录第 {j+1} 段</span></div>'
                        f'<img src="{pg["web"]}" alt="第 {n} 讲 第 {pg["i"]} 页" loading="lazy"></div>')
            body.append(f'<p class="talk">{H.escape(p)}</p>')

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PPT × 逐字稿 图文对照 · 生成式软件工程 2026</title>
<style>{style}</style></head><body>
<div class="top"><span><b>PPT × 逐字稿 图文对照</b>　南京大学《生成式软件工程》2026 秋</span>
<span>点击图片可放大</span></div>
<div class="wrap">
<h1>PPT × 逐字稿 图文对照</h1>
<div class="meta">13 讲、{sum(len(d["pages"]) for d in blocks)} 页幻灯片按讲述位置插入到课堂实录中。灰字是老师原话，图下方标注该页 PPT 的页码。第 14 讲课件已发布但暂无逐字稿，未纳入。第 14 讲课件已发布但暂无逐字稿，未纳入。</div>
<div class="toc">{toc}</div>
{''.join(body)}
</div>
<div id="lb"><img id="lbimg" src="" alt=""></div>
<script>
document.querySelectorAll('.slide img').forEach(function(im){{
  im.addEventListener('click', function(){{
    document.getElementById('lbimg').src = im.src;
    document.getElementById('lb').classList.add('on');
  }});
}});
document.getElementById('lb').addEventListener('click', function(){{ this.classList.remove('on'); }});
document.addEventListener('keydown', function(e){{ if(e.key==='Escape') document.getElementById('lb').classList.remove('on'); }});
</script>
</body></html>"""
    open(OUT + "/index.html", "w", encoding="utf-8").write(html)
    print("HTML", round(len(html) / 1024), "KB；图片", total_imgs, "张")

if __name__ == "__main__":
    main()
