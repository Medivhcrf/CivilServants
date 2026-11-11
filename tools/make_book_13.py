# -*- coding: utf-8 -*-
"""把 Day 1–13 合成一本彩色的《申论全程复习册》：

每天一节，顺序固定：
    题目 → 你的作答 → 得分（色块）→ 逐条对照（✅●绿 △●琥珀 ✗●红）→ 漏点（红）→ 升格版（绿）→ 一个动作（蓝）

用法：
    python tools/make_book_13.py
输出：
    docs/print/全程复习册.docx / .pdf
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import make_handout as H
import make_review_docx as R

ROOT = H.ROOT
OUT = H.OUT
FONT = H.FONT

# ---------------- 颜色 ----------------
INK = RGBColor(0x1F, 0x23, 0x28)
BLUE = RGBColor(0x1F, 0x5F, 0xA8)     # 结构 / 题目 / 动作
GREEN = RGBColor(0x1E, 0x7A, 0x3C)    # 升格版 / 命中
RED = RGBColor(0xB0, 0x25, 0x1E)      # 漏点 / 错误 / 超字
AMBER = RGBColor(0xA8, 0x62, 0x00)    # 不完整 / 提示
PURPLE = RGBColor(0x5B, 0x33, 0x8C)   # 评价型
TEAL = RGBColor(0x0E, 0x6E, 0x66)     # 概括
GRAY = RGBColor(0x64, 0x6B, 0x72)

FILL_BLUE = "DCE8F5"
FILL_GREEN = "DFF0E3"
FILL_RED = "F7DEDC"
FILL_AMBER = "FBEBD3"
FILL_GRAY = "F1F2F4"
FILL_DARK = "23303D"

KITS = [
    dict(day=1, date="2026-10-25", kind="未交卷", score=None, full=None,
         src=None, accent=GRAY, note="系统第 1 天：任务单已发，四样作业未交，无批改。"),
    dict(day=2, date="2026-10-26", kind="贯彻执行 · 工作方案", score=9, full=25,
         src="review-2026-10-26.md", accent=GREEN, note="格式四件全缺（标题／主送／落款／部署语气）。"),
    dict(day=3, date="2026-10-27", kind="综合分析 · 评价型", score=10, full=20,
         src="review-2026-10-27.md", accent=PURPLE, note="第一次做评析题：两派观点并排复述，没有表态。"),
    dict(day=4, date="2026-10-28", kind="综合分析 · 评价型（二次）", score=10, full=20,
         src="review-2026-10-28.md", accent=PURPLE, note="结构升级（正—反—结论），但第一句仍是材料原话。"),
    dict(day=5, date="2026-10-30", kind="归纳概括 · 问题型", score=8, full=15,
         src="review-2026-10-30.md", accent=TEAL, note="第一次真的“合并”了；每条只有定性，没有证据。"),
    dict(day=6, date="2026-10-31", kind="整卷摸底（四题）", score=24, full=100,
         src="review-2026-11-01.md", accent=RED, note="不勾画就作答；四题字数全线不足；作文交白卷。"),
    dict(day=7, date="2026-11-01", kind="回炉卷（同材料三题）", score=29, full=80,
         src="review-2026-11-02.md", accent=AMBER, note="勾画从 0 到 24 句；把最硬的三条自己划掉了。"),
    dict(day=8, date="2026-11-03", kind="混合练 · 概括＋解释", score=22, full=35,
         src="review-2026-11-03.md", accent=TEAL, note="每条挂上证据；第一句还是复述。"),
    dict(day=9, date="2026-11-05", kind="回炉第二遍 · 两句话", score=31, full=35,
         src="review-2026-11-05.md", accent=GREEN, note="总括句＋判断句同时练成；开头段超 14 字。"),
    dict(day=10, date="2026-11-06", kind="对策题 · 参考答案", score=None, full=None,
         src="review-2026-11-06.md", accent=BLUE, note="当天未交作答；这一份是 372 字参考答案，对照用。"),
    dict(day=11, date="2026-11-07", kind="第 2 周限时整卷（四题）", score=79, full=100,
         src="review-2026-11-07-p17.md", accent=GREEN, note="第一句终于会写判断句；三题合计超 69 字。"),
    dict(day=12, date="2026-11-09", kind="复盘日（超字数专项）", score=None, full=None,
         src=None, accent=AMBER, note="不写新题：压字数、同维度分论点、补两句话。"),
    dict(day=13, date="2026-11-10", kind="对策专项 · 加装电梯", score=14, full=20,
         src="review-2026-11-10.md", accent=BLUE, note="内容站住了，四条对策全部超 60 字。"),
]


# ---------------- 小工具 ----------------
def shade_par(p, fill: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    p._p.get_or_add_pPr().append(shd)


def shade_cell(cell, fill: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def txt(doc, body: str, *, size=9.5, bold=False, color=INK, space_after=2.5,
        line=1.35, indent=0.0, align=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    r = p.add_run(body)
    r.font.size = Pt(size)
    r.bold = bold
    r.font.color.rgb = color
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return p


def banner(doc, body: str, fill: str, color=RGBColor(0xFF, 0xFF, 0xFF), size=12.5):
    p = txt(doc, body, size=size, bold=True, color=color, space_after=3)
    shade_par(p, fill)
    return p


def score_color(score, full):
    if score is None or full in (None, 0):
        return GRAY, FILL_GRAY
    pct = score / full
    if pct >= 0.8:
        return GREEN, FILL_GREEN
    if pct >= 0.6:
        return AMBER, FILL_AMBER
    return RED, FILL_RED


def set_widths(table, widths):
    """固定列宽：关掉 autofit，按厘米写死每一列（LibreOffice/Word 都认）。"""
    table.autofit = False
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    for row in table.rows:
        for idx, w in enumerate(widths):
            if idx < len(row.cells):
                H.cell_width(row.cells[idx], w)


# ---------------- 封面 ----------------
def cover(doc):
    for _ in range(2):
        txt(doc, "", size=8)
    txt(doc, "申论全程复习册", size=30, bold=True, color=INK, space_after=4)
    txt(doc, "Day 1 – Day 13 ｜ 十次作答 ＋ 两次整卷 ＋ 参考答案", size=12, color=GRAY, space_after=2)
    txt(doc, "2026-10-25 至 2026-11-10 · 建立期 ＋ 强化期", size=10.5, color=GRAY, space_after=16)

    banner(doc, "　颜色怎么读", FILL_DARK, size=11.5)
    rows = [
        (BLUE, "蓝色＝结构（题目、时间、你的动作）"),
        (GREEN, "绿色＝升格版答案、命中的采分点、80 分以上的日子"),
        (RED, "红色＝漏点、错判、超字数、60 分以下的日子"),
        (AMBER, "琥珀＝不完整、待回炉、60–79 分的日子"),
        (PURPLE, "紫色＝评价型（评析）题的日子"),
        (TEAL, "青色＝概括题的日子"),
        (GRAY, "灰色＝未交卷或只有参考答案的日子"),
    ]
    t = doc.add_table(rows=len(rows), cols=2)
    t.style = "Table Grid"
    for i, (col, label) in enumerate(rows):
        c0, c1 = t.rows[i].cells
        c0.text = ""
        shade_cell(c0, "%02X%02X%02X" % (col[0], col[1], col[2]))
        c1.text = ""
        p = c1.paragraphs[0]
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run("　" + label)
        r.font.size = Pt(9)
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    set_widths(t, [1.6, 15.2])

    txt(doc, "", size=8)
    banner(doc, "　十三天的账", FILL_DARK, size=11.5)
    t2 = doc.add_table(rows=len(KITS) + 1, cols=5)
    t2.style = "Table Grid"
    heads = ["Day", "日期", "题型", "得分", "一句话"]
    widths = [1.4, 2.6, 6.2, 2.4, 5.0]
    for i, h in enumerate(heads):
        c = t2.rows[0].cells[i]
        c.text = ""
        H.cell_width(c, widths[i])
        shade_cell(c, "E8EAED")
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(8.5)
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    for i, k in enumerate(KITS, 1):
        col, fill = score_color(k["score"], k["full"])
        cells = t2.rows[i].cells
        for j, w in enumerate(widths):
            H.cell_width(cells[j], w)
        vals = [
            str(k["day"]),
            k["date"],
            k["kind"],
            "—" if k["score"] is None else f"{k['score']} / {k['full']}",
            k["note"],
        ]
        for j, v in enumerate(vals):
            c = cells[j]
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(v)
            r.font.size = Pt(8)
            r.font.name = FONT
            r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
            if j == 3:
                r.bold = True
                r.font.color.rgb = col
                shade_cell(c, fill)

    set_widths(t2, widths)

    txt(doc, "", size=8)
    txt(doc, "怎么用（每次 15 分钟）", size=10.5, bold=True, color=BLUE, space_after=3)
    for i, s in enumerate([
        "先只读题目和材料，自己在纸上把第一句写出来——十三天里反复失分的就是这一句。",
        "翻到当天那一节，只看三处：得分表的红色项、漏点、升格版的第一句。",
        "把「带走的一个动作」抄到同一张纸上。十三天抄完，重复最多的三条就是现在真正的短板。",
        "颜色只用来定位，不用来评分：红的多半是格式问题，琥珀的多半是内容只写半句。",
    ], 1):
        txt(doc, f"{i}. {s}", size=9, color=INK, space_after=1.5, indent=0.3)


# ---------------- 一天的正文 ----------------
ARCHIVE = ROOT / "申论" / "任务存档"


def questions_for(k):
    """从任务存档里取当天的题目原文，返回 [(标签, 题干)]。"""
    path = ARCHIVE / f"{k['date']}.md"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for i, ln in enumerate(lines):
        t = ln.strip()
        m = re.match(r"^>\s*\*\*题目\s*(\d*)\s*\*\*\s*[:：]?\s*(.+)$", t)
        if m:
            num, body = m.group(1), m.group(2)
            out.append((f"第 {num} 题" if num else "原题", body.strip()))
            continue
        m = re.match(r"^##\s*T2\s*·\s*作答.*$", t)
        if m:
            for j in range(i + 1, min(i + 6, len(lines))):
                nxt = lines[j].strip()
                if nxt.startswith(">"):
                    body = nxt.lstrip("> ").strip()
                    if body:
                        out.append(("原题", body))
                    break
    # 去掉残留的 **题目**：前缀，并按内容去重（同一题常被抄两份）
    cleaned, seen = [], set()
    for label, body in out:
        body = re.sub(r"^\*\*题目[^*]*\*\*\s*[:：]?\s*", "", body).strip()
        key = body[:40]
        if not body or key in seen:
            continue
        seen.add(key)
        cleaned.append((label, body))
    return cleaned


REQ_RE = re.compile(r"（([^（）]*?(?:\d+\s*字|\d+\s*分|要求)[^（）]*?)）")
TYPE_WORDS = ("工作方案", "倡议书", "评析", "评价", "概括", "对策建议", "对策", "提纲",
              "议论文", "短评", "简报", "讲话稿", "解说词")
ROLE_RE = re.compile(r"假如你是[^，。；]{2,30}?(?:工作人员|干部|干事|负责人|专员)")
NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:字|分|分钟)")


def question_block(doc, label: str, body: str):
    """一行原题：紫色标签 + 题干（黑），括号里的字数/分值（红），其余数字（琥珀）。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.35
    pf.left_indent = Cm(0.2)
    shade_par(p, "F2ECF9")

    def run(text, color=INK, bold=False, size=9.2):
        if not text:
            return
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        r.font.color.rgb = color
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    run(f" {label} ", PURPLE, True, 8.5)
    run("　")

    # 三种标记同时上色：括号里的字数/分值（红）、身份限定（蓝）、文种（紫加粗）
    spans = []  # (start, end, kind)
    for m in REQ_RE.finditer(body):
        spans.append((m.start(), m.end(), "req"))
    for m in ROLE_RE.finditer(body):
        spans.append((m.start(), m.end(), "role"))
    for word in TYPE_WORDS:
        for m in re.finditer(re.escape(word), body):
            spans.append((m.start(), m.end(), "type"))
    spans.sort()

    pos = 0
    for start, end, kind in spans:
        if start < pos:  # 重叠，跳过
            continue
        run(body[pos:start], INK, False, 9.2)
        seg = body[start:end]
        if kind == "req":
            run(seg, RED, True, 9.0)
        elif kind == "role":
            run(seg, BLUE, True, 9.2)
        else:
            run(seg, PURPLE, True, 9.2)
        pos = end
    run(body[pos:], INK, False, 9.2)


