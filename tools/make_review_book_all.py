# 把 tools/review-*.md 全部合成一本《申论批改合集》。
#
# 用法：python tools/make_review_book_all.py
# 输出：docs/print/批改合集.docx|pdf
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import make_review_docx as R  # noqa: E402
from docx.shared import Cm  # noqa: E402

KITS = [
    ("review-2026-10-26.md", "练习 9 · 贯彻执行（工作方案）· 9 / 25", "餐饮浪费 · 专项行动工作方案（450 字）"),
    ("review-2026-10-27.md", "练习 10 · 综合分析（评价型）· 10 / 20", "社区食堂两种观点评析（300 字）"),
    ("review-2026-10-28.md", "练习 11 · 综合分析（评价型·第二练）· 10 / 20", "「首违不罚」两种观点评析（300 字）"),
    ("review-2026-10-30.md", "练习 12 · 归纳概括（问题型）· 8 / 15", "12345 热线运行中的主要问题（250 字）"),
    ("review-2026-11-01.md", "练习 13 · 整卷摸底 · 24 / 100", "B 县老城更新：概括／评析／对策／提纲"),
    ("review-2026-11-02.md", "练习 14 · 回炉卷 · 29 / 80", "B 县老城更新：同材料重做三题"),
    ("review-2026-11-03.md", "练习 15 · 强化期混合练 · 22 / 35", "Q 县「村 BA」：概括＋解释型分析"),
    ("review-2026-11-05.md", "练习 16 · 回炉第二遍 · 31 / 35", "Q 县「村 BA」：概括第二遍＋解释型换问法"),
]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    doc = R.Document()
    R.set_style(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = Cm(1.6)
    sec.bottom_margin = Cm(1.5)
    sec.left_margin = Cm(1.7)
    sec.right_margin = Cm(1.5)

    hp = sec.header.paragraphs[0]
    hp.text = ""
    hr = hp.add_run("申论 · 批改合集 · 练习 9–15（2026-10-26 至 2026-11-03）")
    hr.font.size = R.Pt(8.5)
    hr.font.name = R.FONT
    hr._element.rPr.rFonts.set(R.qn("w:eastAsia"), R.FONT)

    # 封面
    R.para(doc, "申论批改合集", size=26, bold=True, space_after=6)
    R.para(doc, "练习 9 – 15 ｜ 七次真实作答 ｜ 批注 ＋ 标准答案", size=12, color=(0x55, 0x55, 0x55), space_after=14)
    R.para(doc, "每一节的结构都一样：", size=10.5, bold=True, space_after=3)
    for i, t in enumerate(
        [
            "题目原文（材料在该次的打印版或今日任务存档里）",
            "你的作答原文（批注对象）",
            "得分表（哪一项扣分、扣在什么上）",
            "逐条对照（采分点／你的答案／判定）",
            "漏点（含出处）",
            "升格版 —— 标准答案（可直接背结构，不要背字）",
            "带走的一个动作",
        ],
        1,
    ):
        R.para(doc, f"{i}. {t}", size=10, space_after=1)

    R.para(doc, "怎么用（每次 15 分钟）", size=10.5, bold=True, space_after=3)
    R.para(doc, "① 先只看题目，自己在纸上写第一句；② 翻到这一节的升格版，只比第一句；③ 再读「漏点」；④ 抄下「一个动作」。七节读完，你会得到七条动作，重复最多的那三条就是你现在的短板。", size=9.5, color=(0x44, 0x44, 0x44))

    R.para(doc, "目录", size=10.5, bold=True, space_after=3)
    for i, (_, title, sub) in enumerate(KITS, 1):
        R.para(doc, f"{i}. {R.plain(title)}　—　{R.plain(sub)}", size=9.5, space_after=1)

    # 正文
    for fn, title, sub in KITS:
        src = HERE / fn
        if not src.exists():
            print(f"跳过（缺少）{fn}")
            continue
        doc.add_page_break()
        R.para(doc, R.plain(title), size=15, bold=True, space_after=2)
        R.para(doc, R.plain(sub), size=9, color=(0x66, 0x66, 0x66), space_after=8)
        data = R.parse(src)
        R.emit_blocks(doc, data["block"])

    out = R.OUT
    out.mkdir(parents=True, exist_ok=True)
    docx = out / "批改合集.docx"
    doc.save(str(docx))
    print(f"docx → {docx}")
    pdf = out / "批改合集.pdf"
    if R.to_pdf(docx, pdf):
        print(f"pdf  → {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
