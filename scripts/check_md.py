import re, glob

for f in sorted(glob.glob("source/argon/lecture*-notes.md")):
    s = open(f, encoding="utf-8").read()
    inline_math = len(re.findall(r"\$[^$\n]{1,80}\$", s))
    block_math = s.count("$$")
    fences = s.count("```")
    quotes = len(re.findall(r"^>", s, re.M))
    bullets = len(re.findall(r"^- ", s, re.M))
    ordered = len(re.findall(r"^\d+\. ", s, re.M))
    codes = len(re.findall(r"`[^`\n]+`", s))
    links = len(re.findall(r"\]\(", s))
    print(f"{f}: 行内公式={inline_math} 块公式={block_math} 代码围栏={fences} 引用={quotes} 无序={bullets} 有序={ordered} 行内码={codes} 链接={links}")
