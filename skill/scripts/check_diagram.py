#!/usr/bin/env python3
"""校验申论图解课件（HTML）的结构一致性。

用法:
    python3 check_diagram.py <file.html> [--limit 250]

检查五项:
    1. 所有 data-src 引用的材料句 id 都存在
    2. HTML 标签闭合平衡
    3. 答案块数量 == 注释块数量
    4. 「完整答案（考场版）」与「逐句注释」版逐字一致
    5. 答案字数实测（并检查是否超出上限）

退出码: 0 全部通过 / 1 存在错误
"""

from __future__ import annotations

import re
import sys
import html.parser
from pathlib import Path

VOID = {"meta", "br", "hr", "img", "input", "link", "source", "area", "base", "col", "embed", "track", "wbr"}


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def norm(s: str) -> str:
    """去掉所有空白，用于逐字比对与字数实测。"""
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


def check(path: Path, limit: int | None) -> int:
    if not path.is_file():
        print(f"✗ 文件不存在: {path}")
        return 1

    src = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warns: list[str] = []

    # ---- 1. data-src <-> id ----
    ids = set(re.findall(r'id="(m\d+-\d+)"', src))
    refs: set[str] = set()
    for m in re.findall(r'data-src="([^"]+)"', src):
        refs |= {x.strip() for x in m.split(",") if x.strip()}
    missing = sorted(refs - ids)
    if missing:
        errors.append(f"data-src 引用了不存在的 id: {missing}")
    unused = sorted(ids - refs)
    if unused:
        warns.append(f"以下材料句未被任何答案句引用（确认是否为有意省略的数据句/过渡句）: {unused}")

    # ---- 2. 标签平衡 ----
    p = TagBalance()
    p.feed(src)
    if p.stack:
        errors.append(f"标签未闭合: {p.stack}")
    if p.errors:
        errors.append("标签错误: " + "; ".join(p.errors[:5]))

    # ---- 3. 答案块 / 注释块 ----
    n_ans = len(re.findall(r'class="ans[ "]', src))
    n_note = len(re.findall(r'class="ans-note"', src))
    if n_ans != n_note:
        errors.append(f"答案块 {n_ans} 个，注释块 {n_note} 个，数量不一致")
    if n_ans == 0:
        errors.append("未找到任何答案块（class=\"ans\"）")

    # ---- 4. 考场版 vs 逐句版 逐字一致 ----
    final = re.search(r'<div class="final">(.*?)</div>\s*<div class="bench">', src, re.S)
    if not final:
        errors.append("未找到「完整答案（考场版）」面板（<div class=\"final\"> ... <div class=\"bench\">）")
        a = b = ""
    else:
        # 去掉「① 释义」这类分段标签，它不属于答案正文
        body = re.sub(r'<span class="seg[^"]*"[^>]*>.*?</span>', "", final.group(1), flags=re.S)
        a = norm("".join(re.findall(r"<p>(.*?)</p>", body, re.S)))
        b = norm("".join(re.findall(r'<div class="ans-text">(.*?)</div>', src, re.S)))
        if a != b:
            i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            errors.append(
                f"考场版与逐句版不一致（{len(a)} 字 vs {len(b)} 字），"
                f"首个差异在第 {i} 字附近：\n        考场版 …{a[max(0,i-15):i+15]}…\n"
                f"        逐句版 …{b[max(0,i-15):i+15]}…"
            )

    # ---- 5. 字数实测 ----
    total = len(a)
    if limit is None:
        m = re.search(r"(\d+)\s*字以内", src)
        limit = int(m.group(1)) if m else None

    print(f"文件      : {path}")
    print(f"材料句    : {len(ids)} 个（被引用 {len(refs)} 个）")
    print(f"答案块    : {n_ans} 个 / 注释块 {n_note} 个")
    print(f"答案字数  : {total} 字" + (f"　上限 {limit} 字" if limit else ""))

    if limit is not None:
        if total > limit:
            errors.append(f"答案 {total} 字，超出上限 {limit} 字 {total - limit} 格")
        elif total < limit * 0.8:
            warns.append(f"答案仅 {total} 字，不足上限 {limit} 字的 80% —— 通常意味着漏点")
        else:
            print(f"字数校验  : ✅ 在 {limit} 字以内")

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
    limit = None
    if "--limit" in argv:
        i = argv.index("--limit")
        limit = int(argv[i + 1])
        del argv[i : i + 2]
    return check(Path(argv[0]).expanduser().resolve(), limit)


if __name__ == "__main__":
    raise SystemExit(main())
