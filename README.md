# 南京大学《生成式软件工程》2026 秋 · 课程资料整理

> 一门课的讲义、课件、逐字稿与多个版本的阅读/打印文档。
> 课程：南京大学计算机学院《生成式软件工程》（Generative Software Engineering, GSE），2026 年秋季学期
> 主讲：蒋炎岩（B 站「绿导师原谅你了」）
> 本仓库是**第三方学习整理**，非官方仓库，不代表课程作者与南京大学。

---

## 这是什么

把这门课散落在**课程 wiki、B 站、GitHub、微信公众号**的材料收拢到一处，做成可以按不同方式读的版本：

| 想做什么 | 打开 |
|---|---|
| 边读边搜，五种读法切换 | [`web/index.html`](web/index.html)（单文件，离线可用） |
| 看课堂原话怎么讲、讲义怎么写 | [`web/讲义逐字稿对照.html`](web/讲义逐字稿对照.html) |
| 直接看课件 | [`slides/index.html`](slides/index.html)（14 讲 + 3 个 Lab） |
| 找某句话在原文哪一节 | [`docs/总目录.md`](docs/总目录.md) |
| 通读讲义 | [`docs/讲义全文.md`](docs/讲义全文.md) |
| 想知道 AI 写的代码怎么查 | [`docs/AI代码检查手册.md`](docs/AI代码检查手册.md) |
| 搞清楚资料都是哪来的 | [`docs/资料来源与整理说明.md`](docs/资料来源与整理说明.md) |

---

## 内容

### 阅读器（`web/index.html`，2.8 MB，单文件）

五种读法，左上角切换：

| 读法 | 内容 | 覆盖 |
|---|---|---|
| 速览 | 每讲一句话主旨 + 核心问题 + 5–7 条要点 | 13 讲 |
| 讲义原文 | 官方讲义全文 | 13 讲 / 137 节 / 10.9 万字 |
| 逐讲精读 | 公众号「软工星球」的非官方精读 | 13 篇 / 13.0 万字 |
| 视频逐字稿 | 人工校对的课堂实录 | 13 讲 / 27.6 万字 |
| 系统重写 | Argon 重写的教科书版 | 1–8 讲 / 35.3 万字 |

左栏三级目录（讲 → 讲义节 → 段首要点），顶部跨五源全文搜索，`/` 聚焦、`↑↓` 选择、`Enter` 跳转。

### 对照版（`web/讲义逐字稿对照.html`）

以课堂实录为骨架，把讲义原文插到讲述该主题的位置。绿框是讲义原文，灰字是老师原话，每块标了对应强度（正常 / 对应较弱 / 课堂讲述较简略）。

### 课件（`slides/`）

- `slides-01.html` … `slides-14.html`：课堂实际放映的幻灯片，方向键翻页，F11 全屏
- `lab-1.html` … `lab-3.html`：三个实验的完整要求
- `assets/`：MathJax + highlight.js，已本地化，断网也能渲染公式与代码

### 文档（`docs/`）

- `总目录.md`：三级目录 + 13 讲速览，可导入 Obsidian / Notion
- `讲义全文.md`：13 讲讲义合并，`#` 讲 / `##` 节
- `AI代码检查手册.md`：从课程里提炼的「怎么用外部证据检查 AI 写的代码」，含检查清单与 prompt 模板
- `资料来源与整理说明.md`：全部来源的地址、类型、许可、复现步骤

### 脚本（`scripts/`）

从抓取到生成的完整链路，仅依赖 Python 标准库 + python-docx + playwright + pymupdf：

```bash
python extract_lectures.py      # 讲义正文提取
python extract_aux.py           # 精读 + 字幕
python build_sections.py        # 按 H2 切节
python build_site.py            # 生成阅读器与 Markdown
python build_slides.py          # 课件本地化 + 索引
python build_interleave.py      # 讲义 × 逐字稿对照
python shoot_slides.py 1 2 3    # PPT 逐页截图（Playwright）
python build_ppt_interleave.py  # PPT × 逐字稿图文对照
```

---

## 资料来源

| 来源 | 地址 | 类型 | 许可 |
|---|---|---|---|
| 课程主页 | https://jyywiki.cn/GSE/2026/ | 讲义、课件、实验 | CC BY-NC 4.0 |
| B 站 | [合集 sid=8942017](https://space.bilibili.com/202224425/lists?sid=8942017) | 14 讲课堂录像 | CC BY-NC 4.0 |
| 逐字稿 | [NinZeige/NJU-2026-GSE-Captions](https://github.com/NinZeige/NJU-2026-GSE-Captions) | 人工校对口稿 27.6 万字 | CC BY-NC 4.0 |
| 逐讲精读 | [软工星球](https://seplanet.cn/courses/gse-2026/) | 13 篇非官方精读 | 遵循原课许可 |
| 系统重写 | [hqhq1025/ai-course-notes](https://github.com/hqhq1025/ai-course-notes) | Argon 重写版 445 页 | CC BY-NC 4.0 衍生 |
| 模块整编 | [LINJIANG12/video2book-courses](https://github.com/LINJIANG12/video2book-courses) | 5 册模块书 + 笔记 | 二次整理 |
| 教案 | [LvGitHub-9/lesson-plans](https://github.com/LvGitHub-9/lesson-plans) | 1–6 讲教案 | CC BY-NC 4.0 衍生 |

**引用优先级**：讲义原文 > 录像 / 逐字稿 > 精读 > AI 重写。二手材料里的事实（版本号、论文名、数字）请回查一手来源。

---

## 使用

全部离线可用，不需要联网，也不需要安装任何东西：

```bash
git clone git@github.com:kuaitoukuai/nju-gse-2026-notes.git
# 或
git clone git@gitee.com:smallpencil/nju-gse-2026-notes.git
```

双击 `web/index.html` 即可。

---

## 许可

- **文档与整理内容**：CC BY-NC 4.0，署名 + 非商业。详见 [LICENSE](LICENSE)。
- **整理脚本**：MIT。
- **原课程讲义、幻灯片、实验**：© 蒋炎岩 / 南京大学，CC BY-NC 4.0。
- 各第三方材料的署名见 [NOTICE.md](NOTICE.md)。

**不得用于商业用途。** 若原权利方对本仓库有异议，请开 issue，会立即调整或下架。

---

## 已知边界

- 只收**第 1–13 讲**的讲义。第 14 讲《软件发布与运维》已有录像和课件，但 `lect14.md` 尚未公开，因此阅读器不含这一讲；课件在 `slides/slides-14.html` 可看。
- 逐讲精读里的「概念关系图」是内联 SVG，为控制体积已转为占位文字，其余正文完整。
- Argon 重写版是**重写**而非原文，措辞与老师原话不同，引用请回查讲义。
- 本仓库不含 426 张课件截图（约 30 MB）与 Word 打印版（约 48 MB），它们体积较大，通过 Release 分发。
