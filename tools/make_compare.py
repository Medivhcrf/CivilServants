# -*- coding: utf-8 -*-
"""通用「答案对照」生成器：彩色 HTML + docx + PDF。

用法：
    python tools/make_compare.py tools/compare/2026-11-16.json

数据 JSON 结构（段内文字用 [文字, 标记] 数组，标记可选：
ok=绿底命中 / part=黄底一半 / miss=红底删除线 / add=绿下划线（标准答案里补你的））:

{
  "title":  "练习 20 · 答案对照",
  "sub":    "第 2 次限时整卷 · 基层减负 · 2026-11-16 ｜ 你的答案 vs 标准答案 ｜ 总分 ",
  "total":  "63 / 100",
  "table":  [["第 1 题 概括", "15", ["11","part"], "一句话判定"], ...],
  "questions": [
     {"band": "第 1 题 · 概括（15 分 · 250 字）",
      "question": "题干原文",
      "yours_label": "你的答案（约 250 字）",
      "yours": ["...", ["...", "ok"]],
      "std_label": "标准答案（248 字）",
      "std":   [["...", "add"], "..."],
      "rows":  [["采分要素", "你的答案", ["✘ 缺 · 扣 1", "miss"]], ...],
      "head":  ["采分要素", "你的答案", "判定"],
      "fix":   "改法：……"}
  ],
  "tail_title": "四处失分，一页看完",
  "tail_head":  ["失分", "题", "扣分", "一句话改法"],
  "tail_rows":  [["没有总括句", "第 1 题", "-1", "……"], ...],
  "foot":  ["一句话带走：", ["写完抬头问一句……", "miss"], "……"],
  "foot_note": "练习 20 · 2026-11-16 ｜ ……"
}
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import make_handout as H
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = pathlib.Path(__file__).resolve().parents[1]
OK = ("1A7F37", "D7F5DD")
PART = ("7A4D00", "FFF1C9")
MISS = ("B3121F", "FFDBDB")
FILL = {"ok": "D7F5DD", "part": "FFF1C9", "miss": "FFDBDB"}


# ---------------- docx ----------------
def shade_el(el, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    if hasattr(el, "get_or_add_pPr"):
        el.get_or_add_pPr().append(shd)
    else:
        el.get_or_add_rPr().append(shd)


def add_run(p, text, kind="plain", size=10, bold=False):
    r = p.add_run(text)
    r.font.name = H.FONT
    r.font.size = Pt(size)
    r.bold = bold
    if kind in ("ok", "part", "miss"):
        color, fill = {"ok": OK, "part": PART, "miss": MISS}[kind]
        r.font.color.rgb = RGBColor.from_string(color)
        shade_el(r._element, fill)
        if kind == "miss":
            r.font.strike = True
        if kind == "ok":
            r.bold = True
    elif kind == "add":
        r.font.color.rgb = RGBColor.from_string("1A7F37")
        r.underline = True
    elif kind == "muted":
        r.font.color.rgb = RGBColor.from_string("57606A")
    elif kind == "white":
        r.font.color.rgb = RGBColor.from_string("FFFFFF")
        r.bold = True
    return r


def docx_para(doc, segs, size=9.8, after=4, fill=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.42
    if fill:
        shade_el(p._p, fill)
    for seg in segs:
        if isinstance(seg, str):
            add_run(p, seg, size=size)
        else:
            add_run(p, seg[0], kind=seg[1], size=size)
    return p


def docx_table(doc, head, rows, widths, size=9):
    t = doc.add_table(rows=1, cols=len(head))
    t.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "D0D7DE")
        borders.append(e)
    t._tbl.tblPr.append(borders)
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]
        c.text = ""
        H.cell_width(c, widths[i])
        add_run(c.paragraphs[0], h, size=size, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            H.cell_width(cells[i], widths[i])
            if isinstance(val, list):
                add_run(cells[i].paragraphs[0], val[0], kind=val[1], size=size, bold=True)
            else:
                add_run(cells[i].paragraphs[0], str(val), size=size)
    return t


def build_docx(data, out_docx):
    doc = H.new_doc("申论 · 答案对照")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    add_run(p, data["title"], size=20, bold=True)
    docx_para(doc, [(" ".join([data.get("sub", ""), data.get("total", "")]), "muted")], size=10, after=8)
    docx_para(doc, [("颜色怎么读：  你写到了", "ok"), "＝绿底；  ",
                    ("写了一半", "part"), "＝黄底；  ",
                    ("缺", "miss"), "＝红底删除线。标准答案里的绿色下划线文字＝补给你的部分。"],
              size=9.5, fill="F2F4F6", after=8)
    docx_table(doc, ["题目", "分值", "得分", "一句话判定"], data["table"], [5.2, 2.0, 2.0, 8.8])
    for q in data["questions"]:
        band = doc.add_paragraph()
        band.paragraph_format.space_before = Pt(10)
        band.paragraph_format.space_after = Pt(6)
        shade_el(band._p, "1F3A5F")
        add_run(band, "  " + q["band"], "white", size=13, bold=True)
        docx_para(doc, [q["question"]], fill="F2F4F6")
        docx_para(doc, [(q.get("yours_label", "你的答案"), "muted")], size=9, after=2)
        docx_para(doc, q["yours"], fill="FBFCFD")
        docx_para(doc, [(q.get("std_label", "标准答案"), "add")], size=9, after=2)
        docx_para(doc, q["std"], fill="F2FBF4")
        docx_table(doc, q.get("head", ["要素", "你的答案", "判定"]), q["rows"], [4.6, 7.0, 5.4])
        if q.get("fix"):
            docx_para(doc, [q["fix"]], after=6)
    if data.get("tail_rows"):
        band = doc.add_paragraph()
        band.paragraph_format.space_before = Pt(10)
        band.paragraph_format.space_after = Pt(6)
        shade_el(band._p, "1F3A5F")
        add_run(band, "  " + data.get("tail_title", "汇总"), "white", size=13, bold=True)
        docx_table(doc, data["tail_head"], data["tail_rows"], [4.2, 1.8, 1.6, 9.4])
    docx_para(doc, data["foot"], size=10, fill="F2F4F6")
    docx_para(doc, [data.get("foot_note", "")], size=8.5)
    doc.save(out_docx)


# ---------------- html ----------------
def seg_html(seg):
    if isinstance(seg, str):
        return seg.replace("&", "&amp;").replace("<", "&lt;")
    text, kind = seg[0], seg[1]
    text = text.replace("&", "&amp;").replace("<", "&lt;")
    cls = {"ok": "ok", "part": "part", "miss": "miss", "add": "add"}.get(kind)
    return f'<mark class="{cls}">{text}</mark>' if cls else text


def table_html(head, rows):
    out = ["<table><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>"]
    for row in rows:
        cells = []
        for val in row:
            if isinstance(val, list):
                cells.append(f'<td><span class="badge b-{val[1]}">{val[0]}</span></td>')
            else:
                cells.append(f"<td>{val}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</table>")
    return "".join(out)


CSS = """
@page { size: A4; margin: 1.6cm 1.5cm; }
body { font-family: "Microsoft YaHei","PingFang SC",sans-serif; font-size: 15px; line-height: 1.7; color:#1f2328; margin:0; padding:24px; background:#fff; }
h1 { font-size: 30px; margin: 0 0 6px; }
.sub { color:#57606a; font-size: 14px; margin-bottom: 14px; }
h2 { font-size: 19px; margin: 26px 0 8px; padding: 7px 10px; background:#1f3a5f; color:#fff; border-radius:5px; }
h3 { font-size: 15px; margin: 12px 0 6px; color:#0969da; }
.qt { background:#f6f8fa; border-left:4px solid #57606a; padding:9px 11px; margin:0 0 10px; }
.ans { background:#fbfcfd; border-left:3px solid #afb8c1; padding:9px 11px; margin:5px 0 10px; }
.std { background:#f2fbf4; border-left:3px solid #1a7f37; padding:9px 11px; margin:5px 0 10px; }
.lbl { display:block; font-size:12px; color:#57606a; font-weight:700; margin-bottom:3px; letter-spacing:.5px; }
mark.ok { background:#d7f5dd; color:#0b5a22; font-weight:700; padding:0 2px; border-radius:3px; }
mark.part { background:#fff1c9; color:#7a4d00; padding:0 2px; border-radius:3px; }
mark.miss { background:#ffdbdb; color:#b3121f; padding:0 2px; border-radius:3px; text-decoration:line-through; }
mark.add { color:#1a7f37; text-decoration:underline; }
table { width:100%; border-collapse:collapse; font-size:13.5px; margin:6px 0 10px; }
th,td { border:1px solid #d0d7de; padding:6px 8px; vertical-align:top; }
th { background:#eef1f4; }
.badge { display:inline-block; padding:1px 7px; border-radius:9px; font-size:12.5px; font-weight:700; }
.b-ok { background:#d7f5dd; color:#0b5a22; }
.b-part { background:#fff1c9; color:#7a4d00; }
.b-miss { background:#ffdbdb; color:#b3121f; }
.legend { border:1px dashed #afb8c1; border-radius:6px; padding:9px 11px; margin:10px 0 14px; font-size:13.5px; }
.total { font-size:20px; font-weight:800; color:#1f3a5f; }
.foot { margin-top:18px; font-size:13px; color:#57606a; border-top:1px solid #d0d7de; padding-top:8px; }
@media (max-width:620px){ body{padding:14px;font-size:15px} h1{font-size:24px} table{font-size:12.5px} }
"""


def build_html(data, out_html):
    parts = [f"<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\">",
             "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
             f"<title>{data['title']}</title><style>{CSS}</style></head><body>",
             f"<h1>{data['title']}</h1>",
             f"<div class=\"sub\">{data.get('sub','')}<span class=\"total\">{data.get('total','')}</span></div>",
             "<div class=\"legend\"><b>颜色怎么读</b>　"
             "<span class=\"badge b-ok\">✔ 你写到了</span> 绿底＝命中；　"
             "<span class=\"badge b-part\">◐ 写了一半</span> 黄底＝有定性没证据；　"
             "<span class=\"badge b-miss\">✘ 缺</span> 红底删除线＝完全没有。"
             "标准答案里的<span style=\"color:#1a7f37;text-decoration:underline\">绿色下划线</span>＝补给你的部分。</div>",
             table_html(["题目", "分值", "得分", "一句话判定"], data["table"])]
    for q in data["questions"]:
        parts.append(f"<h2>{q['band']}</h2>")
        parts.append(f"<div class=\"qt\">{q['question']}</div>")
        parts.append(f"<span class=\"lbl\">{q.get('yours_label','你的答案')}</span>")
        parts.append("<div class=\"ans\">" + "".join(seg_html(s) for s in q["yours"]) + "</div>")
        parts.append(f"<span class=\"lbl\" style=\"color:#1a7f37\">{q.get('std_label','标准答案')}</span>")
        parts.append("<div class=\"std\">" + "".join(seg_html(s) for s in q["std"]) + "</div>")
        parts.append(table_html(q.get("head", ["要素", "你的答案", "判定"]), q["rows"]))
        if q.get("fix"):
            parts.append(f"<p><b>{q['fix']}</b></p>")
    if data.get("tail_rows"):
        parts.append(f"<h2>{data.get('tail_title','汇总')}</h2>")
        parts.append(table_html(data["tail_head"], data["tail_rows"]))
    parts.append("<div class=\"foot\">" + "".join(seg_html(s) for s in data["foot"]) + "<br>" + data.get("foot_note", "") + "</div>")
    parts.append("</body></html>")
    out_html.write_text("".join(parts), encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("usage: python tools/make_compare.py <data.json>")
        return 1
    src = pathlib.Path(sys.argv[1])
    data = json.loads(src.read_text(encoding="utf-8-sig"))
    stem = data.get("name") or src.stem.replace("-", "·")
    out_html = ROOT / "申论" / f"{stem}.html"
    build_html(data, out_html)
    print("html ->", out_html)
    out_docx = ROOT / "docs" / "print" / f"{src.stem}-compare.docx"
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    build_docx(data, out_docx)
    print("docx ->", out_docx)
    out_pdf = out_docx.with_suffix(".pdf")
    ok = H.to_pdf(out_docx, out_pdf)
    print("pdf  ->", out_pdf if ok else "FAILED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
