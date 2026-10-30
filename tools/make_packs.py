"""一键生成「复习包」：每天的样例答卷 + 批改解析合成一个 PDF（4~6 页）。

用法：
    python tools\\make_packs.py

做的事：
1. 今天：tools/handout-sample.json + 申论/本次批改.md → docs/print/<今天>-sample-pack.pdf
2. 往期：tools/sample-<日期>.json + tools/review-<日期>.md（材料取 tools/sheets/<日期>-sheet.md，没有就用 申论/任务存档/<日期>.md）
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "docs" / "print"
TODAY_MD = ROOT / "申论" / "今日任务.md"


def today_str() -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", TODAY_MD.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def run(*args: str) -> int:
    r = subprocess.run([sys.executable, str(TOOLS / "make_handout.py"), *args],
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write((r.stdout or "") + (r.stderr or ""))
    return r.returncode


def main() -> int:
    today = today_str()
    built = []

    # 今天
    sample = TOOLS / f"sample-{today}.json"
    extra = ROOT / "申论" / "本次批改.md"
    if sample.exists() and extra.exists() and today:
        args = ["--sample", str(sample), "--extra", str(extra),
                "--name", f"{today}-sample-pack"]
        if run(*args) == 0:
            built.append(f"{today}-sample-pack")

    # 往期
    for js in sorted(TOOLS.glob("sample-*.json")):
        m = re.match(r"sample-(\d{4}-\d{2}-\d{2})\.json$", js.name)
        if not m:
            continue
        date = m.group(1)
        if date == today:
            continue
        extra = TOOLS / f"review-{date}.md"
        sheet = TOOLS / "sheets" / f"{date}-sheet.md"
        src = sheet if sheet.exists() else ROOT / "申论" / "任务存档" / f"{date}.md"
        if not (extra.exists() and src.exists()):
            continue
        args = ["--src", str(src), "--sample", str(js), "--extra", str(extra),
                "--name", f"{date}-sample-pack", "--break-t1"]
        if run(*args) == 0:
            built.append(f"{date}-sample-pack")

    for name in built:
        print(f"复习包 → {OUT / (name + '.pdf')}")
    return 0 if built else 1


if __name__ == "__main__":
    raise SystemExit(main())
