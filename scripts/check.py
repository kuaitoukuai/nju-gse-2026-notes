import re, glob
tot = 0
for f in sorted(glob.glob("build/lectures/*.html")):
    s = open(f, encoding="utf-8").read()
    n = len(re.findall(r"\$[^$]{1,80}\$", s))
    img = len(re.findall(r"<img", s))
    pre = len(re.findall(r"<pre", s))
    tbl = len(re.findall(r"<table", s))
    if n or img or pre or tbl:
        print(f, "math=", n, "img=", img, "pre=", pre, "table=", tbl)
    tot += n
print("公式总数", tot)