def day_section(doc, k):
    # 不强制分页：内容短的日子不再留半页空白；用彩色横幅做视觉分割
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(10)
    col, fill = score_color(k["score"], k["full"])
    accent_fill = "%02X%02X%02X" % (k["accent"][0], k["accent"][1], k["accent"][2])
    banner(doc, f"　Day {k['day']} · {k['date']} · {k['kind']}", accent_fill, size=13)

    sub = k["note"]
    if k["score"] is not None:
        p = txt(doc, f"　得分 {k['score']} / {k['full']}　　{sub}", size=9, bold=True, color=col, space_after=6)
        shade_par(p, fill)
    else:
        p = txt(doc, f"　{sub}", size=9, bold=True, color=GRAY, space_after=6)
        shade_par(p, FILL_GRAY)

    if not k["src"]:
        CUR_SCORE[0], CUR_SCORE[1] = score_color(k["score"], k["full"])
        for label, body in questions_for(k):
            question_block(doc, label, body)
        txt(doc, "（这一天没有留下批改：只记录题目与结果。）", size=9, color=GRAY, space_after=4)
        return

    CUR_SCORE[0], CUR_SCORE[1] = score_color(k["score"], k["full"])

    for label, body in questions_for(k):
        question_block(doc, label, body)
    txt(doc, "", size=3, space_after=3)

    src = ROOT / "tools" / k["src"]
    data = R.parse(src)
    emit_colored(doc, data["block"])


