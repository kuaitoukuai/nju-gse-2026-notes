# -*- coding: utf-8 -*-
"""把幻灯片逐页截图为 JPEG，并提取每页文字，供对齐使用。"""
import os, json, pathlib, sys
from playwright.sync_api import sync_playwright

OUT = "build/slides_png"
os.makedirs(OUT, exist_ok=True)

def shoot(lects):
    meta = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        for n in lects:
            src = pathlib.Path(f"source/slides/slides{n}.html").resolve().as_uri()
            pg.goto(src, wait_until="networkidle")
            pg.wait_for_timeout(800)
            total = int(pg.inner_text("#total"))
            # 关掉动画，便于稳定截图
            pg.evaluate("document.querySelectorAll('.slide').forEach(s=>s.classList.add('no-anim'))")
            pages = []
            for i in range(total):
                pg.evaluate(f"show({i})")
                pg.wait_for_timeout(90)
                el = pg.locator(".slide.active")
                path = f"{OUT}/L{n:02d}-{i+1:03d}.jpg"
                el.screenshot(path=path, type="jpeg", quality=72)
                txt = el.inner_text().replace("\n", " ").strip()
                pages.append({"i": i + 1, "text": txt, "img": path})
            meta[n] = {"total": total, "pages": pages}
            print(f"L{n:02d}: {total} 页")
        b.close()
    old = {}
    if os.path.exists("build/slides_pages.json"):
        old = json.load(open("build/slides_pages.json", encoding="utf-8"))
    old.update(meta)
    json.dump(old, open("build/slides_pages.json", "w", encoding="utf-8"), ensure_ascii=False)
    return old

if __name__ == "__main__":
    ns = [int(x) for x in sys.argv[1:]] or [1]
    shoot(ns)
