#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 申论/今日任务.md 变成可以打印的 A4 练习纸（docx），再用 LibreOffice Kit 转 PDF。

设计取向：打印出来是"用来写的"，不是"用来读的"——
  · 材料每段右侧留 4.5cm 空白，专门给勾画和批注；
  · T1 直接给空表格；T2 给表态三行 + 12 条答案横线；
  · T3/T4 给编号横线，写完就是作业。

用法：
    python tools/make_handout.py                 # 今天的任务单
    python tools/make_handout.py --src 申论/今日任务.md
输出：
    docs/print/<date>-任务单.pdf      （站点可下载）
    docs/print/<date>-任务单.docx     （想改排版时用）
    申论/任务存档/<date>-打印版.pdf   （归档）
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "申论" / "今日任务.md"
OUT = ROOT / "docs" / "print"
ARCHIVE = ROOT / "申论" / "任务存档"

FONT = "宋体"
FONT_EN = "Times New Roman"

NODE = Path(r"E:\Program Files、\resources\runtime\primary-runtime\dependencies\node\bin\node.exe")
CLI = Path(r"E:\Program Files、\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")


# ---------- 文本清理 ----------
def clean(s: str) -> str:
    s = re.sub(r"==[^|=\n]*\|([^=\n]*)==", r"\1", s)   # 语义色标记
    s = s.replace("**", "").replace("`", "")
    s = s.replace("*", "")
    return s.strip()


def grab_section(lines: list[str], start_kw: str, stop_kw: list[str]) -> list[str]:
    out, on = [], False
    for ln in lines:
        if not on and ln.strip().startswith(start_kw):
            on = True
            continue
        if on and any(ln.strip().startswith(k) for k in stop_kw):
            break
        if on:
            out.append(ln)
    return out


def parse(src: Path) -> dict:
    text = src.read_text(encoding="utf-8")
    lines = text.splitlines()

    date = re.search(r"(\d{4}-\d{2}-\d{2})", text[:600])
    day = re.search(r"Day\s*(\d+)", text[:600])
    week = re.search(r"（(周[一二三四五六日])）", text[:600])

    # 材料：**材料一** 换行 正文
    mats = []
    for m in re.finditer(r"\*\*材料([一二三四五六七八九十]+)\*\*\s*\n+(.*?)(?=\n\s*\*\*材料|\n---|\n## )",
                         text, re.S):
        body = clean(" ".join(x.strip() for x in m.group(2).splitlines() if x.strip()))
        if body:
            mats.append((f"材料{m.group(1)}", body))

    # 时间表
    rows = []
    for ln in lines:
        if ln.strip().startswith("|") and ln.count("|") >= 3:
            cells = [clean(c) for c in ln.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            rows.append(cells)
    # 只留时间表那一段（以"时段"或"时"开头的那张）
    sched = []
    if rows:
        start = next((i for i, r in enumerate(rows) if r and r[0] in ("时段", "时")), None)
        if start is not None:
            for r in rows[start + 1:]:
                if not r or not r[0] or r[0].startswith("轨道"):
                    break
                sched.append(r)
    # 题目：## T2 后的第一条引用块 **题目**：
    t2 = grab_section(lines, "## T2", ["## 交卷前自查", "## T3"])
    question = ""
    for ln in t2:
        m = re.match(r">\s*\*\*题目\*\*[:：]\s*(.+)$", clean(ln) if not ln.startswith(">") else ln.lstrip("> ").replace("**题目**", "**题目**"))
        if m:
            question = clean(m.group(1))
            break
    if not question:
        m = re.search(r"\*\*题目\*\*[:：]\s*(.+?)(?:\n|$)", text)
        question = clean(m.group(1)) if m else ""

    t1 = grab_section(lines, "## T1", ["## T2"])
    t3 = grab_section(lines, "## T3", ["## T4"])
    t4 = grab_section(lines, "## T4", ["---", "## 交作业"])

    def bullets(block):
        out = []
        for ln in block:
            m = re.match(r"^\s*(?:\d+\.|[-*])\s+(.+)$", ln)
            if m:
                out.append(clean(m.group(1)))
        return out

    return {
        "date": date.group(1) if date else "0000-00-00",
        "day": day.group(1) if day else "?",
        "week": week.group(1) if week else "",
        "mats": mats,
        "sched": sched,
        "question": question,
        "t1_req": bullets(t1),
        "t3": bullets(t3),
        "t4": bullets(t4),
    }


# ---------- 排版工具 ----------
def set_style(doc: Document) -> None:
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.element.rPr.rFonts.set(qn("w:ascii"), FONT_EN)


def para(doc, text="", *, size=10.5, bold=False, space_before=0, space_after=3,
         line=1.35, align=None, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if color:
        r.font.color.rgb = RGBColor(*color)
    return p


def heading(doc, text, *, size=12.5):
    p = para(doc, text, size=size, bold=True, space_before=10, space_after=4)
    pPr = p._p.get_or_add_pPr()
    from docx.oxml import OxmlElement
    bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), "888888")
    bdr.append(bottom)
    pPr.append(bdr)
    return p


