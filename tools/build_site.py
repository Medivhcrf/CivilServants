#!/usr/bin/env python3
"""把申论学习资料（Markdown）构建成可发布的静态站点。

产出到 docs/：
    - 每个页面的【桌面版】与【手机版】两份 HTML
    - index.html 总目录
    - assets/site.css 共用样式
    - 第 2 课图解课件（原样搬运 + 注入返回目录按钮）

用法:
    python3 tools/build_site.py
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"

SITE_TITLE = "申论学习库"
SITE_DESC = "申论系统学习资料 · 方法 · 练习 · 图解课件"

# ---------------------------------------------------------------- 页面清单

PAGES = [
    dict(slug="handbook", group="核心资料", title="学习手册",
         sub="三条真相 · 12 周路线图 · 方法速查 · 进度与成绩",
         src="申论/学习手册.md"),
    dict(slug="practice", group="核心资料", title="练习记录",
         sub="四道练习的存档：诊断结论 · 漏点出处 · 考场版参考答案",
         src="申论/练习记录.md"),
    dict(slug="points", group="方法", title="找点方法论",
         sub="四把钥匙 · 标点切分法 · 字数报警器 · 答题格式规范",
         src="skill/references/01-找点方法论.md"),
    dict(slug="types", group="方法", title="五大题型公式",
         sub="归纳概括 · 综合分析 · 提出对策 · 贯彻执行 · 大作文",
         src="skill/references/02-五大题型公式.md"),
    dict(slug="vocab", group="方法", title="表达与素材库",
         sub="政府话语词汇表 · 对策动词库 · 句式模板 · 大作文框架",
         src="skill/references/05-表达与素材库.md"),
    dict(slug="cards", group="方法", title="素材卡模板",
         sub="每天 15 分钟积累法 · 一篇文章一张卡",
         src="申论/素材/00-素材卡模板.md"),
    dict(slug="rubric", group="教学标准", title="批改评分标准",
         sub="评分档次 · 批改五块模板 · 常见失分诊断表",
         src="skill/references/03-批改评分标准.md"),
    dict(slug="nine-steps", group="教学标准", title="示范课九步法",
         sub="每道题解析必须做满的九步 · 三条质量红线",
         src="skill/references/06-详解标准-示范课九步法.md"),
]

# 图解课件：整份 HTML 搬运，不转换
DIAGRAM = dict(slug="diagram-02", group="核心资料", title="第 2 课图解课件",
               sub="解释型综合分析题 · 悬停答案句自动高亮材料原句",
               src="申论/第2课-综合分析-图解.html",
               preview="申论/第2课-图解-效果预览.png")

GROUP_ORDER = ["核心资料", "方法", "教学标准"]

# ---------------------------------------------------------------- Markdown 转换


def inline(text: str) -> str:
    """行内标记：code / 链接 / 粗体 / 斜体。"""
    text = html.escape(text, quote=False)
    codes: list[str] = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)

    def unstash(m):
        return "<code>" + codes[int(m.group(1))] + "</code>"

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def strip_md(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def build_list(items: list[tuple[int, bool, str]]) -> str:
    out: list[str] = []
    stack: list[tuple[int, str]] = []
    for indent, ordered, text in items:
        tag = "ol" if ordered else "ul"
        while stack and indent < stack[-1][0]:
            out.append(f"</{stack[-1][1]}>")
            stack.pop()
        if not stack or indent > stack[-1][0]:
            out.append(f"<{tag}>")
            stack.append((indent, tag))
        elif stack[-1][1] != tag:
            out.append(f"</{stack[-1][1]}>")
            stack.pop()
            out.append(f"<{tag}>")
            stack.append((indent, tag))
        out.append(f"<li>{inline(text)}</li>")
    while stack:
        out.append(f"</{stack[-1][1]}>")
        stack.pop()
    return "".join(out)


BLOCK_START = re.compile(r"^(#{1,4}\s|>|\||```|[-*]\s|\d+\.\s|-{3,}$|\*{3,}$)")


def md_to_html(md: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = md.split("\n")
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    i = 0
    n = 0

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        # 代码块
        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            n += 1
            hid = f"h-{n}"
            out.append(f'<h{lvl} id="{hid}">{inline(m.group(2))}</h{lvl}>')
            if lvl in (2, 3):
                toc.append((lvl, hid, strip_md(m.group(2))))
            i += 1
            continue

        # 分隔线
        if re.match(r"^(-{3,}|\*{3,})$", s):
            out.append("<hr>")
            i += 1
            continue

        # 表格
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            head = split_row(lines[i])
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(split_row(lines[i]))
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(
                '<div class="table-wrap"><table><thead><tr>'
                + th
                + "</tr></thead><tbody>"
                + trs
                + "</tbody></table></div>"
            )
            continue

        # 引用
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            inner = "<br>".join(inline(x) for x in buf if x)
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # 列表（含缩进续行）
        if re.match(r"^([-*]|\d+\.)\s+", s):
            items: list[tuple[int, bool, str]] = []
            while i < len(lines):
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if mm:
                    items.append((len(mm.group(1)), mm.group(2)[0].isdigit(), mm.group(3).strip()))
                    i += 1
                elif lines[i].strip() and items and len(lines[i]) - len(lines[i].lstrip()) > items[-1][0]:
                    ind, od, txt = items[-1]
                    items[-1] = (ind, od, txt + " " + lines[i].strip())
                    i += 1
                else:
                    break
            out.append(build_list(items))
            continue

        # 空行
        if not s:
            i += 1
            continue

        # 段落
        buf = []
        while i < len(lines) and lines[i].strip() and not BLOCK_START.match(lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
        else:
            i += 1

    return "\n".join(out), toc


# ---------------------------------------------------------------- 样式

CSS = r"""
:root{
  --bg:#f6f7f9; --card:#fff; --ink:#1f2430; --ink2:#5a6473; --ink3:#8b93a1; --line:#e3e7ee;
  --c-bg:#64748b; --c-meaning:#2563eb; --c-problem:#dc2626; --c-action:#059669;
  --c-conclusion:#7c3aed; --c-define:#d97706;
  --radius:14px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--ink);line-height:1.85;
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  -webkit-font-smoothing:antialiased;
}
a{color:#4338ca;text-decoration:none}
a:hover{text-decoration:underline}

/* ---------- 顶栏 ---------- */
.topbar{
  position:sticky;top:0;z-index:40;background:rgba(246,247,249,.93);
  backdrop-filter:saturate(180%) blur(10px);-webkit-backdrop-filter:saturate(180%) blur(10px);
  border-bottom:1px solid var(--line);
  padding:9px 0;padding-top:calc(9px + env(safe-area-inset-top));
}
.topbar .tb-in{max-width:1180px;margin:0 auto;padding:0 18px;display:flex;align-items:center;gap:12px}
.topbar .back{font-size:13.5px;white-space:nowrap}
.topbar .crumb{font-size:13px;color:var(--ink3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.topbar .switch{
  margin-left:auto;font-size:12.5px;border:1px solid var(--line);background:#fff;
  padding:4px 11px;border-radius:99px;white-space:nowrap;
}

/* ---------- 页头 ---------- */
.hero{
  background:linear-gradient(135deg,#1e293b 0%,#312e81 55%,#4c1d95 100%);
  color:#fff;padding:34px 18px 30px;margin-bottom:24px;
}
.hero .h-in{max-width:1180px;margin:0 auto}
.hero .kicker{
  display:inline-block;font-size:11.5px;letter-spacing:.14em;
  background:rgba(255,255,255,.16);padding:4px 11px;border-radius:99px;margin-bottom:13px;
}
.hero h1{margin:0 0 9px;font-size:27px;line-height:1.35;letter-spacing:-.01em}
.hero .sub{margin:0;color:#c7d2fe;font-size:14px}
.hero .meta{margin-top:15px;display:flex;flex-wrap:wrap;gap:9px}
.hero .meta span{
  font-size:12px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);
  padding:3px 10px;border-radius:99px;
}

/* ---------- 布局 ---------- */
.shell{max-width:1180px;margin:0 auto;padding:0 18px 70px}
.mode-desktop .shell{display:grid;grid-template-columns:236px minmax(0,1fr);gap:26px;align-items:start}
/* 总目录页不使用正文的双栏网格 */
.mode-desktop .shell.plain{display:block}

/* ---------- 目录 ---------- */
.toc{
  background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:15px 16px;font-size:13.5px;
}
.mode-desktop .toc{position:sticky;top:64px;max-height:calc(100vh - 90px);overflow-y:auto}
.toc .toc-title{font-size:11.5px;letter-spacing:.1em;color:var(--ink3);margin-bottom:9px}
.toc ol{list-style:none;margin:0;padding:0;counter-reset:t}
.toc li{margin:0}
.toc a{display:block;padding:5px 0;color:var(--ink2);border-bottom:1px dashed #eef1f5}
.toc li.lv3 a{padding-left:13px;font-size:12.8px;color:var(--ink3)}
.toc li:last-child a{border-bottom:none}
details.toc summary{
  cursor:pointer;font-size:13.5px;font-weight:600;color:var(--ink);
  padding:13px 16px;background:var(--card);border:1px solid var(--line);border-radius:12px;
  list-style:none;
}
details.toc summary::-webkit-details-marker{display:none}
details.toc summary::after{content:"▾";float:right;color:var(--ink3)}
details.toc[open] summary::after{content:"▴"}
details.toc[open] summary{border-radius:12px 12px 0 0;border-bottom:none}
.mode-mobile details.toc{margin-bottom:16px}
.mode-mobile details.toc .toc-body{
  background:var(--card);border:1px solid var(--line);border-top:none;
  border-radius:0 0 12px 12px;padding:6px 16px 12px;
}
.mode-mobile details.toc a{padding:9px 0}

/* ---------- 正文 ---------- */
.content{
  background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:28px 30px;box-shadow:0 1px 2px rgba(16,24,40,.04);min-width:0;
}
.content > *:first-child{margin-top:0}
h1,h2,h3,h4{line-height:1.45;letter-spacing:-.01em}
.content h1{font-size:24px;margin:34px 0 14px}
.content h2{
  font-size:19.5px;margin:34px 0 12px;padding-bottom:9px;
  border-bottom:2px solid #eef2ff;
}
.content h3{font-size:16px;margin:26px 0 9px;color:#312e81}
.content h4{font-size:14.5px;margin:20px 0 8px;color:var(--ink2)}
.content p{margin:0 0 13px}
.content ul,.content ol{margin:0 0 14px;padding-left:22px}
.content li{margin:4px 0}
.content li > ul,.content li > ol{margin:4px 0}
.content hr{border:none;border-top:1px dashed var(--line);margin:26px 0}
.content strong{color:#111827}
.content code{
  background:#f1f5f9;color:#334155;padding:1.5px 6px;border-radius:5px;
  font-size:.9em;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  word-break:break-word;
}
.content pre{
  background:#0f172a;color:#e2e8f0;padding:16px 18px;border-radius:11px;
  overflow-x:auto;-webkit-overflow-scrolling:touch;font-size:13px;line-height:1.7;
}
.content pre code{background:none;color:inherit;padding:0;font-size:inherit}
.content blockquote{
  margin:16px 0;padding:13px 18px;background:#f8fafc;
  border-left:3px solid var(--c-conclusion);border-radius:0 10px 10px 0;color:#334155;
}
.content blockquote p{margin:0}

/* 表格 */
.table-wrap{
  overflow-x:auto;-webkit-overflow-scrolling:touch;
  margin:16px 0;border:1px solid var(--line);border-radius:11px;
}
.content table{width:100%;border-collapse:collapse;font-size:13.8px;min-width:430px}
.content th,.content td{
  text-align:left;padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top;
}
.content th{background:#f9fafb;color:var(--ink2);font-weight:600;font-size:12.8px;white-space:nowrap}
.content tr:last-child td{border-bottom:none}
.scroll-hint{font-size:12px;color:var(--ink3);margin:-9px 0 16px;text-align:right}

/* ---------- 手机版专属 ---------- */
.mode-mobile{font-size:16.5px}
.mode-mobile .shell{padding:0 15px 56px;max-width:760px}
.mode-mobile .content{padding:20px 17px;border-radius:12px}
.mode-mobile .hero{padding:26px 16px 24px}
.mode-mobile .hero h1{font-size:22px}
.mode-mobile .content h1{font-size:20px}
.mode-mobile .content h2{font-size:17.5px;margin-top:28px}
.mode-mobile .content h3{font-size:15.5px}
.mode-mobile .content table{font-size:14px;min-width:400px}
.mode-mobile .content th,.mode-mobile .content td{padding:11px 13px}
.mode-mobile .content ul,.mode-mobile .content ol{padding-left:20px}
.mode-mobile .content pre{font-size:12.5px;padding:14px}

/* ---------- 总目录 ---------- */
.idx-group{margin:0 0 30px}
.idx-group > h2{
  font-size:15px;color:var(--ink2);margin:0 0 13px;letter-spacing:.06em;
  display:flex;align-items:center;gap:9px;
}
.idx-group > h2::after{content:"";flex:1;height:1px;background:var(--line)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;align-items:start}
.card{
  background:var(--card);border:1px solid var(--line);border-radius:13px;padding:17px 18px;
  transition:.18s;box-shadow:0 1px 2px rgba(16,24,40,.04);
}
.card:hover{border-color:#c7d2fe;box-shadow:0 6px 18px rgba(67,56,202,.09);transform:translateY(-1px)}
.card .card-title{margin:0 0 6px;font-size:16px;font-weight:600;display:block;color:var(--ink)}
.card:hover .card-title{color:#4338ca}
.card .card-sub{font-size:13.2px;color:var(--ink2);margin:0 0 13px;line-height:1.65}
.card .card-links{display:flex;gap:8px;flex-wrap:wrap}
.card .card-links a{
  font-size:12.5px;border:1px solid var(--line);border-radius:99px;padding:4px 13px;
  background:#fbfcfe;color:var(--ink2);
}
.card .card-links a.pri{background:#eef2ff;border-color:#c7d2fe;color:#4338ca;font-weight:600}
.card .card-links a:hover{text-decoration:none;background:#eef2ff;border-color:#c7d2fe;color:#4338ca}
.card .thumb{
  display:block;width:100%;height:132px;object-fit:cover;object-position:top;
  border-radius:9px;border:1px solid var(--line);margin-bottom:13px;
}
.mode-mobile .cards{grid-template-columns:1fr}
.mode-mobile .card .card-links a{padding:7px 15px;font-size:13.5px}

.notice{
  background:#fffbeb;border-left:3px solid var(--c-define);border-radius:0 10px 10px 0;
  padding:13px 17px;font-size:13.5px;color:#92400e;margin:0 0 28px;
}
.foot{
  text-align:center;color:var(--ink3);font-size:12.5px;
  padding:26px 0 8px;border-top:1px solid var(--line);margin-top:34px;
}

/* ---------- 手机窄屏适配 ---------- */
@media (max-width:760px){
  .hero h1{font-size:23px}
  .cards{grid-template-columns:1fr}
}
""".strip()


# ---------------------------------------------------------------- 模板


def page_shell(*, title: str, sub: str, kicker: str, body: str, toc: str,
               mode: str, slug: str, meta: list[str], toc_count: int) -> str:
    other = f"{slug}.html" if mode == "mobile" else f"{slug}-m.html"
    other_label = "桌面版" if mode == "mobile" else "手机版"
    toc_block = (
        f'<details class="toc"><summary>本页目录（{toc_count} 节）</summary>'
        f'<div class="toc-body"><ol>{toc}</ol></div></details>'
        if mode == "mobile"
        else f'<nav class="toc"><div class="toc-title">本页目录（{toc_count} 节）</div><ol>{toc}</ol></nav>'
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#312e81">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="description" content="{html.escape(sub)}">
<title>{html.escape(title)} · {SITE_TITLE}</title>
<link rel="stylesheet" href="assets/site.css">
</head>
<body class="mode-{mode}">

<div class="topbar">
  <div class="tb-in">
    <a class="back" href="index.html">← 总目录</a>
    <span class="crumb">{html.escape(title)}</span>
    <a class="switch" href="{other}">{other_label}</a>
  </div>
</div>

<header class="hero">
  <div class="h-in">
    <span class="kicker">{html.escape(kicker)}</span>
    <h1>{html.escape(title)}</h1>
    <p class="sub">{html.escape(sub)}</p>
    <div class="meta">{''.join(f'<span>{html.escape(m)}</span>' for m in meta)}</div>
  </div>
</header>

<div class="shell">
  {toc_block}
  <main class="content">
{body}
  </main>
</div>

<footer class="foot">
  {SITE_TITLE} · 本页为{'手机版' if mode == 'mobile' else '桌面版'}
  ｜ <a href="{other}">切换到{other_label}</a>
  ｜ <a href="https://github.com/Medivhcrf/CivilServants">GitHub 仓库</a>
</footer>

</body>
</html>
"""


def build_toc(toc: list[tuple[int, str, str]], mode: str, table_count: int) -> str:
    items = "".join(
        f'<li class="lv{lvl}"><a href="#{hid}">{html.escape(txt)}</a></li>' for lvl, hid, txt in toc
    )
    return items


def build_index(mode: str) -> str:
    groups: dict[str, list[dict]] = {}
    for p in PAGES:
        groups.setdefault(p["group"], []).append(p)
    groups.setdefault(DIAGRAM["group"], []).insert(0, {**DIAGRAM, "is_diagram": True})

    sections = []
    for g in GROUP_ORDER:
        if g not in groups:
            continue
        cards = []
        for p in groups[g]:
            thumb = (
                '<img class="thumb" src="assets/preview-02.png" alt="课件预览">'
                if p.get("is_diagram") else ""
            )
            if p.get("is_diagram"):
                links = f'<a class="pri" href="{p["slug"]}.html">打开课件</a>'
            elif mode == "mobile":
                links = (
                    f'<a class="pri" href="{p["slug"]}-m.html">手机版</a>'
                    f'<a class="sec" href="{p["slug"]}.html">桌面版</a>'
                )
            else:
                links = (
                    f'<a class="pri" href="{p["slug"]}.html">桌面版</a>'
                    f'<a class="sec" href="{p["slug"]}-m.html">手机版</a>'
                )
            cards.append(f"""      <article class="card">
        {thumb}
        <a class="card-title" href="{p['slug']}.html">{html.escape(p['title'])}</a>
        <p class="card-sub">{html.escape(p['sub'])}</p>
        <div class="card-links">{links}</div>
      </article>""")
        sections.append(
            f'  <section class="idx-group">\n    <h2>{html.escape(g)}</h2>\n    <div class="cards">\n'
            + "\n".join(cards)
            + "\n    </div>\n  </section>"
        )

    body = "\n".join(sections)

    css_common = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#312e81">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="description" content="SITEDESC">
<title>SITETITLE</title>
<link rel="stylesheet" href="assets/site.css">
</head>
<body class="MODE">
<div class="hero">
  <div class="h-in">
    <span class="kicker">公务员考试 · 申论</span>
    <h1>申论学习库</h1>
    <p class="sub">要点抄材料，骨架自己搭 · 一句一勾 · 字数实测 · 正反两层对称</p>
    <div class="meta"><span>8 份资料</span><span>桌面版 + 手机版</span><span>1 份图解课件</span></div>
  </div>
</div>
<div class="shell plain">
  <div class="notice">
    NOTICE
  </div>
BODY
  <footer class="foot">
    申论学习库 ｜ <a href="https://github.com/Medivhcrf/CivilServants">GitHub 仓库</a>
  </footer>
</div>
</body>
</html>
"""
    notice = (
        "<strong>手机上浏览？</strong>每份资料都有手机版（字号更大、单栏排版、目录可折叠）。"
        "点卡片上的<b>手机版</b>即可。桌面版在手机上也能看，会自动缩放。"
        if mode == "desktop" else
        "<strong>你在看手机版。</strong>手机版是单栏大字号排版，目录可折叠、表格可左右滑动。"
        "想用电脑看，点卡片上的<b>桌面版</b>。"
    )
    return (
        css_common.replace("SITEDESC", SITE_DESC)
        .replace("SITETITLE", SITE_TITLE + (" · 总目录（手机版）" if mode == "mobile" else " · 总目录"))
        .replace("MODE", "mode-mobile" if mode == "mobile" else "mode-desktop")
        .replace("NOTICE", notice)
        .replace("BODY", body)
    )


# ---------------------------------------------------------------- 主流程


def main() -> int:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "site.css").write_text(CSS, encoding="utf-8")

    built = []
    for p in PAGES:
        src = ROOT / p["src"]
        if not src.is_file():
            print(f"  ✗ 源文件缺失，跳过：{p['src']}")
            continue
        md = src.read_text(encoding="utf-8")
        body, toc = md_to_html(md)
        toc_html = build_toc(toc, "desktop", body.count("<table"))

        n_tables = body.count('class="table-wrap"')
        for mode, suffix in (("desktop", ""), ("mobile", "-m")):
            b = body
            if mode == "mobile" and n_tables:
                b = b.replace(
                    "</tbody></table></div>",
                    '</tbody></table></div><div class="scroll-hint">← 表格可左右滑动 →</div>',
                )
            out = page_shell(
                title=p["title"], sub=p["sub"], kicker=p["group"],
                body=b, toc=toc_html, mode=mode, slug=p["slug"], toc_count=len(toc),
                meta=[f"{len(body)} 字符", "桌面版" if mode == "desktop" else "手机版"],
            )
            (DOCS / f"{p['slug']}{suffix}.html").write_text(out, encoding="utf-8")
        built.append((p["slug"], len(toc)))
        print(f"  ✓ {p['title']:<14} 桌面版 + 手机版　（{len(toc)} 个目录项）")

    # 图解课件：整份搬运 + 注入返回目录按钮
    dsrc = ROOT / DIAGRAM["src"]
    if dsrc.is_file():
        dh = dsrc.read_text(encoding="utf-8")
        inject = (
            '<a href="index.html" style="position:fixed;left:14px;bottom:14px;z-index:99;'
            "background:rgba(30,41,59,.9);color:#fff;font-size:13px;padding:8px 15px;"
            'border-radius:99px;text-decoration:none;'
            'font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\',sans-serif;'
            'box-shadow:0 4px 14px rgba(0,0,0,.25);backdrop-filter:blur(6px)">← 总目录</a>'
        )
        dh = dh.replace("</body>", inject + "\n</body>")
        (DOCS / f"{DIAGRAM['slug']}.html").write_text(dh, encoding="utf-8")
        print(f"  ✓ {DIAGRAM['title']:<14} 图解课件（响应式，两端通用）")

    pv = ROOT / DIAGRAM["preview"]
    if pv.is_file():
        shutil.copy2(pv, ASSETS / "preview-02.png")

    (DOCS / "index.html").write_text(build_index("desktop"), encoding="utf-8")
    (DOCS / "index-m.html").write_text(build_index("mobile"), encoding="utf-8")
    print("  ✓ 总目录       index.html + index-m.html")

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"\n构建完成 → {DOCS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
