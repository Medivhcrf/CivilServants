"""把三天的复习包合成一本《申论复习册》：样例答卷 ＋ 批改解析，一个 PDF 看完全部。

用法：
    python tools\\make_review_book.py            # 生成到 docs/print/复习册-<今天>.pdf
    python tools\\make_review_book.py --out E:\\Harness\\申论复习册.pdf
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_handout as H  # noqa: E402

ROOT = H.ROOT
TOOLS = Path(__file__).resolve().parent
OUT = H.OUT

PACKS = [
    ("2026-10-26", "Day 2 · 贯彻执行（工作方案）", "练习 9 · 餐饮浪费 · 9 / 25"),
    ("2026-10-27", "Day 3 · 综合分析（评价型）", "练习 10 · 社区食堂 · 10 / 20"),
    ("2026-10-28", "Day 4 · 综合分析（评价型）", "练习 11 · 首违不罚 · 10 / 20"),
]


def pack_sources(date: str) -> tuple[Path, Path, Path] | None:
    sheet = TOOLS / "sheets" / f"{date}-sheet.md"
    src = sheet if sheet.exists() else ROOT / "申论" / "任务存档" / f"{date}.md"
    if not src.exists():
        # 今天（还没有存档）
        src = ROOT / "申论" / "今日任务.md"
    sample = TOOLS / f"sample-{date}.json"
    if not sample.exists():
        sample = TOOLS / "handout-sample.json"
    extra = TOOLS / f"review-{date}.md"
    if not extra.exists():
        extra = ROOT / "申论" / "本次批改.md"
    if not (src.exists() and sample.exists() and extra.exists()):
        return None
    return src, sample, extra


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    doc = H.new_doc("申论 · 复习册 · 样例答卷 ＋ 批改解析 · 建立期 Day 2–Day 4")

    # 封面
    H.para(doc, "", size=10, space_after=60)
    H.para(doc, "申论复习册", size=30, bold=True, space_after=6)
    H.para(doc, "样例答卷 ＋ 批改解析", size=14, color=(0x55, 0x55, 0x55), space_after=4)
    H.para(doc, "建立期 · 第 1 周 · Day 2 — Day 4（2026-10-26 至 2026-10-28）",
           size=10.5, color=(0x66, 0x66, 0x66), space_after=24)

    H.para(doc, "这本册子里有什么", size=12, bold=True, space_before=8, space_after=4)
    for line in (
        "每份复习包含两部分：前几页是**填满的答题卡**（材料勾画 · T1 表格 · T2 三行与答案 · T3/T4），后两页是当天的**批改解析**（得分表 · 逐条对照 · 漏点出处 · 一个动作）。",
        "三天对应三次真实作答：工作方案 9/25、评价型 10/20、评价型 10/20。三天的毛病其实是一条线：格式没搭起来 → 不表态 → 表态了但不算分。",
    ):
        H.para(doc, H.clean(line), size=10.5, space_after=3)

    H.para(doc, "怎么用（每天 20 分钟，三天一轮）", size=12, bold=True, space_before=12, space_after=4)
    for i, line in enumerate((
        "先不看样例：只读题目和材料，把 T2 的**第一句**写出来。这是三天里唯一反复失分的地方。",
        "再翻到该题的样例答案，只比三处：第一句是不是判断句／每派有没有写「边界」／主体占比够不够。",
        "解析页只读两节：「漏点（含出处）」和「带走的一个动作」。得分表扫一眼即可。",
        "三份读完，把三个「一个动作」抄到同一张纸上：骨架五行 · 第一句判断句 · 先写小标题再写正文。",
    ), 1):
        H.para(doc, f"{i}. {H.clean(line)}", size=10.5, space_after=2)

    H.para(doc, "目录", size=12, bold=True, space_before=14, space_after=4)
    for i, (date, title, score) in enumerate(PACKS, 1):
        H.para(doc, f"{i}. {H.clean(title)}　{date}　（{score}）", size=10.5, space_after=2)

    # 三个包
    built = []
    for date, title, score in PACKS:
        got = pack_sources(date)
        if not got:
            print(f"跳过 {date}（缺材料/样例/解析）")
            continue
        src, sample_json, extra = got
        data = H.parse(src)
        sample = json.loads(sample_json.read_text(encoding="utf-8-sig"))
        doc.add_page_break()
        H.heading(doc, title)
        H.para(doc, f"{date}　{score}", size=9.5, color=(0x66, 0x66, 0x66), space_after=4)
        H.render_into(doc, data, sample, extra, break_t1=True)
        built.append(title)

    name = args.out or str(OUT / "复习册.docx")
    docx = Path(name)
    docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx))
    print(f"docx → {docx}")
    pdf = docx.with_suffix(".pdf")
    if H.to_pdf(docx, pdf):
        print(f"pdf  → {pdf}")
    else:
        print("pdf 转换失败（docx 可手动打印）", file=sys.stderr)
        return 1
    return 0 if built else 1


if __name__ == "__main__":
    raise SystemExit(main())
