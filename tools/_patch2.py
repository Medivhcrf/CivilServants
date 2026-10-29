import pathlib

# ---------- 1) make_review_docx: 抽出 emit_blocks ----------
p = pathlib.Path(r"tools\make_review_docx.py")
s = p.read_text(encoding="utf-8")

start = s.index('    for b in data["block"]:')
end = s.index('    doc.save(str(dst))')
loop = s[start:end]

# 去掉一层缩进（从 4 空格变成 4 空格仍是函数体）——保持原样，放进 emit_blocks
func = "def emit_blocks(doc, blocks) -> None:\n" + loop.replace("data[\"block\"]", "blocks") + "\n\n"

s = s[:start] + "    emit_blocks(doc, data[\"block\"])\n\n" + s[end:]
s = s.replace("def build(data: dict, dst: Path) -> None:", func + "def build(data: dict, dst: Path) -> None:")
p.write_text(s, encoding="utf-8")
print("review patched")

# ---------- 2) make_handout: --extra / --name ----------
h = pathlib.Path(r"tools\make_handout.py")
t = h.read_text(encoding="utf-8")

t = t.replace(
    "def build(data: dict, dst: Path, sample: dict | None = None) -> None:",
    "def build(data: dict, dst: Path, sample: dict | None = None, extra: Path | None = None) -> None:",
)

t = t.replace(
    '''    para(doc, "交作业：T1 勾画稿、T2 表态行 + 300 字、T3 三样零件（拍照发对话即可）。",
         size=8.5, color=(0x66, 0x66, 0x66), space_before=6)''',
    '''    para(doc, "交作业：T1 勾画稿、T2 表态行 + 300 字、T3 三样零件（拍照发对话即可）。",
         size=8.5, color=(0x66, 0x66, 0x66), space_before=6)

    if extra and Path(extra).exists():
        doc.add_page_break()
        import make_review_docx  # 延迟导入，避免循环
        blocks = make_review_docx.parse(Path(extra))["block"]
        make_review_docx.emit_blocks(doc, blocks)''',
)

t = t.replace(
    '''    ap.add_argument("--sample", default="", help="样例答案 JSON 路径（留空=空白练习纸）")''',
    '''    ap.add_argument("--sample", default="", help="样例答案 JSON 路径（留空=空白练习纸）")
    ap.add_argument("--extra", default="", help="解析 markdown 路径（附在最后，另起一页）")
    ap.add_argument("--name", default="", help="输出文件名（不含扩展名）")''',
)

t = t.replace(
    '''    name = f"{data['date']}-task" + ("-sample" if sample else "")
    docx = out / f"{name}.docx"
    build(data, docx, sample)''',
    '''    extra = Path(args.extra) if args.extra else None
    name = args.name or (f"{data['date']}-task" + ("-sample" if sample else ""))
    docx = out / f"{name}.docx"
    build(data, docx, sample, extra)''',
)

h.write_text(t, encoding="utf-8")
print("handout patched")
