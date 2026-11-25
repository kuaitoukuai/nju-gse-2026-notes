import urllib.parse, urllib.request, os, json

BASE = "https://raw.githubusercontent.com/LINJIANG12/video2book-courses/main/"
PREFIX = "计算机/软件工程/南京大学-生成式软件工程/"
files = [
    ("textbooks/模块01_欢迎来到未来：AI 时代为什么仍然需要软件工程_精读全书.md", "v2b-模块01.md"),
    ("textbooks/模块02_提示词工程：与 AI 协作的可控做法_精读全书.md", "v2b-模块02.md"),
    ("textbooks/模块03_软件仓库管理：从版本控制到工程化协作_精读全书.md", "v2b-模块03.md"),
    ("textbooks/模块04_软件工程的来龙去脉_精读全书.md", "v2b-模块04.md"),
    ("textbooks/模块05_需求与架构：把方向和复杂度钉死_精读全书.md", "v2b-模块05.md"),
    ("notes/笔记01_欢迎来到未来AI时代为什么仍然需要软件工程_笔记.md", "v2b-笔记01.md"),
    ("notes/笔记02_提示词工程与AI协作的可控做法_笔记.md", "v2b-笔记02.md"),
    ("notes/笔记03_软件仓库管理从版本控制到工程化协作_笔记.md", "v2b-笔记03.md"),
    ("notes/笔记04_软件工程的来龙去脉_笔记.md", "v2b-笔记04.md"),
    ("notes/笔记05_需求与架构把方向和复杂度钉死_笔记.md", "v2b-笔记05.md"),
]
os.makedirs("source/v2b", exist_ok=True)
for rel, out in files:
    url = BASE + urllib.parse.quote(PREFIX + rel)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
        open("source/v2b/" + out, "wb").write(data)
        print(f"OK {out} {len(data)//1024}KB")
    except Exception as e:
        print(f"FAIL {out} {e}")