def ruled(doc, n: int, *, gap=0.95, indent=Cm(0), dotted=True):
    """n 行横线：用只有一个单元格的表格画（相邻段落的 pBdr 会被合并，表格边框不会）。"""
    t = doc.add_table(rows=n, cols=1)
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    spec = {"top": "nil", "left": "nil", "right": "nil", "insideV": "nil"}
    for name, val in spec.items():
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:val"), val)
        borders.append(el)
    for name in ("insideH", "bottom"):
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "AAAAAA")
        borders.append(el)
    tblPr.append(borders)
    for row in t.rows:
        row.height = Cm(gap * 0.95)
        trPr = row._tr.get_or_add_trPr()
        h = OxmlElement("w:trHeight")
        h.set(qn("w:val"), str(int((gap * 0.95) * 567)))
        h.set(qn("w:hRule"), "atLeast")
        trPr.append(h)
        c = row.cells[0]
        c.width = Cm(17.4)
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.add_run(" ").font.size = Pt(6)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def cell_width(cell, cm):
    cell.width = Cm(cm)


def fill_table(table, header, rows, widths, *, size=10.5, header_size=10.5):
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for j, h in enumerate(header):
        c = table.rows[0].cells[j]
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(header_size)
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        cell_width(c, widths[j])
    for row in rows:
        cells = table.add_row().cells
        for j, val in enumerate(row):
            c = cells[j]
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.25
            r = p.add_run(val)
            r.font.size = Pt(size)
            r.font.name = FONT
            r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
            cell_width(c, widths[j])


