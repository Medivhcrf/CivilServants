import pathlib

p = pathlib.Path(r"tools\make_handout.py")
s = p.read_text(encoding="utf-8")

old_head = '''def build(data: dict, dst: Path, sample: dict | None = None, extra: Path | None = None, break_t1: bool = False) -> None:
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

    para(doc, f"Day {data['day']}　{data['date']}{data['week']}", size=16, bold=True, space_after=2)'''

new_head = '''def new_doc(header_text: str = "") -> Document:
    """建一个 A4 文档，设好样式、页边距和页眉。"""
    doc = Document()
    set_style(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.6)
    sec.left_margin = Cm(1.8)
    sec.right_margin = Cm(1.6)
    if header_text:
        hp = sec.header.paragraphs[0]
        hp.text = ""
        hr = hp.add_run(header_text)
        hr.font.size = Pt(8.5)
        hr.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        hr.font.name = FONT
        hr._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return doc


def build(data: dict, dst: Path, sample: dict | None = None, extra: Path | None = None, break_t1: bool = False) -> None:
    header = f"申论 · Day {data['day']} · {data['date']}{data['week']} · 打印练习纸　　姓名／日期：__________"
    doc = new_doc(header)
    render_into(doc, data, sample, extra, break_t1)
    doc.save(str(dst))


def render_into(doc: Document, data: dict, sample: dict | None = None,
                extra: Path | None = None, break_t1: bool = False) -> None:
    para(doc, f"Day {data['day']}　{data['date']}{data['week']}", size=16, bold=True, space_after=2)'''

assert old_head in s
s = s.replace(old_head, new_head)

# build() 里原来的 doc.save(dst) 现在在 build 中已处理；去掉 render 末尾的 save
s = s.replace('''        make_review_docx.emit_blocks(doc, blocks)

    doc.save(dst)''', '''        make_review_docx.emit_blocks(doc, blocks)''')

p.write_text(s, encoding="utf-8")
print("refactored")