CUR_SCORE = [None, None]


SEC_COLORS = [
    ("漏点", RED, FILL_RED),
    ("升格", GREEN, FILL_GREEN),
    ("参考", GREEN, FILL_GREEN),
    ("一个动作", BLUE, FILL_BLUE),
    ("下一步", BLUE, FILL_BLUE),
    ("T1", TEAL, FILL_GRAY),
    ("T3", TEAL, FILL_GRAY),
    ("T4", TEAL, FILL_GRAY),
    ("题目", INK, None),
]


def heading_color(text: str):
    if "得分" in text and CUR_SCORE[0] is not None:
        return CUR_SCORE[0], CUR_SCORE[1]
    for key, col, fill in SEC_COLORS:
        if key in text:
            return col, fill
    return INK, None


def emit_colored(doc, blocks):
    skip = False
    for b in blocks:
        kind = b["t"]
        if kind == "hr":
            continue
        if kind in ("h2", "h3"):
            head = R.plain(b["text"])
            # 原题由 question_block 统一渲染（带颜色），这里跳过解析自带的题目小节
            skip = "题目" in head
            if skip:
                continue
        if skip:
            continue
        if kind == "h2":
            body = R.plain(b["text"])
            col, fill = heading_color(body)
            p = txt(doc, body, size=11.5, bold=True, color=col, space_after=4)
            if fill:
                shade_par(p, fill)
        elif kind == "h3":
            body = R.plain(b["text"])
            col, fill = heading_color(body)
            txt(doc, body, size=10, bold=True, color=col, space_after=2)
        elif kind == "quote":
            p = txt(doc, R.plain(b["text"]), size=9, color=RGBColor(0x33, 0x3A, 0x40),
                    space_after=3, indent=0.5)
            shade_par(p, FILL_GRAY)
        elif kind == "li":
            num, body = b.get("num"), R.plain(b["text"])
            txt(doc, f"{num}. {body}" if num else f"· {body}", size=9, color=INK,
                space_after=1, indent=0.3)
        elif kind == "p":
            txt(doc, R.plain(b["text"]), size=9.2, color=INK, space_after=2)
        elif kind == "table":
            rows = b["rows"]
            if not rows:
                continue
            ncol = max(len(r) for r in rows)
            t = doc.add_table(rows=len(rows), cols=ncol)
            t.style = "Table Grid"
            total = 16.8
            first = 3.6 if ncol == 3 else (2.4 if ncol == 4 else 16.8 / max(ncol, 1))
            rest = (total - first) / max(ncol - 1, 1)
            widths = [first] + [rest] * (ncol - 1)
            for ri, row in enumerate(rows):
                for ci in range(ncol):
                    cell = t.rows[ri].cells[ci]
                    cell.text = ""
                    raw = row[ci] if ci < len(row) else ""
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(0.5)
                    add_cell_runs(p, raw, header=(ri == 0))
                    if ri == 0:
                        shade_cell(cell, "E8EAED")
            set_widths(t, widths)
            txt(doc, "", size=4, space_after=2)


