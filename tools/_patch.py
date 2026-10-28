import json
import pathlib

p = pathlib.Path(r"tools\make_handout.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
    "def build(data: dict, dst: Path) -> None:\n    doc = Document()",
    "def build(data: dict, dst: Path, sample: dict | None = None) -> None:\n    doc = Document()",
)

s = s.replace(
    '    para(doc, "照时间表推进；来不及时先砍 T1／T4，T2 不许砍。", size=9.5, color=(0x66, 0x66, 0x66))',
    '    if sample:\n'
    '        para(doc, sample.get("note", ""), size=9, bold=True, color=(0xB0, 0x30, 0x30))\n'
    '    else:\n'
    '        para(doc, "照时间表推进；来不及时先砍 T1／T4，T2 不许砍。", size=9.5, color=(0x66, 0x66, 0x66))',
)

s = s.replace(
    '        right.text = ""\n        # 一段材料不许被分页切开',
    '        right.text = ""\n'
    '        if sample:\n'
    '            marks = (sample.get("marks") or {}).get(label) or []\n'
    '            rp = right.paragraphs[0]\n'
    '            rp.paragraph_format.space_after = Pt(0)\n'
    '            rp.paragraph_format.line_spacing = 1.1\n'
    '            for k, line in enumerate(marks):\n'
    '                if k:\n'
    '                    rp.add_run("\\n")\n'
    '                rr = rp.add_run(line)\n'
    '                rr.font.size = Pt(7.5)\n'
    '                rr.font.name = FONT\n'
    '                rr._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)\n'
    '        # 一段材料不许被分页切开',
)

s = s.replace(
    '    rows = [[str(i), "", ""] for i in range(1, 17)]',
    '    if sample and sample.get("t1"):\n'
    '        rows = [[str(a), str(b), str(c)] for a, b, c in sample["t1"]]\n'
    '    else:\n'
    '        rows = [[str(i), "", ""] for i in range(1, 17)]',
)

s = s.replace(
    '''    for label in ("表态：", "我主张：", "论证顺序：一、　　　二、　　　三、"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(label)''',
    '''    t2 = (sample or {}).get("t2") or {}
    labels = [
        ("表态：", t2.get("stance", "")),
        ("我主张：", t2.get("claim", "")),
        ("论证顺序：一、　　　二、　　　三、", t2.get("order", "")),
    ]
    for label, val in labels:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(label)''',
)

s = s.replace(
    '''        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    para(doc, "　", size=6, space_after=2)
    para(doc, "答案（目标 270–300 字）：", size=9.5, space_after=2)
    ruled(doc, 14)''',
    '''        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        if val:
            rv = p.add_run(val)
            rv.font.size = Pt(10)
            rv.font.name = FONT
            rv._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    para(doc, "　", size=6, space_after=2)
    if t2.get("answer"):
        para(doc, "答案（答题卡上就这样写成一段，270–300 字）：", size=9.5, bold=True, space_after=3)
        box(doc, t2["answer"], size=10.5)
        para(doc, "　", size=6, space_after=2)
        para(doc, "自己练的时候写在这下面（样例只留 3 行提示位置）：", size=8.5, color=(0x66, 0x66, 0x66))
        ruled(doc, 3)
    else:
        para(doc, "答案（目标 270–300 字）：", size=9.5, space_after=2)
        ruled(doc, 14)''',
)

s = s.replace(
    '''    para(doc, "立意一句（≤30 字）：", size=9.5, bold=True, space_after=2)
    ruled(doc, 2)
    para(doc, "三个标题（一实／一虚／一稳）：", size=9.5, bold=True, space_after=2)
    ruled(doc, 3)
    para(doc, "开头段（150 字，不许超）：", size=9.5, bold=True, space_after=2)
    ruled(doc, 7)''',
    '''    t3 = (sample or {}).get("t3") or {}
    para(doc, "立意一句（≤30 字）：", size=9.5, bold=True, space_after=2)
    if t3.get("idea"):
        box(doc, t3["idea"], size=10.5)
    else:
        ruled(doc, 2)
    para(doc, "三个标题（一实／一虚／一稳）：", size=9.5, bold=True, space_after=2)
    if t3.get("titles"):
        box(doc, "\\n".join(t3["titles"]), size=10.5)
    else:
        ruled(doc, 3)
    para(doc, "开头段（150 字，不许超）：", size=9.5, bold=True, space_after=2)
    if t3.get("para"):
        box(doc, t3["para"], size=10.5)
    else:
        ruled(doc, 7)''',
)

s = s.replace(
    '''    if data["t4"]:
        for i, it in enumerate(data["t4"], 1):
            para(doc, f"{i}. {it}", size=9, space_after=1)
    ruled(doc, 4)''',
    '''    if data["t4"]:
        for i, it in enumerate(data["t4"], 1):
            para(doc, f"{i}. {it}", size=9, space_after=1)
    if sample and sample.get("t4"):
        box(doc, "\\n".join(f"{i}. {x}" for i, x in enumerate(sample["t4"], 1)), size=10)
    else:
        ruled(doc, 4)''',
)

box_fn = '''

def box(doc, text: str, *, size: float = 10.5) -> None:
    """带边框的答题区（样例文字写在这里）。"""
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    cell_width(c, 17.4)
    c.text = ""
    lines = text.split("\\n")
    first = True
    for line in lines:
        p = c.paragraphs[0] if first else c.add_paragraph()
        first = False
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.4
        r = p.add_run(line)
        r.font.size = Pt(size)
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    para(doc, "", size=3, space_after=0)


def to_pdf(docx: Path, pdf: Path) -> bool:'''
s = s.replace("\ndef to_pdf(docx: Path, pdf: Path) -> bool:", box_fn, 1)

s = s.replace(
    '''    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()''',
    '''    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--sample", default="", help="样例答案 JSON 路径（留空=空白练习纸）")
    args = ap.parse_args()''',
)

s = s.replace(
    '''    name = f"{data['date']}-task"
    docx = out / f"{name}.docx"
    build(data, docx)''',
    '''    sample = None
    if args.sample:
        raw = Path(args.sample).read_text(encoding="utf-8-sig")
        sample = json.loads(raw)
    name = f"{data['date']}-task" + ("-sample" if sample else "")
    docx = out / f"{name}.docx"
    build(data, docx, sample)''',
)

s = s.replace("import argparse\nimport re", "import argparse\nimport json\nimport re")

p.write_text(s, encoding="utf-8")
print("patched chars:", len(s))
