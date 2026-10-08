#!/usr/bin/env python3
"""校验申论图解课件（HTML）。

用法:
    python3 check_diagram.py <file.html> [--limit 250] [--marks]

通用检查（所有模板）:
    1. 所有 data-src 引用的元素 id 都存在
    2. HTML 标签闭合平衡
    3. 答案块数量 == 注释块数量

模板 A（含「完整答案（考场版）」+ 对照工作台）额外检查:
    4. 考场版与逐句注释版逐字一致
    5. 答案字数实测，且在题目上限之内

--marks 额外输出:
    6. 逐节统计「抄（材料原词）／自（自己写）／概（概括上升）」的字数与占比，
       用于与课件里宣称的数字人工核对。点评块 .an 会被排除。

退出码: 0 全部通过 / 1 存在错误
"""

from __future__ import annotations

import re
import sys
import html.parser
from pathlib import Path

VOID = {"meta", "br", "hr", "img", "input", "link", "source",
        "area", "base", "col", "embed", "track", "wbr"}

MARK_CLASSES = ("mk-copy", "mk-own", "mk-cond")
MARK_NAMES = {"mk-copy": "抄", "mk-own": "自", "mk-cond": "概"}


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def norm(s: str) -> str:
    return re.sub(r"\s+", "", strip_tags(s))


class TagBalance(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"未闭合 <{self.stack.pop()}>")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"孤立闭合 </{tag}>")


def final_answer(src: str) -> str | None:
    """模板 A 的「考场版」正文；不存在则返回 None。"""
    m = re.search(r'<div class="final">(.*?)</div>\s*<div class="bench">', src, re.S)
    if not m:
        return None
    body = re.sub(r'<span class="seg[^"]*"[^>]*>.*?</span>', "", m.group(1), flags=re.S)
    return norm("".join(re.findall(r"<p>(.*?)</p>", body, re.S)))


def annotated_answer(src: str) -> str:
    """逐句注释版的答案正文。"""
    return norm("".join(re.findall(r'<div class="ans-text">(.*?)</div>', src, re.S)))


def section_ratios(src: str) -> list[tuple[str, int, dict[str, int]]]:
    """按 <section> 切分，逐节统计三色标记字数。排除点评块 .an。"""
    out = []
    parts = re.split(r"<section\b", src)[1:]
    for idx, part in enumerate(parts, 1):
        body = re.sub(r'<div class="an"[^>]*>.*?</div>', "", part, flags=re.S)
        ats = re.findall(r'<div class="at">(.*?)</div>', body, re.S)
        if not ats:
            continue
        counts = {k: 0 for k in MARK_CLASSES}
        for at in ats:
            for k in MARK_CLASSES:
                for m in re.findall(r'<span class="%s">(.*?)</span>' % k, at, re.S):
                    counts[k] += len(strip_tags(m))
        total = len(norm("".join(ats)))
        if total:
            out.append((f"section {idx}", total, counts))
    return out


def check(path: Path, limit: int | None, marks: bool) -> int:
    if not path.is_file():
        print(f"✗ 文件不存在: {path}")
        return 1

    src = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warns: list[str] = []

    # ---- 1. data-src <-> id ----
    ids = set(re.findall(r'id="([^"]+)"', src))
    refs: set[str] = set()
    for m in re.findall(r'data-src="([^"]+)"', src):
        refs |= {x.strip() for x in m.split(",") if x.strip()}
    missing = sorted(refs - ids)
    if missing:
        errors.append(f"data-src 引用了不存在的 id: {missing}")

    # ---- 2. 标签平衡 ----
    p = TagBalance()
    p.feed(src)
    if p.stack:
        errors.append(f"标签未闭合: {p.stack}")
    if p.errors:
        errors.append("标签错误: " + "; ".join(p.errors[:5]))

    # ---- 3. 答案块 / 注释块 ----
    n_ans = len(re.findall(r'class="ans[ "]', src))
    n_note = len(re.findall(r'class="(?:ans-note|an)"', src))
    if n_ans and n_ans != n_note:
        errors.append(f"答案块 {n_ans} 个，注释块 {n_note} 个，数量不一致")

    # ---- 4/5. 模板 A 专属 ----
    a = final_answer(src)
    has_final = a is not None
    total = 0
    if has_final:
        a = a or ""
        b = annotated_answer(src)
        total = len(a)
        if a != b:
            i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            errors.append(
                f"考场版与逐句版不一致（{len(a)} 字 vs {len(b)} 字），首个差异在第 {i} 字附近：\n"
                f"        考场版 …{a[max(0,i-15):i+15]}…\n"
                f"        逐句版 …{b[max(0,i-15):i+15]}…"
            )
        if limit is None:
            m = re.search(r"(\d+)\s*字以内", src)
            limit = int(m.group(1)) if m else None
        if limit is not None:
            if total > limit:
                errors.append(f"答案 {total} 字，超出上限 {limit} 字 {total - limit} 格")
            elif total < limit * 0.8:
                warns.append(f"答案仅 {total} 字，不足上限 {limit} 字的 80% —— 通常意味着漏点")

    # ---- 输出 ----
    print(f"文件      : {path}")
    print(f"元素 id   : {len(ids)} 个（被引用 {len(refs)} 个）")
    print(f"答案块    : {n_ans} 个 / 注释块 {n_note} 个")
    if has_final:
        print("模板      : A（考场版 + 对照工作台）")
        print(f"答案字数  : {total} 字" + (f"　上限 {limit} 字" if limit else ""))
        if limit and total <= limit:
            print(f"字数校验  : ✅ 在 {limit} 字以内")
    else:
        print("模板      : B（多版本解剖，无考场版面板）")

    if marks:
        print("\n三色成分统计（已排除点评块）：")
        for name, tot, c in section_ratios(src):
            line = "　".join(
                f"{MARK_NAMES[k]} {c[k]:>4} 字 {c[k]/tot*100:>5.1f}%" for k in MARK_CLASSES
            )
            print(f"  {name:<11} 共 {tot:>4} 字　{line}")

    for w in warns:
        print(f"⚠ 提示    : {w}")
    if errors:
        print("\n✗ 校验未通过：")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\n✅ 全部校验通过")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    marks = "--marks" in argv
    if marks:
        argv.remove("--marks")
    limit = None
    if "--limit" in argv:
        i = argv.index("--limit")
        limit = int(argv[i + 1])
        del argv[i : i + 2]
    return check(Path(argv[0]).expanduser().resolve(), limit, marks)


if __name__ == "__main__":
    raise SystemExit(main())