def add_cell_runs(p, raw: str, *, header=False):
    """表格单元格：识别 ✅ / △ / × 上色，其余按普通文字。"""
    s = R.plain(raw).strip()
    if not s:
        return

    def push(text, color=INK, bold=False, size=8):
        if not text:
            return
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold or header
        r.font.color.rgb = color
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    if "✅" in s:
        push(s.replace("✅", "").strip() or "命中", GREEN, True)
        p.runs[0].text = "● " + p.runs[0].text
    elif s.startswith("△") or "△" in s:
        push(s.replace("△", "").strip() or "不完整", AMBER, True)
        p.runs[0].text = "◐ " + p.runs[0].text
    elif "×" in s or "❌" in s or s.startswith("✗"):
        push(s.replace("❌", "").replace("×", "").replace("✗", "").strip() or "未命中", RED, True)
        p.runs[0].text = "✗ " + p.runs[0].text
    else:
        push(s, INK if not header else RGBColor(0x20, 0x24, 0x28))


# ---------------- 结尾 ----------------
def closing(doc):
    doc.add_page_break()
    banner(doc, "　十三天，一张纸", FILL_DARK, size=13)
    txt(doc, "把每天那一句「带走的一个动作」按时间抄下来，重复出现的就是你真正的短板：",
        size=9.5, color=INK, space_after=6)
    items = [
        (GREEN, "Day 2–4", "格式先于内容：骨架五行、判断句、标题三法——写不满格式就别谈采分。"),
        (TEAL, "Day 5–8", "每条要点后面必须挂一个数字或一句原话，否则只是口号。"),
        (GREEN, "Day 9", "总括句和判断句是两句话，都要单独练，不能互相代替。"),
        (RED, "Day 6 / 11 / 13", "字数：先算格再动笔。400＝开头 45＋5 条×60＋结尾 25；250＝开头 35＋3 条×60＋结尾 35。"),
        (BLUE, "Day 13", "一条对策只干一件事；写完数一数自己提了几条。"),
    ]
    t = doc.add_table(rows=len(items), cols=2)
    t.style = "Table Grid"
    for i, (col, tag, body) in enumerate(items):
        c0, c1 = t.rows[i].cells
        H.cell_width(c0, 3.4)
        H.cell_width(c1, 14.0)
        c0.text = ""
        shade_cell(c0, "%02X%02X%02X" % (col[0], col[1], col[2]))
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(tag)
        r0.bold = True
        r0.font.size = Pt(8.5)
        r0.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r0.font.name = FONT
        r0._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        c1.text = ""
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(body)
        r1.font.size = Pt(8.5)
        r1.font.name = FONT
        r1._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    txt(doc, "", size=8)
    banner(doc, "　接下来两周怎么走", FILL_BLUE, color=INK, size=11)
    for s in [
        "第 3 周（现在）：对策专项——一条一件事、每条 40–60 字、至少两条带「考核」或「钱」。",
        "第 4 周：作文零件升级为整篇，第一次限时写 1000 字。",
        "每次整卷结束把这一本翻到「十三天，一张纸」，看有没有新的重复项。",
    ]:
        txt(doc, "· " + s, size=9, color=INK, space_after=2, indent=0.3)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    doc = Document()
    H.set_style(doc)
    OUT.mkdir(parents=True, exist_ok=True)

    cover(doc)
    for k in KITS:
        day_section(doc, k)
    closing(doc)

    dst = OUT / "全程复习册.docx"
    doc.save(str(dst))
    print("docx →", dst)
    pdf_path = dst.with_suffix(".pdf")
    pdf = H.to_pdf(dst, pdf_path)
    print("pdf  →", pdf_path if pdf else "（失败）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