def build(data: dict, dst: Path) -> None:
    doc = Document()
    set_style(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.6)
    sec.left_margin = Cm(1.8)
    sec.right_margin = Cm(1.6)

    # 页眉
    hp = sec.header.paragraphs[0]
    hp.text = ""
    hr = hp.add_run(f"申论 · Day {data['day']} · {data['date']}{data['week']} · 打印练习纸　　姓名／日期：__________")
    hr.font.size = Pt(8.5)
    hr.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    hr.font.name = FONT
    hr._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    para(doc, f"Day {data['day']}　{data['date']}{data['week']}", size=16, bold=True, space_after=2)
    para(doc, "照时间表推进；来不及时先砍 T1／T4，T2 不许砍。", size=9.5, color=(0x66, 0x66, 0x66))

    # 时间表（压成一行行短句，省纸）
    if data["sched"]:
        heading(doc, "时间表")
        for r in data["sched"]:
            r = r + [""] * (4 - len(r))
            line = f"{r[0]}　{r[1]}　{r[2]}"
            if r[3]:
                line += f"　（{r[3]}）"
            para(doc, line, size=9, space_after=1.5, line=1.15)

    # 材料
    heading(doc, "一、材料（T1 读 20 分钟，右边空白处写勾画）")
    for label, body in data["mats"]:
        t = doc.add_table(rows=1, cols=2)
        t.style = "Table Grid"
        t.autofit = False
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        left, right = t.rows[0].cells
        cell_width(left, 14.0)
        cell_width(right, 3.4)
        left.text = ""
        p = left.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(label + "　")
        r.bold = True
        r.font.size = Pt(9)
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        r2 = p.add_run(body)
        r2.font.size = Pt(9)
        r2.font.name = FONT
        r2._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        right.text = ""
        # 一段材料不许被分页切开
        for row in t.rows:
            trPr = row._tr.get_or_add_trPr()
            cant = OxmlElement("w:cantSplit")
            trPr.append(cant)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
        spacer = doc.paragraphs[-1].paragraph_format
        spacer.line_spacing = 0.5
        doc.paragraphs[-1].add_run(" ").font.size = Pt(4)

    # T1
    heading(doc, "二、T1 勾画稿（一句一勾，标类：背 意 问 做 观 结）")
    if data["t1_req"]:
        for i, req in enumerate(data["t1_req"][:4], 1):
            para(doc, f"{i}. {req}", size=9, space_after=1)
    rows = [[str(i), "", ""] for i in range(1, 17)]
    t = doc.add_table(rows=1, cols=3)
    fill_table(t, ["句号", "我勾到的句子（原词，别改写）", "类标"], rows, [1.6, 13.4, 2.4], size=9)

    # T2
    doc.add_page_break()
    heading(doc, "三、T2 作答（限时 25 分钟，300 字，20 分）")
    if data["question"]:
        para(doc, "题目：" + data["question"], size=10, bold=True, space_after=4)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    para(doc, "动笔前先填这三行：", size=9.5, space_after=1)
    for label in ("表态：", "我主张：", "论证顺序：一、　　　二、　　　三、"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(label)
        r.font.size = Pt(10)
        r.bold = True
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    para(doc, "　", size=6, space_after=2)
    para(doc, "答案（目标 270–300 字）：", size=9.5, space_after=2)
    ruled(doc, 14)

    # T3
    heading(doc, "四、T3 作文零件（25 分钟）")
    if data["t3"]:
        for i, it in enumerate(data["t3"], 1):
            para(doc, f"{i}. {it}", size=9, space_after=1)
    para(doc, "立意一句（≤30 字）：", size=9.5, bold=True, space_after=2)
    ruled(doc, 2)
    para(doc, "三个标题（一实／一虚／一稳）：", size=9.5, bold=True, space_after=2)
    ruled(doc, 3)
    para(doc, "开头段（150 字，不许超）：", size=9.5, bold=True, space_after=2)
    ruled(doc, 7)

    # T4
    heading(doc, "五、T4 素材（15 分钟，5 句 + 1 条政策，标 [YYYY-MM]）")
    if data["t4"]:
        for i, it in enumerate(data["t4"], 1):
            para(doc, f"{i}. {it}", size=9, space_after=1)
    ruled(doc, 4)

    para(doc, "交作业：T1 勾画稿、T2 表态行 + 300 字、T3 三样零件（拍照发对话即可）。",
         size=8.5, color=(0x66, 0x66, 0x66), space_before=6)

    doc.save(dst)


def to_pdf(docx: Path, pdf: Path) -> bool:
    if not NODE.exists() or not CLI.exists():
        return False
    # LibreOffice Kit 不会覆盖已存在的输出文件，先转成临时名再替换
    tmp = pdf.with_name(pdf.stem + ".tmp.pdf")
    for f in (tmp, pdf):
        if f.exists():
            f.unlink()
    r = subprocess.run([str(NODE), str(CLI), "convert", "--input", str(docx), "--output", str(tmp)],
                       capture_output=True, encoding="utf-8", errors="replace")
    ok = tmp.exists() and tmp.stat().st_size > 0 and tmp.open("rb").read(5) == b"%PDF-"
    if ok:
        tmp.replace(pdf)
    else:
        sys.stderr.write((r.stdout or "") + (r.stderr or ""))
    return ok


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    src = Path(args.src)
    data = parse(src)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    name = f"{data['date']}-task"
    docx = out / f"{name}.docx"
    build(data, docx)
    print(f"docx → {docx}")

    pdf = out / f"{name}.pdf"
    if to_pdf(docx, pdf):
        print(f"pdf  → {pdf}")
        shutil.copy2(pdf, ARCHIVE / f"{data['date']}-打印版.pdf")
        print(f"归档 → {ARCHIVE / (data['date'] + '-打印版.pdf')}")
        # 固定文件名，站点上一个永远指向"今天"的打印入口
        shutil.copy2(pdf, out / "today.pdf")
        print(f"最新 → {out / 'today.pdf'}")
    else:
        print("pdf 转换失败（docx 已保存，可用 Word 打开打印）", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())





