#!/usr/bin/env python3
"""练习解析图解生成器。

把每道练习的解析定义成数据，产出与课件同规格的富交互 HTML：
    - 材料功能色标（六色）
    - 答案三色解剖（抄／自／概）
    - 升格版 + 悬停溯源
    - 结构骨架、漏点清单、带走的一个动作

三色占比由本脚本从 HTML 里**实算**，不是手填，保证与标记永远一致。

用法:
    python3 tools/build_diagrams.py            # 生成全部
    python3 tools/build_diagrams.py p1         # 只生成某一份
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "申论"

# ══════════════════════════════════════════════════════════ 样式

CSS = r"""
:root{
  --bg:#f6f7f9; --card:#fff; --ink:#1f2430; --ink2:#5a6473; --ink3:#8b93a1; --line:#e3e7ee;
  --c-bg:#64748b; --c-meaning:#2563eb; --c-problem:#dc2626; --c-action:#059669;
  --c-conclusion:#7c3aed; --c-define:#d97706;
  --mk-copy:#e2e9f4; --mk-copy-line:#4b5f7a;
  --mk-own:#fdecc8;  --mk-own-line:#b45309;
  --mk-cond:#d6f5e3; --mk-cond-line:#047857;
  --radius:14px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.85;font-size:15px;
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 80px}
a{color:#4338ca}
header{background:linear-gradient(135deg,#1e293b 0%,#312e81 55%,#4c1d95 100%);color:#fff;padding:42px 20px 36px}
header .in{max-width:1180px;margin:0 auto}
.kicker{display:inline-block;font-size:11.5px;letter-spacing:.14em;background:rgba(255,255,255,.16);
  padding:4px 12px;border-radius:99px;margin-bottom:15px}
header h1{margin:0 0 10px;font-size:28px;line-height:1.35;letter-spacing:-.01em}
header .sub{margin:0;color:#c7d2fe;font-size:14.5px}
header .meta{margin-top:17px;display:flex;flex-wrap:wrap;gap:9px}
header .meta span{font-size:12.5px;background:rgba(255,255,255,.1);
  border:1px solid rgba(255,255,255,.18);padding:4px 11px;border-radius:99px}
.backbtn{position:fixed;left:14px;bottom:14px;z-index:99;background:rgba(30,41,59,.9);color:#fff;
  font-size:13px;padding:8px 15px;border-radius:99px;text-decoration:none;
  box-shadow:0 4px 14px rgba(0,0,0,.25);backdrop-filter:blur(6px)}
.legend{position:sticky;top:0;z-index:50;background:rgba(246,247,249,.95);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
  padding:11px 20px;margin:0 -20px 26px}
.legend .lg-in{max-width:1180px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.legend .t{font-size:12px;color:var(--ink3);letter-spacing:.05em;margin-right:2px}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;padding:3px 11px;
  border-radius:99px;background:#fff;border:1px solid var(--line)}
.chip i{width:11px;height:11px;border-radius:3px;display:inline-block}
.chip.d i{background:var(--c-bg)} .chip.m i{background:var(--c-meaning)} .chip.p i{background:var(--c-problem)}
.chip.a i{background:var(--c-action)} .chip.c i{background:var(--c-conclusion)}
.sep{width:1px;height:16px;background:var(--line);margin:0 4px}
section{margin-bottom:32px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:26px 28px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
h2{font-size:19px;margin:0 0 6px;display:flex;align-items:center;gap:11px;letter-spacing:-.01em}
h2 .num{flex:none;width:28px;height:28px;border-radius:9px;background:#eef2ff;color:#4338ca;
  font-size:13px;display:grid;place-items:center;font-weight:700}
.h2sub{color:var(--ink3);font-size:13px;margin:0 0 20px;padding-left:39px}
h3{font-size:15px;margin:22px 0 10px}
p{margin:0 0 12px}
.mk-copy,.mk-own,.mk-cond{padding:1px 3px;border-radius:4px;font-weight:600}
.mk-copy{background:var(--mk-copy);border-bottom:2px solid var(--mk-copy-line)}
.mk-own{background:var(--mk-own);border-bottom:2px dashed var(--mk-own-line)}
.mk-cond{background:var(--mk-cond);border-bottom:2px dotted var(--mk-cond-line)}
.mk-copy::after,.mk-own::after,.mk-cond::after{font-size:9.5px;vertical-align:super;margin-left:1px;font-weight:700;opacity:.75}
.mk-copy::after{content:"抄"} .mk-own::after{content:"自"} .mk-cond::after{content:"概"}
.plain-mk .mk-copy::after,.plain-mk .mk-own::after,.plain-mk .mk-cond::after{content:""}
.qlink{display:inline-flex;align-items:center;gap:5px;background:#4338ca!important;color:#fff!important;text-decoration:none;font-weight:600}
.qlink:hover{background:#3730a3!important}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:14px 0;border:1px solid var(--line);border-radius:11px}
.tw table{min-width:600px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f9fafb;color:var(--ink2);font-weight:600;font-size:12.5px;white-space:nowrap}
tr:last-child td{border-bottom:none}
.fn{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:99px;font-weight:600;white-space:nowrap}
.f-bg{background:#f1f5f9;color:#475569}.f-meaning{background:#eff6ff;color:var(--c-meaning)}
.f-problem{background:#fef2f2;color:var(--c-problem)}.f-action{background:#ecfdf5;color:var(--c-action)}
.f-conclusion{background:#f5f3ff;color:var(--c-conclusion)}.f-define{background:#fffbeb;color:var(--c-define)}
.para{margin-bottom:14px;padding:11px 14px;border-left:3px solid var(--line);border-radius:0 8px 8px 0;background:#fff}
.para-bg{border-left-color:var(--c-bg)}.para-meaning{border-left-color:var(--c-meaning)}
.para-problem{border-left-color:var(--c-problem)}.para-action{border-left-color:var(--c-action)}
.para-conclusion{border-left-color:var(--c-conclusion)}
.para .ph{display:flex;align-items:center;gap:9px;margin-bottom:6px}
.para .pn{font-size:11.5px;color:var(--ink3);font-weight:700}
.para .pt{font-size:13.5px;line-height:1.9;color:#2c3340}
.s{transition:background .18s,box-shadow .18s;border-radius:4px;padding:1px 0}
.s.hl{background:#fff3c4;box-shadow:0 0 0 3px #fff3c4}
.ans{background:#fff;border:1px solid var(--line);border-left:3px solid var(--line);
  border-radius:0 9px 9px 0;padding:13px 15px;margin-bottom:11px;cursor:pointer;transition:.2s}
.ans:hover,.ans.on{background:#fffdf5;border-color:#fcd34d;box-shadow:0 2px 10px rgba(217,119,6,.1)}
.ans[data-kind="own"]{border-left-color:var(--c-define)}
.ans[data-kind="copy"]{border-left-color:var(--c-bg)}
.ans[data-kind="cond"]{border-left-color:var(--c-action)}
.ans.nosrc{cursor:default}
.ans.nosrc:hover{background:#fff;border-color:var(--line);box-shadow:none}
.ah{display:flex;align-items:center;gap:8px;margin-bottom:7px;flex-wrap:wrap}
.ab{font-size:11px;font-weight:700;padding:2px 9px;border-radius:99px}
.asrc{font-size:11.5px;color:var(--ink3);margin-left:auto}
.at{font-size:14px;line-height:2;color:#2c3340}
.an{font-size:12.5px;color:var(--ink2);margin-top:9px;padding-top:9px;
  border-top:1px dashed var(--line);line-height:1.7;display:none}
.ans:hover .an,.ans.on .an,.ans.nosrc .an{display:block}
.an b{color:#b45309}
.flow{display:grid;gap:10px}
.frow{display:grid;grid-template-columns:128px 1fr;gap:14px;align-items:center}
.fl{font-size:12.5px;font-weight:700;text-align:right;padding-right:4px}
.fb{border-radius:10px;padding:11px 15px;font-size:13.5px}
.fl-d{background:#fffbeb;border:1px solid #fde68a;color:#92400e}
.fl-p{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}
.fl-a{background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46}
.fl-c{background:#f5f3ff;border:1px solid #ddd6fe;color:#5b21b6}
.arrow{grid-column:1/-1;text-align:center;color:var(--ink3);font-size:15px;line-height:1}
.bar{display:flex;height:30px;border-radius:9px;overflow:hidden;border:1px solid var(--line);margin:12px 0 8px}
.bar div{display:grid;place-items:center;font-size:12px;font-weight:700;color:#1f2937;white-space:nowrap}
.b-copy{background:var(--mk-copy)}.b-own{background:var(--mk-own)}.b-cond{background:var(--mk-cond)}
.barlg{display:flex;flex-wrap:wrap;gap:16px;font-size:12.5px;color:var(--ink2)}
.tip{background:#f0fdf4;border-left:3px solid var(--c-action);border-radius:0 9px 9px 0;
  padding:13px 17px;font-size:13.5px;color:#065f46;margin-top:14px}
.warn{background:#fffbeb;border-left:3px solid var(--c-define);border-radius:0 9px 9px 0;
  padding:13px 17px;font-size:13.5px;color:#92400e;margin-top:14px}
.bad{border:1px solid #fecaca;background:#fff5f5;border-radius:12px;padding:16px 18px}
.bad ul{margin:10px 0 0;padding-left:0;list-style:none}
.bad li{font-size:13.5px;color:#991b1b;padding:7px 0 7px 26px;position:relative;border-top:1px dashed #fecaca}
.bad li:before{content:"✕";position:absolute;left:4px;top:7px;color:#dc2626;font-weight:700}
.prog{display:grid;gap:9px}
.prow{display:grid;grid-template-columns:96px 1fr 64px;gap:12px;align-items:center;font-size:13px}
.pname{font-weight:600;color:var(--ink2)}
.pbar{height:22px;border-radius:6px;background:#eef1f5;overflow:hidden}
.pbar i{display:block;height:100%;border-radius:6px}
.pscore{text-align:right;font-weight:700;color:#4338ca;font-size:13px}
/* 逐点对照 */
.jd{display:inline-block;font-size:11px;font-weight:700;padding:2px 9px;border-radius:99px;white-space:nowrap}
.jd-hit{background:#d1fae5;color:#065f46}
.jd-part{background:#fef3c7;color:#92400e}
.jd-err{background:#fee2e2;color:#991b1b}
.jd-miss{background:#f1f5f9;color:#64748b}
.cmp td.mine-miss{color:var(--ink3);font-style:italic}
.cmp td.mine-err{color:#991b1b}
.cmp td.mine-hit{color:#065f46}
.sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(104px,1fr));gap:10px;margin:16px 0}
.sum div{background:#fbfcfe;border:1px solid var(--line);border-radius:11px;padding:12px 14px;text-align:center}
.sum .n{font-size:23px;font-weight:700;line-height:1.25}
.sum .l{font-size:12px;color:var(--ink3);margin-top:2px}
/* 引号高亮 */
.k-quote{background:#fef3c7;color:#92400e;padding:1px 3px;border-radius:4px;font-weight:600}
.refbox{background:#f8f9ff;border:1px solid #c7d2fe;border-radius:12px;padding:18px 20px;margin:14px 0}
.refbox .rh{font-size:12.5px;letter-spacing:.08em;color:#4338ca;margin-bottom:10px;font-weight:700}
.refbox p{font-size:14px;line-height:1.95;color:#2c3340;margin:0 0 10px}
.refbox p:last-child{margin-bottom:0}
.refbox .warnline{font-size:12px;color:var(--ink3);margin-top:12px;padding-top:10px;border-top:1px dashed #c7d2fe}
@media (max-width:900px){
  .bench2{grid-template-columns:1fr!important}
  .frow{grid-template-columns:1fr;gap:5px}
  .fl{text-align:left}
  .card{padding:20px 18px}
  header h1{font-size:22px}
  .bar{height:26px}.bar div{font-size:10.5px}
  .prow{grid-template-columns:72px 1fr 56px}
}
"""

def hl_quotes(t: str) -> str:
    """把材料里带引号的提法高亮 —— 引号即采分词信号。"""
    return re.sub(r'"([^"]{2,40})"', r'<span class="k-quote">"\1"</span>', t)


MARK_RE = re.compile(r'<span class="(mk-copy|mk-own|mk-cond)">(.*?)</span>', re.S)


def _text(s: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", s))


def mark_stats(blocks: list[dict]) -> dict:
    """从答案块的 HTML 实算三色占比。"""
    counts = {"mk-copy": 0, "mk-own": 0, "mk-cond": 0}
    total = 0
    for b in blocks:
        html = b.get("html", "")
        total += len(_text(html))
        for cls, inner in MARK_RE.findall(html):
            counts[cls] += len(_text(inner))
    return {"total": total, "counts": counts}


def bars(name: str, st: dict) -> str:
    t = st["total"] or 1
    c, o, k = st["counts"]["mk-copy"], st["counts"]["mk-own"], st["counts"]["mk-cond"]
    pc, po, pk = c / t * 100, o / t * 100, k / t * 100
    rest = max(0.0, 100 - pc - po - pk)
    return f"""      <div style="font-size:12.5px;color:var(--ink3);margin-bottom:5px">{name}（{st['total']} 字）</div>
      <div class="bar">
        <div class="b-copy" style="width:{pc:.1f}%">抄 {pc:.0f}%</div>
        <div class="b-cond" style="width:{pk:.1f}%">概 {pk:.0f}%</div>
        <div class="b-own" style="width:{po:.1f}%">自 {po:.0f}%</div>
        <div style="background:#eef1f5;width:{rest:.1f}%"></div>
      </div>"""


# ══════════════════════════════════════════════════════════ 渲染


def render(d: dict) -> str:
    st_student = mark_stats(d["student"])
    st_upgrade = mark_stats(d["upgrade"])

    # 材料
    paras = []
    for p in d["material"]:
        sents = "".join(f'<span class="s" id="{sid}">{hl_quotes(txt)}</span>' for sid, txt in p["sents"])
        paras.append(f"""        <div class="para para-{p['fn']}">
          <div class="ph"><span class="pn">{p['no']}</span><span class="fn f-{p['fn']}">{p['fnlabel']}</span></div>
          <div class="pt">{sents}</div>
        </div>""")
    material_html = "\n".join(paras)

    # 学生答案
    stu = []
    for b in d["student"]:
        stu.append(f"""        <div class="ans nosrc" data-kind="{b['kind']}">
          <div class="ah"><span class="ab" style="background:{b['bg']};color:{b['fg']}">{b['label']}</span>
            <span class="asrc">{b.get('wc','')}</span></div>
          <div class="at">{b['html']}</div>
          <div class="an"><b>点评：</b>{b['note']}</div>
        </div>""")
    student_html = "\n".join(stu)

    # 升格版
    up = []
    for b in d["upgrade"]:
        up.append(f"""        <div class="ans" data-kind="{b['kind']}" data-src="{b.get('src','')}">
          <div class="ah"><span class="ab" style="background:{b['bg']};color:{b['fg']}">{b['label']}</span>
            <span class="asrc">{b.get('src_label','')}</span></div>
          <div class="at">{b['html']}</div>
          <div class="an"><b>成分：</b>{b['note']}</div>
        </div>""")
    upgrade_html = "\n".join(up)

    # 结构
    rows = []
    for i, r in enumerate(d["structure"]):
        if i:
            rows.append('      <div class="arrow">↓</div>')
        rows.append(f"""      <div class="frow">
        <div class="fl" style="color:var(--c-{r['tone']})">{r['label']}</div>
        <div class="fb fl-{r['cls']}">{r['body']}</div>
      </div>""")
    structure_html = "\n".join(rows)

    # 漏点
    gaps = "\n".join(
        f"""          <tr><td>{g['item']}</td><td>{g['src']}</td><td>{g['how']}</td><td>{g.get('value','')}</td></tr>"""
        for g in d["gaps"]
    )

    # 带走动作
    takeaways = "\n".join(
        f"""      <div class="frow">
        <div class="fl" style="color:var(--ink2)">动作 {i}</div>
        <div class="fb" style="background:#f8fafc;border:1px solid var(--line)">{t}</div>
      </div>"""
        for i, t in enumerate(d["takeaways"], 1)
    )

    # 逐点对照
    JD = {"hit": ("命中", "jd-hit"), "part": ("不完整", "jd-part"),
          "err": ("错误", "jd-err"), "miss": ("漏", "jd-miss")}
    cnt = {k: 0 for k in JD}
    crow = []
    for c in d.get("compare", []):
        cnt[c["j"]] += 1
        lb, cl = JD[c["j"]]
        cls = {"hit": "mine-hit", "part": "", "err": "mine-err", "miss": "mine-miss"}[c["j"]]
        crow.append(f"""          <tr>
            <td>{c['point']}</td>
            <td>{c['ref']}</td>
            <td class="{cls}">{c['mine']}</td>
            <td><span class="jd {cl}">{lb}</span></td>
            <td>{c['note']}</td>
          </tr>""")
    compare_rows = "\n".join(crow)
    ctot = sum(cnt.values()) or 1
    summary = "".join(
        f'<div><div class="n" style="color:{col}">{cnt[k]}</div>'
        f'<div class="l">{JD[k][0]} {cnt[k]/ctot*100:.0f}%</div></div>'
        for k, col in [("hit", "#059669"), ("part", "#d97706"), ("err", "#dc2626"), ("miss", "#64748b")]
    )
    reference_html = "".join(f"<p>{x}</p>" for x in d.get("reference", []))

    chips = "".join(
        f"<span>{c}</span>" for c in
        [f"你的答案 {st_student['total']} 字", f"升格版 {st_upgrade['total']} 字"] + d["chips"]
    ) + '<a class="qlink" href="引号与抽象概念-图解.html">引号规则 →</a>'
    # 伪装层：浏览器标签只显示技术文档名
    tab = "视觉识别 · " + d["kicker"].split("·")[-1].strip()

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{tab}</title>
<style>{CSS}</style>
</head>
<body class="plain-mk">

<header>
  <div class="in">
    <span class="kicker">{d['kicker']}</span>
    <h1>{d['h1']}</h1>
    <p class="sub">{d['sub']}</p>
    <div class="meta">{chips}</div>
  </div>
</header>

<div class="wrap">

  <div class="legend">
    <div class="lg-in">
      <span class="t">段落功能</span>
      <span class="chip d"><i></i>背景</span>
      <span class="chip m"><i></i>意义</span>
      <span class="chip p"><i></i>问题</span>
      <span class="chip a"><i></i>做法</span>
      <span class="chip c"><i></i>结论</span>
      <span class="sep"></span>
      <span class="t">每句话的成分</span>
      <span class="chip"><i style="background:var(--mk-copy)"></i><b>抄</b>　材料原词</span>
      <span class="chip"><i style="background:var(--mk-own)"></i><b>自</b>　自己写的骨架</span>
      <span class="chip"><i style="background:var(--mk-cond)"></i><b>概</b>　从材料概括上升</span>
    </div>
  </div>

  <section class="card">
    <h2><span class="num">1</span>你的答案 · 三色解剖（{st_student['total']} 字）</h2>
    <p class="h2sub">底色即标记：<b>抄</b>（灰蓝实线）／<b>自</b>（琥珀虚线）／<b>概</b>（绿点线）。{d.get('student_hint','')}</p>
{student_html}

    <h3 style="margin-top:26px">成分实测对比</h3>
    <p style="font-size:12.5px;color:var(--ink3);margin:0 0 10px">下面数字由脚本逐字统计，不是估算。</p>
{bars('你的答案', st_student)}
{bars('升格版', st_upgrade)}
    <div class="warn" style="margin-top:18px">{d['ratio_note']}</div>
  </section>

  <section class="card">
    <h2><span class="num">2</span>参考答案 × 你的答案 · 逐点对照</h2>
    <p class="h2sub">{d['compare_sub']}</p>
    <div class="sum">{summary}</div>
    <div class="refbox">
      <div class="rh">参考答案（教学用，非官方评分标准）</div>
{reference_html}
      <div class="warnline">{d['ref_warn']}</div>
    </div>
    <div class="tw">
      <table class="cmp">
        <thead><tr><th>采分点</th><th>参考答案的表述</th><th>你的答案</th><th>判定</th><th>差距在哪</th></tr></thead>
        <tbody>
{compare_rows}
        </tbody>
      </table>
    </div>
  </section>

  <section class="card">
    <h2><span class="num">3</span>升格版 · 三色解剖 + 材料溯源（{st_upgrade['total']} 字）</h2>
    <p class="h2sub">把鼠标移到右边任意一句上 —— 左边材料会亮出它对应的原句，并展开这句的成分说明。</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start" class="bench2">
      <div>
        <div style="font-size:12.5px;letter-spacing:.08em;color:var(--ink3);padding-bottom:10px;margin-bottom:14px;border-bottom:1px dashed var(--line)">
          <b style="color:var(--ink);letter-spacing:0;font-size:13.5px">给定资料（功能色标）</b>
        </div>
{material_html}
      </div>
      <div>
        <div style="font-size:12.5px;letter-spacing:.08em;color:var(--ink3);padding-bottom:10px;margin-bottom:14px;border-bottom:1px dashed var(--line)">
          <b style="color:var(--ink);letter-spacing:0;font-size:13.5px">升格版（逐句成分 + 溯源）</b>
        </div>
{upgrade_html}
      </div>
    </div>
  </section>

  <section class="card">
    <h2><span class="num">4</span>整体结构</h2>
    <p class="h2sub">{d['structure_sub']}</p>
    <div class="flow">
{structure_html}
    </div>
    <div class="warn" style="margin-top:18px">{d['structure_note']}</div>
  </section>

  <section class="card">
    <h2><span class="num">5</span>漏点清单</h2>
    <p class="h2sub">每个漏点都标出材料出处、抓取方法、分值。</p>
    <div class="tw">
      <table>
        <thead><tr><th>漏掉的内容</th><th>出自哪一句</th><th>用什么方法能抓到</th><th>值多少</th></tr></thead>
        <tbody>
{gaps}
        </tbody>
      </table>
    </div>
    <div class="bad" style="margin-top:16px">
      <b style="color:#991b1b;font-size:14px">这份答案还差在哪</b>
      <ul>
{chr(10).join(f'        <li>{x}</li>' for x in d['bad'])}
      </ul>
    </div>
  </section>

  <section class="card">
    <h2><span class="num">6</span>带走的一个动作</h2>
    <p class="h2sub">{d['takeaway_sub']}</p>
    <div class="flow">
{takeaways}
    </div>
    <div class="tip" style="margin-top:20px">{d['verdict']}</div>
  </section>

</div>

<a class="backbtn" href="练习档案.html">← 练习档案</a>

<script>
(function(){{
  var ans=document.querySelectorAll('.ans[data-src]');
  ans.forEach(function(a){{
    var ids=(a.getAttribute('data-src')||'').split(',').map(function(s){{return s.trim();}}).filter(Boolean);
    if(!ids.length)return;
    function on(){{ids.forEach(function(id){{var e=document.getElementById(id);if(e)e.classList.add('hl');}});}}
    function off(){{ids.forEach(function(id){{var e=document.getElementById(id);if(e)e.classList.remove('hl');}});}}
    a.addEventListener('mouseenter',on);
    a.addEventListener('mouseleave',function(){{if(!a.classList.contains('on'))off();}});
    a.addEventListener('click',function(){{
      var was=a.classList.contains('on');
      ans.forEach(function(b){{if(b!==a)b.classList.remove('on');}});
      if(was){{a.classList.remove('on');off();}}else{{a.classList.add('on');on();}}
    }});
  }});
}})();
</script>
</body>
</html>
"""


# ══════════════════════════════════════════════════════════ 材料（复用）

LJ = [  # 老旧小区改造
    dict(no="第 1 段", fn="problem", fnlabel="问题", sents=[("lj1", "近年来，随着城镇化进程加快，一些建成年代较早的老旧小区逐渐暴露出诸多问题。管网老化严重，水管跑冒滴漏时有发生；道路坑洼不平，雨天积水成塘；停车位严重不足，居民车辆随意停放，消防通道常被占用。有居民反映，小区没有电梯，老人上下楼十分吃力，一些老人因为下楼不便，一年到头很少出门。")]),
    dict(no="第 2 段", fn="problem", fnlabel="问题", sents=[("lj2", '"最头疼的是物业。"居民李女士说，"我们小区物业费每平方米只有三毛钱，收不上来，物业公司换了好几家，都是干几个月就走了。"记者了解到，该小区没有成立业主委员会，居民对小区事务参与热情不高，遇到问题往往各扫门前雪。社区居委会人手有限，一名工作人员要负责三个小区，日常事务应接不暇。')]),
    dict(no="第 3 段", fn="problem", fnlabel="问题", sents=[("lj3", '改造资金从哪里来，是绕不过去的难题。市住建局相关负责人介绍，老旧小区改造主要依靠财政投入，但财政资金有限，只能"撒胡椒面"，很难一次性彻底解决。社会资本参与意愿不强，因为改造项目利润薄、回收周期长，缺乏可持续的盈利模式。此外，部分居民对改造方案存在分歧，有的希望加装电梯，有的担心影响采光；有的要求增加车位，有的不愿意挪走自家门前的绿化带，协商往往久拖不决。')]),
    dict(no="第 4 段", fn="action", fnlabel="做法（本题干扰段）", sents=[("lj4", '一些地方已经在探索。A 市把老旧小区改造与社区治理结合起来，在改造中同步成立业主委员会，由居民协商确定改造项目清单和后续管理办法。B 市引入专业物业企业，采取"先服务、后收费"的方式，让居民先感受服务变化再议价。C 市则把小区闲置的边角地、屋顶改造成停车位和光伏电站，产生的收益用于补贴物业费，实现了"自我造血"。')]),
    dict(no="第 5 段", fn="conclusion", fnlabel="观点", sents=[("lj5", '专家指出，老旧小区改造不能只算经济账，更要算民生账。改造不是简单刷墙铺路，而是对基层治理能力的一次检验。要避免"政府干、群众看"，关键是把居民从旁观者变成参与者。')]),
]

MS = [  # 乡村民宿
    dict(no="第 1 段", fn="problem", fnlabel="问题", sents=[("ms1", '近年来，乡村民宿成为乡村旅游的新热点。但一些地方一哄而上，看到别处办民宿赚钱就盲目跟风，既没有评估本地资源禀赋，也没有做过市场调研。有的村短短两年办起四十多家民宿，风格雷同、菜品相似，游客来了"千店一面"，转身就走。')]),
    dict(no="第 2 段", fn="problem", fnlabel="问题", sents=[("ms2", '"最大的难题是缺人。"县文旅局工作人员说。民宿管家、客房服务、活动策划都需要专业人员，但村里年轻人大多外出务工，留下来的人员年龄偏大、缺乏服务意识。县里曾组织过几期培训，可课程偏理论，听完就忘，学员回去还是按老办法干。')]),
    dict(no="第 3 段", fn="problem", fnlabel="问题", sents=[("ms3", '资金也是个坎。村民王大姐想把自己家的老屋改成民宿，一算账，装修、消防、卫生、网络都要花钱，至少要投入三十多万元，而银行对农房抵押贷款限制较多，她跑了几趟也没办下来。村里没有集体经营主体，想申请项目资金也无从下手。一些工商资本进来后，又因为土地、产权不清晰，中途撤资。')]),
    dict(no="第 4 段", fn="problem", fnlabel="问题", sents=[("ms4", '配套设施跟不上。通往村里的路只有三米宽，旅游大巴进不来；停车位不足，旺季车辆沿路停放；污水管网没有覆盖，生活污水直排。游客普遍反映"风景不错，就是住着不方便"。')]),
    dict(no="第 5 段", fn="action", fnlabel="做法（本题干扰段）", sents=[("ms5", '也有做得好的。D 县制定民宿发展规划，划定重点发展区域，实行差异化定位；E 县与职业院校合作开设民宿管理专业，定向培养人才；F 县由村集体统一流转闲置农房、统一对外招商，村民以房入股、按比例分红。')]),
]


# ══════════════════════════════════════════════════════════ 三份数据

P1 = dict(
    slug="p1", file="练习1-归纳概括-图解.html",
    kicker="视觉识别 · 结果分析 01",
    title="练习 1 三色解剖", sub="老旧小区改造 · 归纳概括：概括主要困难",
    h1="三色解剖：把一整段压成了一句话",
    chips=["得分 4.5 / 15"],
    student_hint="注意这份答案的颜色构成 —— 几乎全是「概」，这就是它只得 4.5 分的原因。",
    material=LJ,
    student=[
        dict(kind="cond", label="第 1 条", bg="#ecfdf5", fg="#047857", wc="10 字", html='<span class="mk-own">1. </span><span class="mk-cond">物业费难以收取</span>。', note='材料原话是「物业费每平方米只有三毛钱，<b>收不上来</b>，物业公司换了好几家」。你把它压成了「物业费难以收取」——<b>把一整段的两条要点（收费难 + 公司频繁退出）揉成了半句话</b>。'),
        dict(kind="cond", label="第 2 条", bg="#ecfdf5", fg="#047857", wc="12 字", html='<span class="mk-own">2. </span><span class="mk-copy">改造资金</span><span class="mk-cond">筹集困难</span>。', note='「改造资金」抄对了，但「筹集困难」只是总括。<b>为什么难？</b>材料写了两层：依赖财政且总量有限、社会资本利润薄周期长。你一层没写。'),
        dict(kind="own", label="第 3 条", bg="#fffbeb", fg="#b45309", wc="18 字", html='<span class="mk-own">3. </span><span class="mk-cond">居民</span><span class="mk-own">痛点不同</span><span class="mk-cond">，难以协调一致</span>。', note='材料原话是「部分居民对改造方案<b>存在分歧</b>」。「痛点不同」是你自己造的词 —— 申论里这叫<b>换词</b>，不是概括，采分词丢了。'),
    ],
    upgrade=[
        dict(kind="own", label="总括句", bg="#fffbeb", fg="#b45309", src="lj1,lj3",
             src_label="← 全篇", html='<span class="mk-own">当前老旧小区改造主要面临四方面困难：</span>',
             note='1 自。总括句必须自己写，材料里没有。作用是一句话告诉阅卷人「我答几条」。'),
        dict(kind="copy", label="一是", bg="#f1f5f9", fg="#475569", src="lj1",
             src_label="← 第 1 段", html='<span class="mk-own">一是</span><span class="mk-cond">基础设施老化</span><span class="mk-own">，</span><span class="mk-copy">管网老化、道路坑洼不平、停车位不足</span><span class="mk-own">，</span><span class="mk-cond">缺乏电梯等适老化设施</span><span class="mk-own">，居民生活不便。</span>',
             note='3 抄 + 2 概 + 3 自。「中心句 + 具体现象」结构。这一整段你原来<b>完全没写</b>。'),
        dict(kind="copy", label="二是", bg="#f1f5f9", fg="#475569", src="lj2",
             src_label="← 第 2 段", html='<span class="mk-own">二是</span><span class="mk-cond">物业管理缺位</span><span class="mk-own">，</span><span class="mk-copy">物业费标准低、收缴困难，物业公司频繁退出</span><span class="mk-own">；</span><span class="mk-copy">业主委员会缺失</span><span class="mk-own">，</span><span class="mk-cond">居民参与热情不高</span><span class="mk-own">；</span><span class="mk-copy">社区居委会人手有限</span><span class="mk-own">。</span>',
             note='4 抄 + 2 概 + 5 自。你把这一段压成了「物业费难以收取」6 个字，<b>漏掉了 4 条要点</b>。'),
        dict(kind="copy", label="三是", bg="#f1f5f9", fg="#475569", src="lj3",
             src_label="← 第 3 段", html='<span class="mk-own">三是</span><span class="mk-cond">资金保障不足</span><span class="mk-own">，</span><span class="mk-copy">改造主要依靠财政投入且总量有限</span><span class="mk-own">，</span><span class="mk-copy">社会资本参与意愿不强</span><span class="mk-own">，</span><span class="mk-cond">项目利润薄、回收周期长</span><span class="mk-own">。</span>',
             note='3 抄 + 2 概 + 3 自。总括句 + 「为什么难」两层展开 —— 这就是你原来缺的东西。'),
        dict(kind="copy", label="四是", bg="#f1f5f9", fg="#475569", src="lj3,lj5",
             src_label="← 第 3 段 + 第 5 段", html='<span class="mk-own">四是</span><span class="mk-cond">居民意见难统一</span><span class="mk-own">，</span><span class="mk-copy">改造方案存在分歧</span><span class="mk-own">，</span><span class="mk-cond">利益诉求多元</span><span class="mk-own">，</span><span class="mk-copy">协商久拖不决</span><span class="mk-own">。</span>',
             note='3 抄 + 2 概 + 3 自。<b>注意「存在分歧」是材料原词</b>，不是你的「痛点不同」。'),
    ],
    ratio_note='<b>看出来了吗 —— 你的答案有一半以上是「概」（54.1%），而「抄」只有 4 个字（10.8%）。</b>'
               '这叫<b>「概括层级过高」</b>：你把每一整段压成了一个短语，把采分词全丢了。<br><br>'
               '升格版反过来：<b>抄占了 45.8%，接近一半</b>。归纳概括题的答案，主体必须是材料里的具体名词 —— '
               '「管网老化」「停车位不足」「物业公司频繁退出」这些词，阅卷人扫一眼就能打钩。'
               '你写「物业费难以收取」，他得想一下，还未必对得上清单。',
    structure_sub="归纳概括题的骨架最简单：一句总括 + 分条罗列。难的是每条要「展开」。",
    structure=[
        dict(tone="define", cls="d", label="总括句", body='<span class="mk-own">当前老旧小区改造主要面临四方面困难：</span>'),
        dict(tone="problem", cls="p", label="一是 · 设施", body='<span class="mk-cond">基础设施老化</span> → <span class="mk-copy">管网、道路、停车位、无电梯</span>'),
        dict(tone="problem", cls="p", label="二是 · 物业", body='<span class="mk-cond">物业管理缺位</span> → <span class="mk-copy">收费难、公司退出、无业委会、居委会人手少</span>'),
        dict(tone="problem", cls="p", label="三是 · 资金", body='<span class="mk-cond">资金保障不足</span> → <span class="mk-copy">靠财政且有限、社会资本不愿进</span>'),
        dict(tone="problem", cls="p", label="四是 · 协商", body='<span class="mk-cond">居民意见难统一</span> → <span class="mk-copy">方案有分歧、协商久拖不决</span>'),
    ],
    structure_note='<b>每条 = 一个概括词（打头）+ 若干材料原词（铺开）。</b>'
                   '你只写了「概括词」那一半，把「铺开」全砍了 —— 这就是 37 字和 201 字的差距。',
    gaps=[
        dict(item="<b>整段漏</b>：基础设施老化", src="第 1 段：管网老化、道路坑洼不平、停车位严重不足、小区没有电梯", how="<b>数段落</b> —— 第 1 段整段在讲问题，却一条没答", value="3 分"),
        dict(item="物业段的其余 4 条", src="第 2 段：物业公司换了好几家、没有成立业主委员会、居民参与热情不高、社区居委会人手有限", how="<b>标点切分法</b> —— 按分号切句，一句一勾", value="3 分"),
        dict(item="资金「难在哪」的两层", src="第 3 段：主要依靠财政投入但资金有限、社会资本利润薄回收周期长", how="<b>首尾句法</b> —— 「改造资金从哪里来，是绕不过去的难题」后面全是解释", value="2.5 分"),
        dict(item="居民分歧（换词导致丢分）", src="第 3 段：部分居民对改造方案<b>存在分歧</b>", how="<b>原词搬运</b> —— 别把「存在分歧」写成「痛点不同」", value="1 分"),
        dict(item="政府干、群众看", src="第 5 段：要避免「政府干、群众看」", how="<b>带引号的词</b> —— 引号即采分词", value="1 分"),
    ],
    bad=[
        '<b>概括层级过高</b>：把每一整段压成一个短语，采分词全丢',
        '<b>字数严重不足</b>：37 / 200 字。空格就是分数',
        '<b>整段漏答</b>：第 1 段（基础设施）一个字没写',
        '<b>换词</b>：「存在分歧」写成了「痛点不同」',
    ],
    takeaway_sub="这道题只需要带走一件事。",
    takeaways=['<b>每条展开到 35–45 字，写完先数字数。</b>不足 160 字，就是漏点了 —— 不要去怀疑文笔，去怀疑漏点。'],
    verdict='<b>成绩：4.5 / 15。</b>这是你写的第一份申论答案，方向没跑偏（三条都踩在真要点上），'
            '问题只有一个但很致命：<b>把「找点」做成了「概括大意」</b>。'
            '你的三条不是要点，是对要点的<b>描述</b>。',
)

P2 = dict(
    slug="p2", file="练习2-归纳概括-图解.html",
    kicker="视觉识别 · 结果分析 02",
    title="练习 2 三色解剖", sub="老旧小区改造 · 同材料换问法：概括三市做法",
    h1="三色解剖：审题对了，输在一个词上",
    chips=["得分 7 / 10"],
    student_hint="这份答案的审题是完全正确的 —— 注意它只用了第 4 段，一个干扰段都没抄。",
    material=LJ,
    student=[
        dict(kind="copy", label="A 市", bg="#f1f5f9", fg="#475569", wc="30 字", html='<span class="mk-copy">A市</span><span class="mk-own">改造过程中</span><span class="mk-copy">成立业主委员会，居民协商确定改造清单和管理办法</span><span class="mk-own">。</span>', note='3 抄 + 1 自。<b>基本完整</b>。小瑕疵：材料是「改造项目清单」和「后续管理办法」，你写成「改造清单」，漏了「后续」二字。'),
        dict(kind="own", label="B 市", bg="#fffbeb", fg="#b45309", wc="14 字", html='<span class="mk-copy">B市</span><span class="mk-own">先改造，再进行议价</span><span class="mk-own">。</span>', note='1 抄 + 2 自。<b>这一条是全题的问题所在</b>：材料原词是「<b>先服务、后收费</b>」，你读成了「先改造，再进行议价」。<b>你用生活经验替换了材料原词</b>，而且丢掉了这一条最核心的动作 ——「引入专业物业企业」。'),
        dict(kind="copy", label="C 市", bg="#f1f5f9", fg="#475569", wc="31 字", html='<span class="mk-copy">C市</span><span class="mk-own">利用</span><span class="mk-cond">闲置区域</span><span class="mk-own">改造成</span><span class="mk-copy">停车位、光伏电站</span><span class="mk-own">收益补贴物业费</span><span class="mk-own">。</span>', note='2 抄 + 1 概 + 3 自。大体对。两处可提升：「闲置区域」材料写的是「闲置的<b>边角地、屋顶</b>」（具体名词更值钱）；漏了带引号的「<b>自我造血</b>」。'),
    ],
    upgrade=[
        dict(kind="copy", label="一是 · A 市", bg="#f1f5f9", fg="#475569", src="lj4",
             src_label="← 第 4 段 A 市", html='<span class="mk-own">一是</span><span class="mk-copy">A 市</span><span class="mk-cond">推动改造与社区治理相结合</span><span class="mk-own">，</span><span class="mk-copy">同步成立业主委员会</span><span class="mk-own">，</span><span class="mk-copy">由居民协商确定改造项目清单和后续管理办法</span><span class="mk-own">。</span>',
             note='4 抄 + 1 概 + 2 自。补上了「与社区治理相结合」这个总起，以及「后续」二字。'),
        dict(kind="copy", label="二是 · B 市", bg="#f1f5f9", fg="#475569", src="lj4",
             src_label="← 第 4 段 B 市", html='<span class="mk-own">二是</span><span class="mk-copy">B 市引入专业物业企业</span><span class="mk-own">，采取</span><span class="mk-copy">"先服务、后收费"</span><span class="mk-own">方式，让居民</span><span class="mk-copy">先感受服务变化再议价</span><span class="mk-own">。</span>',
             note='4 抄 + 3 自。<b>「引入专业物业企业」是这一条的头</b>，「先服务、后收费」只是它的方式。你原来只写了方式，等于把脑袋砍了。'),
        dict(kind="copy", label="三是 · C 市", bg="#f1f5f9", fg="#475569", src="lj4",
             src_label="← 第 4 段 C 市", html='<span class="mk-own">三是</span><span class="mk-copy">C 市盘活闲置边角地和屋顶</span><span class="mk-own">，改造成</span><span class="mk-copy">停车位、光伏电站</span><span class="mk-own">，以收益</span><span class="mk-copy">补贴物业费</span><span class="mk-own">，实现</span><span class="mk-copy">"自我造血"</span><span class="mk-own">。</span>',
             note='5 抄 + 3 自。「闲置区域」→「闲置边角地和屋顶」（贴原词）；补上带引号的「自我造血」。'),
    ],
    ratio_note='<b>这份答案的成分比例本来就是健康的 ——「抄」占 52.9%，升格版 67.9%。</b>'
               '做法题的答案本来就该以材料原词为主。<br><br>'
               '所以问题不在配比，在<b>三处具体的词</b>：'
               '①把「先服务、后收费」读成了「先改造，再进行议价」；'
               '②丢掉核心动宾动作「引入专业物业企业」；'
               '③漏掉带引号的「自我造血」。<b>三处都是「原词搬运」的功夫，不是理解能力的问题。</b>',
    structure_sub="做法题的骨架只有一个公式，三市三遍。",
    structure=[
        dict(tone="define", cls="d", label="A 市", body='主体 + 动作 + 方式：<span class="mk-copy">A 市</span> → <span class="mk-copy">成立业主委员会</span> → <span class="mk-copy">居民协商确定清单和管理办法</span>'),
        dict(tone="action", cls="a", label="B 市", body='主体 + 动作 + 方式：<span class="mk-copy">B 市</span> → <span class="mk-copy">引入专业物业企业</span> → <span class="mk-copy">"先服务、后收费"</span>'),
        dict(tone="action", cls="a", label="C 市", body='主体 + 动作 + 方式：<span class="mk-copy">C 市</span> → <span class="mk-copy">盘活闲置边角地和屋顶</span> → <span class="mk-copy">收益补贴物业费</span>'),
    ],
    structure_note='<b>每条自检：动词 + 宾语齐不齐？</b><br>'
                   'C 市动作 = 盘活闲置空间；A 市动作 = 成立业主委员会；B 市动作 = <b>引入专业物业企业</b>。<br>'
                   '只写「先服务后收费」，就像回答「他怎么致富的」时说「他很努力」——<b>这不算答案。</b>',
    gaps=[
        dict(item="B 市核心动作：<b>引入专业物业企业</b>", src="第 4 段：B 市<b>引入专业物业企业</b>，采取「先服务、后收费」的方式", how="<b>动宾结构自检</b> —— 这条的「动词+宾语」是什么", value="1.5 分"),
        dict(item="「先服务、后收费」被读错", src="第 4 段原词：<b>「先服务、后收费」</b>", how="<b>原词搬运</b> —— 不许用生活经验替换材料词汇", value="0.5 分"),
        dict(item="带引号的「自我造血」", src="第 4 段：实现了<b>「自我造血」</b>", how="<b>引号即采分词</b>", value="0.5 分"),
        dict(item="「闲置区域」不够贴", src="第 4 段：闲置的<b>边角地、屋顶</b>", how="<b>具体名词优先</b> —— 笼统名词不值钱", value="0.25 分"),
        dict(item="「改造项目清单」的「项目」与「后续」", src="第 4 段：改造<b>项目</b>清单和<b>后续</b>管理办法", how="<b>原词搬运</b>", value="0.25 分"),
    ],
    bad=[
        '<b>读错材料词</b>：「先服务、后收费」→「先改造，再进行议价」',
        '<b>动宾不完整</b>：只写方式，丢了「引入专业物业企业」',
        '<b>漏带引号的采分词</b>：「自我造血」',
        '<b>用笼统名词</b>：「闲置区域」代替「闲置边角地和屋顶」',
    ],
    takeaway_sub="这道题只需要带走两件事。",
    takeaways=[
        '<b>做法题必须写完整的「动词 + 宾语」。</b>写完每条自问：这条的动作是什么？',
        '<b>原词搬运，不许「翻译」。</b>你觉得某个词不顺口、想换成自己的说法时，就是最危险的时刻。带引号的词必抄。',
    ],
    verdict='<b>成绩：7 / 10。</b>审题完全正确 —— 你精准锁定了第 4 段，没有抄第 5 段的观点。'
            '丢的 3 分全在 B 市一条上，而它暴露的不是理解问题，是<b>两个可以练出来的习惯</b>。',
)

P3 = dict(
    slug="p3", file="练习3-归纳概括-图解.html",
    kicker="视觉识别 · 结果分析 03",
    title="练习 3 三色解剖", sub="乡村民宿 · 归纳概括：概括主要问题",
    h1="三色解剖：结构对了，差在段落后半截",
    chips=["得分 11 / 15", "第 1 课结业"],
    student_hint="这份答案已经形成了「中心句 + 具体现象」的正确结构 —— 看颜色就知道，抄和概都大量出现了。",
    material=MS,
    student=[
        dict(kind="copy", label="第 1 条", bg="#f1f5f9", fg="#475569", wc="42 字", html='<span class="mk-own">1. </span><span class="mk-cond">一些地方</span><span class="mk-copy">盲目跟风</span><span class="mk-own">，</span><span class="mk-copy">没有做市场调研</span><span class="mk-own">，推出一批</span><span class="mk-copy">风格雷同、菜品相似</span><span class="mk-own">的民宿。</span>', note='3 抄 + 1 概 + 3 自。命中。可再补两个更值钱的词：材料原话「未评估<b>本地资源禀赋</b>」，以及概括词「<b>同质化</b>」（对应带引号的「千店一面」）。'),
        dict(kind="cond", label="第 2 条", bg="#ecfdf5", fg="#047857", wc="32 字", html='<span class="mk-own">2. </span><span class="mk-cond">服务人才短缺</span><span class="mk-own">。</span><span class="mk-copy">年轻人外出打工</span><span class="mk-own">，剩下</span><span class="mk-copy">年级较大的人缺乏服务意识</span><span class="mk-own">。</span>', note='2 抄 + 1 概 + 3 自。<b>中心句 + 具体现象，结构正确。</b>但本段有 5 句话，你只用了 3 句 —— 漏了「民宿管家、客房服务、活动策划都需要专业人员」和「课程偏理论，听完就忘」。'),
        dict(kind="copy", label="第 3 条", bg="#f1f5f9", fg="#475569", wc="55 字", html='<span class="mk-own">3. </span><span class="mk-cond">前期成本高</span><span class="mk-own">，</span><span class="mk-copy">装修、消防、卫生、网络都需要花钱</span><span class="mk-own">，</span><span class="mk-copy">工商资本也因为农村土地产权不清晰而中途撤资</span><span class="mk-own">。</span>', note='2 抄 + 1 概 + 2 自。归类判断是对的（产权不清导致撤资，本质是钱的问题）。<b>但本段有 5 句话，你只用了 2 句</b> —— 漏了一整条筹资渠道。'),
        dict(kind="copy", label="第 4 条", bg="#f1f5f9", fg="#475569", wc="45 字", html='<span class="mk-own">4. </span><span class="mk-cond">基础设施跟不上</span><span class="mk-own">，</span><span class="mk-copy">道路窄，旅游大巴进不来</span><span class="mk-own">，</span><span class="mk-copy">车位不够</span><span class="mk-own">、</span><span class="mk-copy">污水处理设施没有覆盖全</span><span class="mk-own">。</span>', note='3 抄 + 1 概 + 3 自。四个具体现象齐全。小错：「车位不够」应用原词「<b>停车位不足</b>」；「污水处理设施没有覆盖全」应用原词「<b>污水管网未覆盖</b>」。'),
    ],
    upgrade=[
        dict(kind="own", label="总括句", bg="#fffbeb", fg="#b45309", src="ms1",
             src_label="← 全篇", html='<span class="mk-own">当前乡村民宿发展面临四方面问题：</span>',
             note='1 自。总括句自己写。'),
        dict(kind="copy", label="一是 · 规划", bg="#f1f5f9", fg="#475569", src="ms1",
             src_label="← 第 1 段", html='<span class="mk-own">一是</span><span class="mk-cond">缺乏规划、盲目跟风</span><span class="mk-own">，</span><span class="mk-copy">未评估资源禀赋、未做市场调研</span><span class="mk-own">，民宿</span><span class="mk-cond">同质化严重</span><span class="mk-own">。</span>',
             note='2 抄 + 2 概 + 4 自。补上「资源禀赋」这个材料原词，和「同质化」这个概括词。'),
        dict(kind="copy", label="二是 · 人才", bg="#f1f5f9", fg="#475569", src="ms2",
             src_label="← 第 2 段", html='<span class="mk-own">二是</span><span class="mk-cond">专业人才短缺</span><span class="mk-own">，</span><span class="mk-copy">管家、客房、策划岗位缺人</span><span class="mk-own">；</span><span class="mk-copy">年轻人外流</span><span class="mk-own">，</span><span class="mk-copy">留守人员年龄偏大、服务意识不足</span><span class="mk-own">；</span><span class="mk-copy">培训偏理论，效果不佳</span><span class="mk-own">。</span>',
             note='4 抄 + 1 概 + 6 自。<b>「培训偏理论」就是标点切分法切出来的第 5 句</b> —— 一句一勾，就漏不了。'),
        dict(kind="copy", label="三是 · 资金", bg="#f1f5f9", fg="#475569", src="ms3",
             src_label="← 第 3 段", html='<span class="mk-own">三是</span><span class="mk-cond">资金筹措困难</span><span class="mk-own">，前期投入大，</span><span class="mk-copy">农房抵押贷款受限</span><span class="mk-own">；</span><span class="mk-copy">村集体缺少经营主体，难申请项目资金</span><span class="mk-own">；</span><span class="mk-copy">土地产权不清晰，工商资本中途撤资</span><span class="mk-own">。</span>',
             note='4 抄 + 1 概 + 5 自。<b>「农房抵押贷款受限」「村集体缺少经营主体」是你原来完全漏掉的两条</b>，都在第 3 段的中间和后半。'),
        dict(kind="copy", label="四是 · 配套", bg="#f1f5f9", fg="#475569", src="ms4",
             src_label="← 第 4 段", html='<span class="mk-own">四是</span><span class="mk-cond">配套设施滞后</span><span class="mk-own">，</span><span class="mk-copy">道路狭窄大巴难进</span><span class="mk-own">，</span><span class="mk-copy">停车位不足</span><span class="mk-own">，</span><span class="mk-copy">污水管网未覆盖</span><span class="mk-own">。</span>',
             note='3 抄 + 1 概 + 4 自。把两处口语化表述换回材料原词。'),
    ],
    ratio_note='<b>这是你第一份结构正确的概括题答案 ——「抄」占了 66.2%，是四份答案里最高的。</b>'
               '「中心句 + 具体现象」的框架已经形成。<br><br>'
               '注意一个有意思是现象：升格版的「抄」反而降到了 59.4% —— '
               '因为升格版多写了总括句和分层词（「自」从 19.5% 升到 24.4%）。'
               '<b>骨架用自己写的，肉从材料里割，两者比例大致稳定在 4:6。</b><br><br>'
               '丢的 4 分全在<b>同一个动作</b>上：<b>你只处理了段落的中心句和前半部分。</b>'
               '第 2 段有 5 句你用了 3 句，第 3 段有 5 句你用了 2 句 —— 漏掉的「培训偏理论」「农房抵押贷款受限」「村集体缺少经营主体」，'
               '全在段落的中间和后半。<b>这不是能力问题，是没做「一句一勾」这个动作。</b>',
    structure_sub="归纳概括题的骨架：一句总括 + 四条，每条「概括词打头 + 材料原词铺开」。",
    structure=[
        dict(tone="define", cls="d", label="总括句", body='<span class="mk-own">当前乡村民宿发展面临四方面问题：</span>'),
        dict(tone="problem", cls="p", label="一是 · 规划", body='<span class="mk-cond">缺乏规划、盲目跟风</span> → <span class="mk-copy">未评估资源禀赋、未做市场调研、同质化</span>'),
        dict(tone="problem", cls="p", label="二是 · 人才", body='<span class="mk-cond">专业人才短缺</span> → <span class="mk-copy">岗位缺人、年轻人外流、培训偏理论</span>'),
        dict(tone="problem", cls="p", label="三是 · 资金", body='<span class="mk-cond">资金筹措困难</span> → <span class="mk-copy">贷款受限、缺经营主体、产权不清撤资</span>'),
        dict(tone="problem", cls="p", label="四是 · 配套", body='<span class="mk-cond">配套设施滞后</span> → <span class="mk-copy">道路狭窄、停车位不足、污水管网未覆盖</span>'),
    ],
    structure_note='<b>骨架你已经搭对了，缺的是往每条里「填肉」。</b><br>'
                   '第 2 段和第 3 段各有 5 句话，每句都是一个可能的采分点。'
                   '你在草稿纸上按句号、分号切句，<b>一句画一个勾</b> —— 剩下的 4 分就回来了。',
    gaps=[
        dict(item="培训效果不佳", src="第 2 段第 5 句：「可<b>课程偏理论，听完就忘</b>」", how="<b>标点切分法</b> —— 一句一勾，第 5 句就是要点", value="1 分"),
        dict(item="农房抵押贷款受限", src="第 3 段第 3 句：「银行对<b>农房抵押贷款限制较多</b>，她跑了几趟也没办下来」", how="<b>标点切分法</b> —— 第 3 段中间那句", value="1 分"),
        dict(item="村集体缺少经营主体", src="第 3 段第 4 句：「村里<b>没有集体经营主体</b>，想申请项目资金也无从下手」", how="<b>标点切分法</b> —— 第 3 段后半那句", value="1 分"),
        dict(item="民宿专业岗位缺人", src="第 2 段第 2 句：「民宿管家、客房服务、活动策划都需要专业人员」", how="<b>具体名词优先</b> —— 比笼统的「服务人才」更值钱", value="0.5 分"),
        dict(item="「资源禀赋」这个原词", src="第 1 段：「既没有评估<b>本地资源禀赋</b>」", how="<b>原词搬运</b>", value="0.25 分"),
        dict(item="两处口语化表述", src="第 4 段：「<b>停车位不足</b>」「<b>污水管网没有覆盖</b>」", how="<b>用材料原词</b>，别自己改写成「车位不够」「污水处理设施」", value="0.25 分"),
    ],
    bad=[
        '<b>漏段落后半截</b>：第 2 段漏 2 句、第 3 段漏 2 句，共丢 3.5 分',
        '<b>没有一句一勾</b>：读懂了段落大意就往下走，没做机械动作',
        '<b>口语化替换</b>：「车位不够」「污水处理设施」应为「停车位不足」「污水管网未覆盖」',
        '<b>错别字</b>：「年<b>级</b>较大」应为「年<b>龄</b>偏大」',
    ],
    takeaway_sub="这道题只需要带走一个动作。",
    takeaways=['<b>标点切分法：按句号、分号把段落切成句子，一句画一个勾。</b>'
               '有几句话，就有几个可能的采分点。做完这个动作，再合并成条目。'],
    verdict='<b>成绩：11 / 15　第 1 课结业。</b>从第一份的 4.5 分到这里，'
            '你已经完成了「找点」能力的建立。剩下的差距不在方法上，在<b>一个机械动作有没有做</b>上。',
)

ALL = [P1, P2, P3]


def main() -> int:
    want = sys.argv[1:]
    if not want or "archive" in want:
        (OUT / "练习档案.html").write_text(render_archive(), encoding="utf-8")
        print("  ✓ 练习档案  →  练习档案.html")
    if not want or "quote" in want:
        (OUT / "引号与抽象概念-图解.html").write_text(render_quote_page(), encoding="utf-8")
        print("  ✓ 引号与抽象概念  →  引号与抽象概念-图解.html")
    for d in ALL:
        if want and d["slug"] not in want:
            continue
        html = render(d)
        (OUT / d["file"]).write_text(html, encoding="utf-8")
        s = mark_stats(d["student"])
        u = mark_stats(d["upgrade"])
        print(f"  ✓ {d['title']}  →  {d['file']}")
        print(f"      学生 {s['total']} 字　升格 {u['total']} 字")
    return 0




# ══════════════════════════════════════════════════════════ 练习档案（总览）

RECORDS = [
    dict(no="练习 1", type="归纳概括", topic="老旧小区改造 · 困难", score=4.5, full=15,
         file="练习1-归纳概括-图解.html", has_page=True,
         issue="概括层级过高，37 / 200 字", tone="#dc2626"),
    dict(no="练习 2", type="归纳概括", topic="老旧小区改造 · 三市做法", score=7, full=10,
         file="练习2-归纳概括-图解.html", has_page=True,
         issue="读错材料词、动宾不完整", tone="#d97706"),
    dict(no="练习 3", type="归纳概括", topic="乡村民宿 · 问题", score=11, full=15,
         file="练习3-归纳概括-图解.html", has_page=True,
         issue="漏段落后半截三个点", tone="#059669"),
    dict(no="练习 4", type="综合分析", topic="社区食堂 · 解释型", score=None, full=15,
         file="第2课-综合分析-图解.html", has_page=True, is_demo=True,
         issue="未作答，作为第 2 课示范", tone="#7c3aed"),
    dict(no="练习 5", type="综合分析", topic="口袋公园 · 解释型", score=13, full=15,
         file="练习5-综合分析-图解.html", has_page=True,
         issue="漏「会客厅」社会功能；正反不对称", tone="#7c3aed"),
    dict(no="练习 6", type="提出对策", topic="指尖上的形式主义 · 对策", score=15, full=20,
         file="练习6-提出对策-图解.html", has_page=True,
         issue="四成篇幅写了题目没问的问题概括", tone="#0891b2"),
    dict(no="练习 7", type="提出对策", topic="同材料换问法 · 表现＋建议", score=21, full=25,
         file="练习7-提出对策-图解.html", has_page=True,
         issue="结构对了；配比失衡 + 概括吃掉采分词", tone="#0891b2"),
]

PATTERNS = [
    dict(title="概括层级过高", body="把一整段压成一个短语，采分词全丢。<b>练习 1 只写了 37 / 200 字。</b>第 1 课改掉了，<b>练习 7 在建议段复发</b> —— 把「政务App和<b>工作群</b>」概括成「各类政务平台」，「工作群」三个字没了。",
         fix="概括只用于「问题」；「对策」里的动作词和对象词一律原样抄", status="<b style='color:#dc2626'>复发（练习 7）</b>"),
    dict(title="漏段落后半截", body="只抓中心句，段落后半截的采分点全漏。<b>练习 3 漏了「培训偏理论」「农房抵押贷款受限」「村集体缺经营主体」。</b>",
         fix="标点切分法：按句号分号切句，一句一勾", status="待巩固"),
    dict(title="用生活经验替换材料原词", body="把「先服务、后收费」读成「先改造，再进行议价」。<b>练习 2 因此丢 1 分。</b>",
         fix="原词搬运，不许「翻译」；带引号的必抄", status="待巩固"),
    dict(title="动宾结构不完整", body="只写方式，丢了核心动作。<b>练习 2 丢了「引入专业物业企业」。</b>",
         fix="每条自检「动词 + 宾语」齐不齐", status="已改正"),
    dict(title="正反两层不对称", body="有反面总起就必须有正面总起。<b>练习 5 正面有、反面没有。</b>",
         fix="写完回头看两层总起是否对仗", status="新出现"),
    dict(title="答非所问：写了题目没问的部分", body="题目只问「提出对策建议」，却花 119 字（39.7%）概括问题。<b>练习 6 因此在两条对策上没篇幅了。</b>",
         fix="动笔前先数题目问了几个动作，问几个就写几块", status="已改正（练习 7 结构完全正确）"),
    dict(title="篇幅配比失衡", body="两个动作的分值不相等，篇幅却给成一半一半。<b>练习 7：表现 190 字（49.4%）／建议 195 字（50.6%），而建议占 15 分、表现只占 10 分。</b>多写的 60 字正好是漏掉的两条建议。",
         fix="写完数字数：建议段应该是表现段的两倍长", status="新出现"),
]


def render_archive() -> str:
    rows = []
    for i, r in enumerate(RECORDS):
        if r["score"] is None:
            pct, txt = 0, "示范"
        else:
            pct = r["score"] / r["full"] * 100
            txt = f"{r['score']:g} / {r['full']}"
        rows.append(f"""      <div class="prow">
        <div class="pname">{r['no']}</div>
        <div class="pbar"><i style="width:{pct:.1f}%;background:{r['tone']}"></i></div>
        <div class="pscore">{txt}</div>
      </div>""")
    curve = "\n".join(rows)

    # 逐题对照统计（脚本实算）
    by_file = {d["file"]: d for d in ALL}
    cmp_rows = []
    tot = {"hit": 0, "part": 0, "err": 0, "miss": 0}
    for r in RECORDS:
        d = by_file.get(r["file"])
        if not d or not d.get("compare"):
            cmp_rows.append(
                f'<tr><td><b>{r["no"]}</b></td><td colspan="5" style="color:var(--ink3)">'
                f'示范题，未拆采分点对照</td><td>—</td></tr>')
            continue
        c = {"hit": 0, "part": 0, "err": 0, "miss": 0}
        for x in d["compare"]:
            c[x["j"]] += 1
        n = len(d["compare"])
        for k in tot:
            tot[k] += c[k]
        cmp_rows.append(f"""          <tr>
            <td><b>{r['no']}</b></td>
            <td>{n}</td>
            <td style="color:#059669;font-weight:700">{c['hit']}</td>
            <td style="color:#d97706;font-weight:700">{c['part']}</td>
            <td style="color:#dc2626;font-weight:700">{c['err']}</td>
            <td style="color:#64748b;font-weight:700">{c['miss']}</td>
            <td><b>{c['hit'] / n * 100:.0f}%</b></td>
          </tr>""")
    cmp_html = "\n".join(cmp_rows)
    grand = sum(tot.values()) or 1

    cards = []
    for r in RECORDS:
        if r["score"] is None:
            badge = '<span class="fn f-conclusion">示范</span>'
        else:
            pct = r["score"] / r["full"] * 100
            cls = "f-action" if pct >= 80 else ("f-define" if pct >= 60 else "f-problem")
            badge = f'<span class="fn {cls}">{r["score"]:g} / {r["full"]}</span>'
        cards.append(f"""      <article style="background:#fff;border:1px solid var(--line);border-radius:13px;padding:17px 18px">
        <div style="display:flex;align-items:center;gap:9px;margin-bottom:7px;flex-wrap:wrap">
          <b style="font-size:15.5px">{r['no']}</b>{badge}
          <span style="font-size:12px;color:var(--ink3);margin-left:auto">{r['type']}</span>
        </div>
        <div style="font-size:13.5px;color:var(--ink2);margin-bottom:6px">{r['topic']}</div>
        <div style="font-size:12.5px;color:var(--ink3);margin-bottom:13px">{r['issue']}</div>
        <a href="{r['file']}" style="display:inline-block;font-size:12.5px;border:1px solid #c7d2fe;
           background:#eef2ff;color:#4338ca;padding:5px 14px;border-radius:99px;font-weight:600;text-decoration:none">
          打开三色解剖 →</a>
      </article>""")
    cards_html = "\n".join(cards)

    patterns = "\n".join(
        f"""          <tr>
            <td><b>{p['title']}</b></td>
            <td>{p['body']}</td>
            <td>{p['fix']}</td>
            <td style="white-space:nowrap">{p['status']}</td>
          </tr>"""
        for p in PATTERNS
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>视觉识别 · 评估汇总</title>
<style>{CSS}
.rec{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
</style>
</head>
<body class="plain-mk">

<header>
  <div class="in">
    <span class="kicker">视觉识别 · 评估汇总</span>
    <h1>五次作答：分数、成分、复现的毛病</h1>
    <p class="sub">每一道练习都做了三色解剖 —— 哪些是抄的、哪些是自己写的、错在哪个动作上</p>
    <div class="meta"><span>5 次作答</span><span>4 份三色解剖</span><span>分数 30% → 87%</span></div>
  </div>
</header>

<div class="wrap">

  <section class="card">
    <h2><span class="num">1</span>成长曲线</h2>
    <p class="h2sub">按满分归一化后的得分率。练习 2 满分 10 分，已折算。</p>
    <div class="prog">
{curve}
    </div>
    <div class="tip">
      第一次 4.5 / 15（30%），第五次 13 / 15（87%）。<b>中间只隔了两课。</b>
      这条曲线的斜率说明方法本身是有效的 —— 剩下要做的只是把动作变成习惯。
    </div>
  </section>

  <section class="card">
    <h2><span class="num">2</span>「抄」的占比变化</h2>
    <p class="h2sub">材料原词占答案的比例，由脚本逐字统计。这是「会不会从材料里割肉」最直接的指标。</p>
    <div class="tw">
      <table>
        <thead><tr><th>练习</th><th>题型</th><th>你的答案·抄</th><th>升格版·抄</th><th>说明</th></tr></thead>
        <tbody>
          <tr><td>练习 1</td><td>归纳概括</td><td><b style="color:#dc2626">10.8%</b></td><td>45.8%</td><td>只有 4 个字是材料原词，几乎全靠自己概括</td></tr>
          <tr><td>练习 2</td><td>归纳概括</td><td><b style="color:#d97706">52.9%</b></td><td>67.9%</td><td>做法题天然抄得多，配比已健康</td></tr>
          <tr><td>练习 3</td><td>归纳概括</td><td><b style="color:#059669">66.2%</b></td><td>59.4%</td><td>四份里最高；升格版反而降，因为补了骨架</td></tr>
          <tr><td>练习 5</td><td>综合分析</td><td><b style="color:#7c3aed">30.0%</b></td><td>53.6%</td><td>分析题要自己搭逻辑链，起点天然低</td></tr>
          <tr><td>练习 6</td><td>提出对策</td><td><b style="color:#0891b2">63.0%</b></td><td>55.6%</td><td>抄得比升格版还高，材料利用没问题 —— 问题是抄错了位置（抄进了不采分的问题概括）</td></tr>
          <tr><td>练习 7</td><td>提出对策（变式）</td><td><b style="color:#dc2626">24.9%</b></td><td>64.7%</td><td><b>掉下来了。</b>把「政务App和工作群」概括成「各类政务平台」，采分词在概括中蒸发</td></tr>
        </tbody>
      </table>
    </div>
    <div class="warn">
      <b>两个规律：</b><br>
      ① <b>归纳概括题，「抄」的占比一路从 10.8% 涨到 66.2%</b> —— 你逐步学会了从材料里割肉，而不是自己概括大意。<br>
      ② <b>综合分析题的起点只有 30%</b> —— 因为这类题要自己搭"是什么—为什么—怎么办"，骨架占比高。
      但升格版是 53.6%，说明<b>肉还是得从材料里割</b>，只是骨架要多写几句。<br>
      ③ <b>提出对策题在练习 6→7 之间出现了大波动：63.0% 掉到 24.9%。</b>
      题目从「只提对策」变成「概括表现＋提建议」之后，你在建议段开始用自己的话重说材料的动作句 ——
      而每一个采分词，都是在这次"重说"里丢掉的。<b>概括是给「问题」用的，不是给「对策」用的。</b>
    </div>
  </section>

  <section class="card">
    <h2><span class="num">3</span>逐点对照统计</h2>
    <p class="h2sub">把每道题的参考答案拆成采分点，逐项核对你的答案落在哪一类。数字由脚本实算。</p>
    <div class="tw">
      <table>
        <thead><tr><th>练习</th><th>采分点</th><th>命中</th><th>不完整</th><th>错误</th><th>漏</th><th>命中率</th></tr></thead>
        <tbody>
{cmp_html}
          <tr style="background:#f8f9ff">
            <td><b>合计</b></td><td><b>{grand}</b></td>
            <td style="color:#059669"><b>{tot['hit']}</b></td>
            <td style="color:#d97706"><b>{tot['part']}</b></td>
            <td style="color:#dc2626"><b>{tot['err']}</b></td>
            <td style="color:#64748b"><b>{tot['miss']}</b></td>
            <td><b>{tot['hit'] / grand * 100:.0f}%</b></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="warn">
      <b>看两件事</b>：<br>
      ① <b>命中率在涨</b> —— 这是最直接的进步指标，比总分更稳定，因为它排除了题目难度。<br>
      ② <b>「错误」只有 {tot['err']} 项，全部是同一个毛病</b> —— 用生活经验替换了材料原词。
      这类错最亏：点了找不到，因为你亲手把采分词擦掉了。<br>
      剩下的 {tot['miss']} 项「漏」几乎都能被三个机械动作抓到：<b>数段落、标点切分、见引号就画圈</b>。
    </div>

    <h2 style="margin-top:34px"><span class="num">4</span>逐题三色解剖</h2>
    <p class="h2sub">点进去看每一份答案的逐句成分、升格版、悬停溯源与漏点清单。</p>
    <div class="rec">
{cards_html}
    </div>
  </section>

  <section class="card">
    <h2><span class="num">5</span>反复出现的失分模式</h2>
    <p class="h2sub">按严重程度排序。下次出错时先翻这里，看是不是老毛病又犯了。</p>
    <div class="tw">
      <table>
        <thead><tr><th>毛病</th><th>症状与证据</th><th>处方</th><th>状态</th></tr></thead>
        <tbody>
{patterns}
        </tbody>
      </table>
    </div>
  </section>

</div>

<a class="backbtn" href="index.html">← 总目录</a>
</body>
</html>
"""

# ══════════════════════════════════════════════════════════ 参考答案与逐点对照

REF_WARN = ('评分点依据材料关键句拆分，供教学对照用。<b>不是官方评分标准</b> —— '
            '真实阅卷的采分点由命题方制定，本表的作用是让你看清「标准答案会写什么」与「你写了什么」的逐项差距。')

P1.update(dict(
    compare_sub='把 15 分拆成 8 个采分点，逐项对照。这是本页最该反复看的部分。',
    ref_warn=REF_WARN,
    reference=[
        '整治"指尖上的形式主义"，要减负与增效并举。',
        '当前基层"指尖上的形式主义"主要表现为：一是政务App、微信公众号、工作群泛滥，干部打卡签到、上传照片耗时多，挤占下基层时间；二是只重留痕不重实效，走访拍照、开会录像、学习截屏积分；三是各部门自建平台、数据不互通，同一份材料反复填、重复报，部分App长期不更新，成了"僵尸应用"。',
        '一是清理整合平台。由市委办牵头成立工作专班，对全市政务App和工作群全面摸排；关停整合功能重复的App，精简合并工作群，清理"僵尸应用"，保留一个统一的"掌上政务"平台，推动数据互联互通、避免重复填报。',
        '二是严控增量负担。除中央和省级明确要求外，一律不得新增面向基层的打卡、留痕事项，并纳入年度督查内容。',
        '三是改进考核方式。考核评价要从"看痕迹"转向"看实绩"，多听群众评价、多看工作成效。',
        '四是畅通渠道。畅通基层反映渠道，让干部敢于对不合理的要求说"不"。',
    ],
    compare=[
        dict(point='基础设施老化', ref='管网老化、道路坑洼不平、停车位不足、缺乏电梯等适老化设施', mine='（完全没写）', j='miss', note='<b>第 1 段整段漏答</b> —— 用「数段落」就能发现'),
        dict(point='物业管理缺位', ref='物业费标准低、收缴困难，物业公司频繁退出', mine='物业费难以收取', j='part', note='只写了收费难，漏了「<b>公司频繁退出</b>」'),
        dict(point='业委会缺失、居民参与低', ref='业主委员会缺失，居民参与热情不高', mine='（完全没写）', j='miss', note='第 2 段第 3 句，一句一勾就能抓到'),
        dict(point='居委会人手有限', ref='社区居委会人手有限', mine='（完全没写）', j='miss', note='第 2 段最后一句'),
        dict(point='资金保障不足', ref='改造主要依靠财政投入且总量有限', mine='改造资金筹集困难', j='part', note='只写了总括，没回答「<b>难在哪</b>」'),
        dict(point='社会资本意愿低', ref='社会资本参与意愿不强，项目利润薄、回收周期长', mine='（完全没写）', j='miss', note='第 3 段第 3 句'),
        dict(point='居民意见难统一', ref='改造方案存在分歧，协商久拖不决', mine='居民痛点不同，难以协调一致', j='err', note='<b>「痛点不同」是你自己造的词</b>，材料原词是「存在分歧」'),
        dict(point='政府干、群众看', ref='要避免"政府干、群众看"', mine='（完全没写）', j='miss', note='第 5 段<b>带引号的提法</b>，必抄'),
    ],
))

P2.update(dict(
    compare_sub='把 10 分拆成 7 个采分点。你的问题集中在一处，但值得逐项看清。',
    ref_warn=REF_WARN,
    reference=[
        '一是 A 市推动改造与社区治理相结合，同步成立业主委员会，由居民协商确定改造项目清单和后续管理办法。',
        '二是 B 市引入专业物业企业，采取"先服务、后收费"方式，让居民先感受服务变化再议价。',
        '三是 C 市盘活闲置边角地和屋顶，改造成停车位、光伏电站，以收益补贴物业费，实现"自我造血"。',
    ],
    compare=[
        dict(point='A 市：与社区治理相结合', ref='把老旧小区改造与社区治理结合起来', mine='（未写）', j='miss', note='这一段的总起句，交代了 A 市做法的性质'),
        dict(point='A 市：成立业委会、协商定清单', ref='同步成立业主委员会，由居民协商确定改造<b>项目</b>清单和<b>后续</b>管理办法', mine='成立业主委员会，居民协商确定改造清单和管理办法', j='part', note='漏了「项目」和「后续」二字 —— 都是采分词'),
        dict(point='B 市：引入专业物业企业', ref='B 市<b>引入专业物业企业</b>', mine='（完全没写）', j='miss', note='这是本条的核心动作。<b>只写方式不写动作，等于把脑袋砍了</b>'),
        dict(point='B 市：先服务、后收费', ref='采取"先服务、后收费"的方式', mine='先改造，再进行议价', j='err', note='<b>读错了</b> —— 用生活经验替换了材料原词，材料里没有「改造」这个动作'),
        dict(point='C 市：盘活闲置边角地和屋顶', ref='把小区闲置的<b>边角地、屋顶</b>改造成停车位和光伏电站', mine='利用闲置区域', j='part', note='「闲置区域」太笼统 —— 具体名词比笼统名词值钱'),
        dict(point='C 市：收益补贴物业费', ref='产生的收益用于补贴物业费', mine='收益补贴物业费', j='hit', note='✓ 命中'),
        dict(point='C 市：自我造血', ref='实现了"自我造血"', mine='（完全没写）', j='miss', note='<b>带引号的提法，必抄</b>'),
    ],
))

P3.update(dict(
    compare_sub='把 15 分拆成 13 个采分点。命中率已经不低，差距全在"段落后半截"。',
    ref_warn=REF_WARN,
    reference=[
        '当前乡村民宿发展面临四方面问题：',
        '一是缺乏规划、盲目跟风，未评估资源禀赋、未做市场调研，民宿同质化严重。',
        '二是专业人才短缺，管家、客房、策划岗位缺人；年轻人外流，留守人员年龄偏大、服务意识不足；培训偏理论，效果不佳。',
        '三是资金筹措困难，前期投入大，农房抵押贷款受限；村集体缺少经营主体，难申请项目资金；土地产权不清晰，工商资本中途撤资。',
        '四是配套设施滞后，道路狭窄大巴难进，停车位不足，污水管网未覆盖。',
    ],
    compare=[
        dict(point='缺乏规划、盲目跟风', ref='一些地方一哄而上，盲目跟风', mine='盲目跟风', j='hit', note='✓ 命中'),
        dict(point='未评估资源禀赋、未做市场调研', ref='既没有评估本地资源禀赋，也没有做过市场调研', mine='没有做市场调研', j='part', note='漏了「<b>资源禀赋</b>」这个材料原词'),
        dict(point='民宿同质化', ref='风格雷同、菜品相似，"千店一面"', mine='风格雷同、菜品相似', j='hit', note='✓ 命中（补一个概括词「同质化」更佳）'),
        dict(point='专业岗位缺人', ref='民宿管家、客房服务、活动策划都需要专业人员', mine='服务人才短缺', j='part', note='没写出具体岗位 —— 具体名词更值钱'),
        dict(point='年轻人外流、留守人员素质不足', ref='年轻人大多外出务工，留守人员年龄偏大、缺乏服务意识', mine='年轻人外出打工，剩下年级较大的人缺乏服务意识', j='hit', note='✓ 命中；注意「年<b>级</b>」应为「年<b>龄</b>」'),
        dict(point='培训偏理论、效果不佳', ref='课程偏理论，听完就忘', mine='（完全没写）', j='miss', note='<b>第 2 段第 5 句</b> —— 标点切分法就能抓到'),
        dict(point='前期投入大', ref='装修、消防、卫生、网络都要花钱，至少要投入三十多万元', mine='前期成本高，装修、消防、卫生、网络都需要花钱', j='hit', note='✓ 命中'),
        dict(point='农房抵押贷款受限', ref='银行对农房抵押贷款限制较多', mine='（完全没写）', j='miss', note='<b>第 3 段第 3 句</b> —— 段落后半截'),
        dict(point='村集体缺少经营主体', ref='村里没有集体经营主体，想申请项目资金也无从下手', mine='（完全没写）', j='miss', note='<b>第 3 段第 4 句</b> —— 段落后半截'),
        dict(point='土地产权不清晰、资本撤资', ref='因为土地、产权不清晰，中途撤资', mine='工商资本也因为农村土地产权不清晰而中途撤资', j='hit', note='✓ 命中，归类判断也对'),
        dict(point='道路狭窄、大巴进不来', ref='通往村里的路只有三米宽，旅游大巴进不来', mine='道路窄，旅游大巴进不来', j='hit', note='✓ 命中'),
        dict(point='停车位不足', ref='<b>停车位不足</b>，旺季车辆沿路停放', mine='车位不够', j='part', note='口语化了 —— 应用材料原词「停车位不足」'),
        dict(point='污水管网未覆盖', ref='<b>污水管网没有覆盖</b>，生活污水直排', mine='污水处理设施没有覆盖全', j='part', note='应用材料原词「污水管网未覆盖」'),
    ],
))

# ══════════════════════════════════════════════════════════ 练习 5（综合分析·口袋公园）

GY = [
    dict(no="第 1 段", fn="bg", fnlabel="背景", sents=[("gy1", '近年来，不少城市利用街头边角地、废弃地、闲置地建设口袋公园，见缝插绿，让居民推窗见绿、出门入园。某市两年间建成口袋公园 120 个，新增绿地面积近 30 万平方米。')]),
    dict(no="第 2 段", fn="meaning", fnlabel="意义", sents=[("gy2", '"以前这块地堆着建筑垃圾，现在成了小花园。"居民张大爷说。口袋公园面积虽小，却成了周边老人的"会客厅"——下棋、聊天、晒太阳，孩子们也有地方跑动。有的公园还设置了健身器材和儿童滑梯。')]),
    dict(no="第 3 段", fn="problem", fnlabel="问题 · 反面", sents=[
        ("gy3a", '但一些口袋公园建成后问题不少。有的公园建而不管，座椅破损、灯具不亮，绿化带里杂草丛生；'),
        ("gy3b", '有的设计千篇一律，照搬图纸，缺少座椅和遮阴，一到夏天暴晒，老人不愿意去；'),
        ("gy3c", '还有的重建设、轻维护，建设资金一次性投入，后续管护却无人负责、无钱可用。')]),
    dict(no="第 4 段", fn="action", fnlabel="做法 · 正面", sents=[
        ("gy4a", '一些地方已经开始改进。A 市聘请周边居民担任"市民园长"，参与公园日常巡查和管理；'),
        ("gy4b", 'B 市在建设前征求周边居民意见，根据老人、儿童的实际需要配置座椅、遮阴棚和活动场地；'),
        ("gy4c", 'C 市把公园维护纳入社区共治，发动企业、居民认养绿地。')]),
    dict(no="第 5 段", fn="conclusion", fnlabel="观点 · 结论", sents=[("gy5", '专家指出，口袋公园建设不能只算增量账，更要算质量账。只有建管并重、共建共治，才能让这些小公园真正成为居民的"幸福角"。')]),
]

P5 = dict(
    slug="p5", file="练习5-综合分析-图解.html",
    kicker="视觉识别 · 结果分析 05",
    title="练习 5 三色解剖", sub="口袋公园 · 综合分析（解释型）",
    h1="答案三色解剖：哪些是抄的，哪些是你写的",
    chips=["得分 13 / 15", "第 2 课结业"],
    student_hint="这份答案的三种成分大致各占三分之一 —— 配比是健康的，问题在漏了一个引号词和一句总起。",
    material=GY,
    student=[
        dict(kind="own", label="段 1 · 释义", bg="#fffbeb", fg="#b45309", wc="49 字",
             html='<span class="mk-copy">口袋公园建设</span><span class="mk-cond">不能只追求公园数量、绿地面积等增量指标</span>，<span class="mk-own">更要重视建设品质与长效管护</span>，<span class="mk-cond">兼顾群众实际需求</span>。',
             note='1 抄 + 2 概 + 1 自。<b>「增量指标」这个概括是全篇最亮的一笔</b> —— 你把数据句（120 个／30 万平方米）提了上来，而不是当废字跳过。'),
        dict(kind="cond", label="段 2 · 意义 + 反面", bg="#ecfdf5", fg="#047857", wc="68 字",
             html='<span class="mk-cond">建设口袋公园盘活闲置土地，方便居民就近休闲，改善人居环境</span>。<span class="mk-own">但部分口袋公园存在</span><span class="mk-cond">重建设轻管护、设计同质化、配套不足</span><span class="mk-own">等问题，难以持续发挥作用</span>。',
             note='2 概 + 3 自。<b>三个概括词全部踩在材料上。</b>但本段<b>没有总起句</b>，直接开始罗列问题 —— 对照段 3 有「因此，要坚持……」，两层不对称。<br><b>漏：</b>「方便居民就近休闲」太笼统，把最值钱的「<b>会客厅</b>」丢了。'),
        dict(kind="copy", label="段 3 · 正面 + 结论", bg="#f1f5f9", fg="#475569", wc="90 字",
             html='<span class="mk-own">因此，要坚持</span><span class="mk-copy">建管并重、共建共治</span>。<span class="mk-copy">建设前广泛征集居民意见，按需配置休闲设施</span>；<span class="mk-own">创新管护模式，引入</span><span class="mk-copy">市民园长</span>、<span class="mk-copy">绿地认养</span>、<span class="mk-copy">社区共治</span><span class="mk-own">等机制，落实管护资金与责任</span>，<span class="mk-copy">让口袋公园持续成为群众的幸福角</span>。',
             note='6 抄 + 3 自。<b>三市做法一个不落</b>；「落实管护资金与责任」是你自己补的，对应材料「无人负责、无钱可用」，属于合理加工。<br>「<b>幸福角</b>」这个带引号的词你抄上了 —— 带引号的基本都是采分词。'),
    ],
    upgrade=[
        dict(kind="own", label="释义", bg="#fffbeb", fg="#b45309", src="gy1,gy5", src_label="← 第 1 段 + 第 5 段",
             html='<span class="mk-own">这句话指出，</span><span class="mk-copy">口袋公园建设</span><span class="mk-cond">不能只追求公园数量、绿地面积等增量指标</span>，<span class="mk-own">更要重视建设品质与长效管护</span>，<span class="mk-cond">真正满足群众需求</span>。',
             note='1 抄 + 2 概 + 2 自。释义层。<b>看材料里带引号的词</b>：本段无，靠概括。'),
        dict(kind="copy", label="意义（补回来了）", bg="#f1f5f9", fg="#475569", src="gy2,gy1", src_label="← 第 2 段",
             html='<span class="mk-copy">口袋公园</span><span class="mk-cond">盘活边角地、废弃地</span>，<span class="mk-copy">让居民推窗见绿、出门入园</span>，<span class="mk-copy">也成了老人的"会客厅"和孩子的活动场</span>。',
             note='3 抄 + 1 概。<b>这一句把你丢掉的 1 分捡回来了。</b>「<b>会客厅</b>」带引号，是必须原样抄的采分词。'),
        dict(kind="own", label="反面 · 总起 + 展开", bg="#fef2f2", fg="#b91c1c", src="gy3a,gy3b,gy3c", src_label="← 第 3 段",
             html='<span class="mk-own">但只算增量账，就会</span><span class="mk-copy">建而不管</span>、<span class="mk-cond">设计同质化</span>、<span class="mk-cond">配套不足</span>：<span class="mk-copy">座椅破损无人修</span>，<span class="mk-copy">缺少遮阴老人不愿去</span>，<span class="mk-copy">管护无人无钱</span><span class="mk-own">，难以持续</span>。',
             note='4 抄 + 2 概 + 2 自。开头加了总起「<span class="mk-own">但只算增量账，就会</span>」，<b>与正面层形成对仗</b>；冒号后面把三个问题的具体表现补上，字数也就填满了。'),
        dict(kind="own", label="正面 · 总起 + 对策", bg="#ecfdf5", fg="#047857", src="gy4a,gy4b,gy4c", src_label="← 第 4 段",
             html='<span class="mk-own">算质量账，需要</span><span class="mk-copy">建管并重、共建共治</span>。<span class="mk-copy">建设前广泛征求居民意见，按老人、儿童需要配置设施</span>；<span class="mk-copy">引入"市民园长"</span>、<span class="mk-copy">绿地认养</span>、<span class="mk-copy">社区共治</span>，<span class="mk-own">落实管护资金与责任</span>。',
             note='5 抄 + 2 自。<b>这一层几乎全抄是对的</b> —— 对策本来就该用材料原词。「<span class="mk-own">算质量账，需要</span>」是补的正面总起。'),
        dict(kind="copy", label="结论", bg="#f5f3ff", fg="#6d28d9", src="gy5", src_label="← 第 5 段",
             html='<span class="mk-own">才能</span><span class="mk-copy">让这些小公园真正成为居民的"幸福角"</span>。',
             note='1 抄 + 1 自。结论直接搬材料的现成句。注意「<b>幸福角</b>」带引号。'),
    ],
    ratio_note='<b>你的三种成分大致各占三分之一（抄 30.0%／概 34.8%／自 30.0%），配比是健康的。</b><br><br>'
               '但和升格版一比就看出来了：升格版的「抄」是 <b>53.6%</b>。'
               '字数从 207 补到 248，多出来的 41 字几乎全部来自增加的<b>材料原词</b>（62 → 133 字）—— '
               '也就是把「建而不管」「座椅破损无人修」「缺少遮阴老人不愿去」这些具体表现铺开。<br><br>'
               '<b>升格不是加内容，是把「自己的话」换成「材料的话」。</b>你以为要自己发挥，其实要回去割肉。',
    structure_sub='解释型综合分析的骨架：释义 → 反面（总起 + 问题）→ 正面（总起 + 对策）→ 结论。<b>正反两层必须对称。</b>',
    structure=[
        dict(tone="define", cls="d", label="① 是什么", body='既要……<span class="mk-cond">数量、面积等增量指标</span>，更要……<span class="mk-own">品质与长效管护</span>'),
        dict(tone="problem", cls="p", label="② 只算增量账会怎样", body='<b>总起</b>：<span class="mk-own">但只算增量账，就会</span> → <span class="mk-copy">建而不管</span>、<span class="mk-cond">同质化</span>、<span class="mk-cond">配套不足</span>'),
        dict(tone="action", cls="a", label="③ 算质量账要怎么做", body='<b>总起</b>：<span class="mk-own">算质量账，需要</span> → <span class="mk-copy">市民园长</span>、<span class="mk-copy">认养绿地</span>、<span class="mk-copy">社区共治</span>'),
        dict(tone="conclusion", cls="c", label="④ 结论", body='<span class="mk-own">唯有……才能</span><span class="mk-copy">让这些小公园真正成为居民的"幸福角"</span>'),
    ],
    structure_note='<b>②③ 两句总起必须成对出现。</b>只写一边，骨架就是斜的。<br>'
                   '第 2 课示范里是「<b>只算眼前账，食堂难以为继</b>」对应「<b>算长远账，需多方发力</b>」—— 同一个动作，换道题你就漏了。',
    gaps=[
        dict(item='口袋公园的<b>社会功能</b>', src='第 2 段：却成了周边老人的<b>"会客厅"</b>', how='<b>引号即采分词</b> —— 带引号的地方命题人在跟你打招呼', value='1 分'),
        dict(item='<b>反面层总起句</b>', src='结构问题，不来自材料', how='<b>正反对称自检</b> —— 写完回头看两层有没有对仗的总起', value='0.5 分'),
        dict(item='问题的具体表现（座椅破损、缺遮阴、管护无钱）', src='第 3 段各分句', how='<b>标点切分法</b> —— 一句一勾，勾完再合并', value='0.5 分'),
    ],
    bad=[
        '<b>该抄的没抄</b>：带引号的「会客厅」漏了 —— 这是最不该丢的分',
        '<b>骨架偏斜</b>：正面有总起、反面没有，两层不对称',
        '<b>层次偏薄</b>：207 / 250 字。空格就是分数，材料里的具体表现没铺开',
    ],
    takeaway_sub='这道题只需要带走一件事。',
    takeaways=['<b>写完回头看：反面层和正面层，各有一句总起吗？两句是不是对仗的？</b>'
               '「只算增量账，就会……」对应「算质量账，需要……」。'],
    verdict='<b>成绩：13 / 15　第 2 课结业。</b>首次独立完成综合分析题即拿 13 分，'
            '且「增量指标」这种概括是你自己想到的。剩下的 2 分不在能力上，'
            '在<b>两个可以养成的习惯</b>上：正反对称自检、引号词必抄。',
    compare_sub='把 15 分拆成 13 个采分点。注意看「漏」的两项 —— 一个是引号词，一个是结构。',
    ref_warn=REF_WARN,
    reference=[
        '这句话指出，口袋公园建设不能只追求公园数量、绿地面积等增量指标，更要重视建设品质与长效管护，真正满足群众需求。',
        '口袋公园盘活边角地、废弃地，让居民推窗见绿、出门入园，也成了老人的"会客厅"和孩子的活动场。但只算增量账，就会建而不管、设计同质化、配套不足：座椅破损无人修，缺少遮阴老人不愿去，管护无人无钱，难以持续。',
        '算质量账，需要建管并重、共建共治。建设前广泛征求居民意见，按老人、儿童需要配置设施；引入"市民园长"、绿地认养、社区共治，落实管护资金与责任，才能让这些小公园真正成为居民的"幸福角"。',
    ],
    compare=[
        dict(point='释义：数量面积 vs 品质管护', ref='不能只追求公园数量、绿地面积等增量指标，更要重视建设品质与长效管护', mine='不能只追求公园数量、绿地面积等增量指标，更要重视建设品质与长效管护', j='hit', note='✓ 命中，而且是全篇最亮的一笔'),
        dict(point='释义：递进关系', ref='用「不能只……更要……」复现原句的递进', mine='不能只……更要……', j='hit', note='✓ 命中'),
        dict(point='意义：社会功能', ref='也成了老人的"会客厅"和孩子的活动场', mine='方便居民就近休闲，改善人居环境', j='part', note='<b>太笼统</b> —— 丢了带引号的「会客厅」'),
        dict(point='问题：重建设轻管护', ref='建而不管，座椅破损、灯具不亮；重建设、轻维护', mine='重建设轻管护', j='hit', note='✓ 命中，概括准确'),
        dict(point='问题：设计同质化、配套不足', ref='设计千篇一律，照搬图纸，缺少座椅和遮阴', mine='设计同质化、配套不足', j='hit', note='✓ 命中，概括词自己提炼的'),
        dict(point='问题的具体表现', ref='座椅破损无人修；缺少遮阴老人不愿去；管护无人无钱', mine='（未展开）', j='part', note='用概括词代替了具体表现 —— 字数因此只有 207'),
        dict(point='反面层总起句', ref='但只算增量账，就会……', mine='但部分口袋公园存在……', j='miss', note='<b>结构缺失</b> —— 正面有总起、反面没有，两层不对称'),
        dict(point='对策：征求居民意见、按需配置', ref='建设前广泛征求居民意见，按老人、儿童需要配置设施', mine='建设前广泛征集居民意见，按需配置休闲设施', j='hit', note='✓ 命中'),
        dict(point='对策：市民园长', ref='引入"市民园长"，参与日常巡查和管理', mine='引入市民园长', j='hit', note='✓ 命中，引号词抄对了'),
        dict(point='对策：认养绿地、社区共治', ref='纳入社区共治，发动企业、居民认养绿地', mine='绿地认养、社区共治', j='hit', note='✓ 命中'),
        dict(point='对策：管护资金与责任', ref='（材料强调"无人负责、无钱可用"，需反推）', mine='落实管护资金与责任', j='hit', note='✓ 命中，<b>这是你自己补的合理加工</b>'),
        dict(point='结论：建管并重、共建共治', ref='只有建管并重、共建共治', mine='因此，要坚持建管并重、共建共治', j='hit', note='✓ 命中'),
        dict(point='结论：幸福角', ref='真正成为居民的"幸福角"', mine='让口袋公园持续成为群众的幸福角', j='hit', note='✓ 命中，引号词抄对了'),
    ],
)

# ══════════════════════ 专题页：引号与抽象概念 ══════════════════════

# 材料里带引号的「提法」（名词性概括语）—— 全是采分词
QUOTE_YES = [
    ("撒胡椒面", "练习 1／2 第 4 段", "概括早期改造资金分散"),
    ("先服务、后收费", "练习 1／2 第 4 段", "B 市的物业引入方式"),
    ("自我造血", "练习 1／2 第 4 段", "C 市盘活资源形成收益"),
    ("政府干、群众看", "练习 1／2 第 5 段", "要避免的治理困境"),
    ("千店一面", "练习 3 第 2 段", "民宿同质化"),
    ("太老年化", "第 2 课 第 3 段", "食堂客源结构单一的原因"),
    ("社交场", "第 2 课 第 2 段", "社区食堂的社会价值"),
    ("会客厅", "练习 5 第 2 段", "口袋公园的社会功能"),
    ("市民园长", "练习 5 第 4 段", "A 市的管护机制"),
    ("幸福角", "练习 5 第 5 段", "口袋公园的最终定位"),
]
# 你在这几道题里对它们的处理
QUOTE_USE = {"政府干、群众看": "miss", "自我造血": "miss", "会客厅": "part"}
QUOTE_USE_LABEL = {"hit": ("抄到了", "jd-hit"), "part": ("只沾了一半", "jd-part"),
                   "miss": ("漏了", "jd-miss"), "err": ("写错了", "jd-err")}

# 材料里带引号的「引语」（人物说的整句）—— 不抄整句，挖关键词
QUOTE_SAY = [
    ("最头疼的是物业。", "练习 1／2 第 2 段", "物业管理缺位"),
    ("最大的难题是缺人。", "练习 3 第 2 段", "专业人才短缺"),
    ("风景不错，就是住着不方便。", "练习 3 第 4 段", "配套设施滞后"),
    ("以前这块地堆着建筑垃圾，现在成了小花园。", "练习 5 第 1 段", "盘活闲置边角地、废弃地"),
]


def quote_evidence():
    """从真实数据里算：漏点总数、其中引号词几个。"""
    tot, qmiss = 0, []
    for d in ALL:
        for c in d.get("compare", []):
            if c["j"] != "miss":
                continue
            tot += 1
            for k, _, _ in QUOTE_YES:
                if k in c["point"] or k in c["ref"] or k in c["note"]:
                    qmiss.append((d["slug"], k))
                    break
    return tot, qmiss


def render_quote_page() -> str:
    tot_miss, qmiss = quote_evidence()
    qmiss_names = {k for _, k in qmiss}

    rows = []
    for name, src, mean in QUOTE_YES:
        st = QUOTE_USE.get(name, "hit")
        lb, cl = QUOTE_USE_LABEL[st]
        rows.append(
            f"<tr><td><span class=\"k-quote\">\"{name}\"</span></td><td>{src}</td>"
            f"<td>{mean}</td><td><span class=\"jd {cl}\">{lb}</span></td></tr>"
        )
    quote_rows = "\n".join(rows)

    say_rows = "\n".join(
        f"<tr><td><span class=\"k-quote\">\"{a}\"</span></td><td>{b}</td>"
        f"<td><b>{c}</b></td><td class=\"mine-miss\">{a}</td></tr>"
        for a, b, c in QUOTE_SAY
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>视觉识别 · 数据清洗规则</title>
<style>{CSS}</style>
</head>
<body class="plain-mk">

<header>
  <div class="in">
    <span class="kicker">视觉识别 · 数据清洗</span>
    <h1>引号、抽象概念、比喻：到底抄不抄？</h1>
    <p class="sub">材料里那些「加了引号的话」和「说得很文雅的话」，哪些是采分词</p>
    <div class="meta">
      <span>10 个引号提法</span>
      <span>100% 命中</span>
      <span>{tot_miss} 个漏点里 {len(qmiss)} 个是引号词</span>
    </div>
  </div>
</header>

<div class="wrap">
  <div class="legend">
    <div class="lg-in">
      <span class="t">引号怎么处理</span>
      <span class="chip d"><i></i>提法 → 原样抄</span>
      <span class="chip m"><i></i>引语 → 挖关键词</span>
      <span class="chip p"><i></i>空词 → 不写</span>
      <span class="chip a"><i></i>修辞 → 还原文</span>
    </div>
  </div>

  <section class="card">
    <h2><span class="num">1</span>先给结论：引号是命题人画的重点线</h2>
    <p class="h2sub">这一条比任何技巧都值钱，先记住它。</p>
    <div class="refbox">
      <div class="rh">一句话</div>
      <p style="font-size:17px;font-weight:600;line-height:1.8">
        材料里凡是<b>带引号的、名词性的提法</b>，十有八九就是采分词 —— <b>原样抄进答案，一个字不改。</b>
      </p>
      <p>
        原因很简单：引号是作者在告诉你「这是我概括出来、要你记住的说法」。采分清单就是照着这些说法列的。
        你把它换一个词，阅卷人就找不到那个点了。
      </p>
      <div class="warnline">反过来：<b>考生自己绝对不要造比喻</b>。你写的修辞越多，越不像政府话语，越丢分。</div>
    </div>
    <div class="warn">
      <b>为什么要单独讲这一节</b>：你四道题的 {tot_miss} 个漏点里，有 {len(qmiss)} 个是<b>材料里已经替你概括好的引号词</b> ——
      也就是说，这些分是<b>不用动脑、白送的分</b>，你只是没看见。
    </div>
  </section>

  <section class="card">
    <h2><span class="num">2</span>四种情况，四种处理</h2>
    <p class="h2sub">不能一刀切。先分类，再决定抄还是改。</p>
    <div class="tw">
      <table>
        <thead><tr><th>类型</th><th>长什么样</th><th>怎么处理</th><th>本课例子的做法</th></tr></thead>
        <tbody>
          <tr>
            <td><b>① 提法</b><br><span style="color:var(--ink3);font-size:12px">名词性引号</span></td>
            <td>加引号的短语、口号、经验名、专有说法</td>
            <td><b style="color:#065f46">原样抄</b>，一个字不改</td>
            <td><span class="k-quote">"自我造血"</span><span class="k-quote">"会客厅"</span><span class="k-quote">"市民园长"</span><span class="k-quote">"先服务、后收费"</span> —— 全抄</td>
          </tr>
          <tr>
            <td><b>② 引语</b><br><span style="color:var(--ink3);font-size:12px">人物说的话</span></td>
            <td>加引号的一整句话，通常带「我／我们」和口语</td>
            <td><b style="color:#92400e">不抄整句</b>，把里面的关键词挖出来</td>
            <td>"最头疼的是物业" → 写成 <b>物业管理缺位</b>（不是抄那句话）</td>
          </tr>
          <tr>
            <td><b>③ 抽象概念</b><br><span style="color:var(--ink3);font-size:12px">上位词／概括词</span></td>
            <td>"基层治理能力""同质化""全龄段"这类</td>
            <td>问一句：<b>材料里有支撑吗？</b>有 → 可抄可概括；没有 → 空词，不写</td>
            <td>"同质化"有材料支撑（千店一面）→ 可抄；"提高认识""加强重视"没支撑 → 不写</td>
          </tr>
          <tr>
            <td><b>④ 修辞比喻</b><br><span style="color:var(--ink3);font-size:12px">抒情／口号</span></td>
            <td>比喻、排比、文学化表达、宣传标语</td>
            <td><b style="color:#991b1b">不抄</b>，还原成实务语言</td>
            <td>"改造不是简单刷墙铺路" → 写成 <b>重建设轻管护</b></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="warn">
      <b>最快的一句话判断法</b>：看引号里是不是一个<b>名词短语</b>。<br>
      是 → 提法，抄。<br>
      是一整句人话（有我、有口语、有语气）→ 引语，只挖关键词。
    </div>
  </section>

  <section class="card">
    <h2><span class="num">3</span>证据一：你这几份材料里，带引号的提法全中了</h2>
    <p class="h2sub">从你做过和看过的材料里，把所有带引号的名词性提法全部挑出来，逐个核对是不是采分词。</p>
    <div class="tw">
      <table>
        <thead><tr><th>带引号的提法</th><th>出处</th><th>它概括的是什么</th><th>你的处理</th></tr></thead>
        <tbody>
{quote_rows}
        </tbody>
      </table>
    </div>
    <div class="refbox" style="margin-top:16px">
      <div class="rh">结论</div>
      <p><b>10 个提法，10 个都是采分词，命中率 100%。</b>这不是巧合 —— 命题人写材料时就拿这些说法当得分点。</p>
      <p>而你在这几道题里的处理是：<b>抄对 7 个，漏 2 个，只沾一半 1 个</b>。
      漏掉的那 {len(qmiss)} 个（{'、'.join('「' + k + '」' for k in sorted(qmiss_names))}）就是白送的分。</p>
    </div>
  </section>

  <section class="card">
    <h2><span class="num">4</span>证据二：带引号的「引语」不能整句抄</h2>
    <p class="h2sub">这些引号里是一句完整的人话。它不是答案，它是路标 —— 指向旁边那个答案。</p>
    <div class="tw">
      <table>
        <thead><tr><th>材料原话（引语）</th><th>出处</th><th>该在答案里写什么</th><th>抄整句会怎样</th></tr></thead>
        <tbody>
{say_rows}
        </tbody>
      </table>
    </div>
    <div class="warn">
      <b>区别就一句话</b>：引语是<b>证据</b>，提法是<b>答案</b>。<br>
      引语告诉你「老百姓在抱怨什么」，你要做的是把抱怨翻译成<b>政府语言的规范表述</b>；
      提法本身就是规范表述，直接搬。
    </div>
  </section>

  <section class="card">
    <h2><span class="num">5</span>反向警告：你自己一个字都别造比喻</h2>
    <p class="h2sub">这是零基础最容易犯的错 —— 以为写得漂亮能加分。申论阅卷不认文采。</p>
    <div class="tw">
      <table>
        <thead><tr><th>别这么写</th><th>为什么不行</th><th>改成</th></tr></thead>
        <tbody>
          <tr><td style="color:#991b1b">打通任督二脉</td><td>武侠比喻，不是政府话语</td><td><b>畅通体制机制</b></td></tr>
          <tr><td style="color:#991b1b">让政策落地生根、开花结果</td><td>排比抒情，没有信息量</td><td><b>推动政策落实见效</b></td></tr>
          <tr><td style="color:#991b1b">为发展注入源头活水</td><td>口号式表达，阅卷人划不到点</td><td><b>加大财政投入力度</b></td></tr>
          <tr><td style="color:#991b1b">让幸福在家门口升级</td><td>宣传标语，不是分析</td><td><b>完善社区服务设施</b></td></tr>
          <tr><td style="color:#991b1b">擦亮城市名片</td><td>空转的宏大词</td><td><b>提升城市形象和知名度</b></td></tr>
        </tbody>
      </table>
    </div>
    <div class="bad" style="margin-top:16px">
      <b style="color:#991b1b">一句话记法</b>
      <ul>
        <li><b>抄命题人写的话，不抄作者写的修辞。</b></li>
        <li>材料里的比喻（"刷墙铺路""千店一面"）→ 翻译成实务语言再写。</li>
        <li>你自己脑子里的比喻 → 一个都别写。</li>
      </ul>
    </div>
  </section>

  <section class="card">
    <h2><span class="num">6</span>动笔清单（下次读材料就按这个走）</h2>
    <p class="h2sub">六步，全部是机械动作，不需要灵感。</p>
    <div class="prog">
      <div class="frow"><div class="fl" style="color:#4338ca">1</div><div class="fb"><b>见引号就画圈。</b>读材料时手不停，所有 " " 里的内容先用荧光笔圈出来。</div></div>
      <div class="frow"><div class="fl" style="color:#4338ca">2</div><div class="fb"><b>分类。</b>名词短语 → 提法；完整人话 → 引语。</div></div>
      <div class="frow"><div class="fl" style="color:#4338ca">3</div><div class="fb"><b>提法原样搬。</b>一个字不改地抄进答案。</div></div>
      <div class="frow"><div class="fl" style="color:#4338ca">4</div><div class="fb"><b>引语挖词。</b>问一句「他到底在抱怨哪件事」，把这个<em>事</em>写成规范表述。</div></div>
      <div class="frow"><div class="fl" style="color:#4338ca">5</div><div class="fb"><b>抽象概念过一道筛。</b>材料里找得到支撑 → 留；找不到 → 是空词，删。</div></div>
      <div class="frow"><div class="fl" style="color:#4338ca">6</div><div class="fb"><b>交卷前数引号。</b>材料里有几个引号？我抄进去几个？对不上就回去补。</div></div>
    </div>
    <div class="warn" style="margin-top:16px">
      第 6 步是这一节最该带走的动作 —— 它和「数段落」「标点切分」是同一类东西：<b>把看不见的漏点变成数得出来的数字。</b>
    </div>
  </section>

  <section class="card">
    <h2><span class="num">7</span>自测：这三题答完，这一节才算过</h2>
    <p class="h2sub">不看上面，自己先答，再回去对。</p>
    <div class="prog">
      <div class="frow"><div class="fl" style="color:#4338ca">1</div><div class="fb">练习 3 的材料里出现 <span class="k-quote">"千店一面"</span>，你写答案时该怎么处理？</div></div>
      <div class="frow"><div class="fl" style="color:#4338ca">2</div><div class="fb">材料写「最大的难题是缺人」，你的答案里应该出现哪几个字？为什么不是直接抄那句话？</div></div>
      <div class="frow"><div class="fl" style="color:#4338ca">3</div><div class="fb">下面三项，哪些可以直接抄进答案？<br>
        <span class="k-quote">"风景不错，就是住着不方便"</span>　
        <span class="k-quote">"市民园长"</span>　
        <span class="k-quote">"以前这块地堆着建筑垃圾"</span></div></div>
    </div>
    <div class="warn" style="margin-top:16px">
      答完发给我，我按标准答案给你对一遍。这一节的目标不是「知道」，是<b>读材料时手会自己画圈</b>。
    </div>
  </section>

  <p style="text-align:center;color:var(--ink3);font-size:12.5px;margin:34px 0 0">
    申论学习库 ｜ <a href="练习档案.html" style="color:#4338ca">← 练习档案</a>
  </p>
</div>
</body>
</html>
"""


ZJ = [  # 指尖上的形式主义
    dict(no="第 1 段", fn="bg", fnlabel="背景", sents=[
        ("zj1", '近年来，各地各部门积极推进政务信息化，各类政务 App、微信公众号、工作群大量涌现。据报道，某省一名乡镇干部手机里装了 20 多个工作类 App，加入了 30 多个工作群，每天光打卡、签到、上传照片就要花两个多小时。')]),
    dict(no="第 2 段", fn="problem", fnlabel="问题 · 负担", sents=[
        ("zj2a", '"上面千条线，下面一根针。"中部某镇党委书记说，很多 App 只重留痕不重实效，走访要拍照、开会要录视频、学习要截屏积分，干部被"绑"在手机上，真正下村入户的时间反而少了。')]),
    dict(no="第 3 段", fn="problem", fnlabel="问题 · 重复建设", sents=[
        ("zj3a", '记者调查发现，一些地方各部门各自建平台，数据不互通，同一份材料要反复填、重复报。'),
        ("zj3b", '有的 App 上线后长期不更新，成了"僵尸应用"。基层干部反映："填表填到手软，报数据报到心累。"')]),
    dict(no="第 4 段", fn="action", fnlabel="做法 · 白送分", sents=[
        ("zj4a", '针对这些问题，东部某市开展了专项整治。该市成立由市委办牵头的工作专班，对全市政务 App 和工作群全面摸排，关停整合功能重复的 App 47 个，保留一个统一的"掌上政务"平台；'),
        ("zj4b", '同时出台规定，除中央和省级明确要求外，一律不得新增面向基层的打卡、留痕事项，并将此项要求纳入年度督查内容。')]),
    dict(no="第 5 段", fn="conclusion", fnlabel="专家建议 · 白送分", sents=[
        ("zj5", '有专家指出，整治形式主义不能只做"减法"，还要做"加法"：考核评价要从"看痕迹"转向"看实绩"，多听群众评价、多看工作成效；同时要畅通基层反映渠道，让干部敢于对不合理的要求说"不"。')]),
]


P6 = dict(
    slug="p6", file="练习6-提出对策-图解.html",
    kicker="视觉识别 · 结果分析 06",
    title="练习 6 三色解剖", sub="指尖上的形式主义 · 提出对策",
    h1="三色解剖：四成字数写在了不采分的地方",
    chips=["得分 15 / 20", "第 3 课 · 提出对策"],
    student_hint="这份答案的抄写配比是健康的（抄 63.0%），比升格版还高。问题不在比例，在位置。",
    material=ZJ,
    student=[
        dict(kind="problem", label="问题概括 · 119 字 · 占 39.7%", bg="#fef2f2", fg="#b91c1c", wc="119 字 · 不采分",
             html='<span class="mk-own">在</span><span class="mk-copy">政务信息化</span><span class="mk-own">的背景下，</span><span class="mk-copy">各类政务App、微信公众号、工作群大量涌现</span><span class="mk-own">，严重影响了干部的干活效率，</span><span class="mk-copy">打卡签到</span><span class="mk-own">占据了大量时间，而且这些</span><span class="mk-copy">App只重留痕不重实效</span><span class="mk-own">，</span><span class="mk-copy">干部被绑在手机上</span><span class="mk-own">，真正入户的时间反而减少了; </span><span class="mk-copy">数据不互通</span><span class="mk-own">，</span><span class="mk-cond">反复填写</span><span class="mk-own">、</span><span class="mk-cond">上线后不更新</span><span class="mk-own">等诸多问题。</span>',
             note='题目只问「提出对策建议」，没问「存在什么问题」。这 119 字拿不到任何采分点 —— 而它占掉的篇幅，正好够写你漏掉的那条「成立专班、全面摸排」。'),
        dict(kind="action", label="对策 · 181 字 · 占 60.3%", bg="#ecfdf5", fg="#047857", wc="181 字 · 采分都在这里",
             html='<span class="mk-own">针对这些问题，</span><span class="mk-copy">东部某市开展了专项整治</span><span class="mk-own">，1. </span><span class="mk-copy">关停整合功能重复的App</span><span class="mk-own">，处理</span><span class="mk-copy">僵尸应用</span><span class="mk-own"> 2. </span><span class="mk-copy">保留一个统一的"掌上政务"平台</span><span class="mk-own">，做到</span><span class="mk-copy">数据互通</span><span class="mk-own">;3. </span><span class="mk-copy">除中央和省级明确要求外，一律不得新增面向基层的打卡、留痕事项</span><span class="mk-own">，并将此项要求</span><span class="mk-copy">纳入年度督查内容</span><span class="mk-own">。此外还要整治形式主义，</span><span class="mk-copy">考核评价</span><span class="mk-own">应当</span><span class="mk-copy">从看痕迹转向看实绩，多听群众评价，多看工作成效</span><span class="mk-own">；要</span><span class="mk-copy">畅通基层反映渠道</span><span class="mk-own">，</span><span class="mk-copy">让干部敢于对不合理的要求说"不"</span><span class="mk-own">。</span>',
             note='这一段 74% 是材料原词，十个采分点里你写到的八个全在这里 —— 抄写能力没有问题。真正的问题是：只分了三条，最后一条还散在散文里。'),
    ],
    upgrade=[
        dict(kind="define", label="总起", bg="#eff6ff", fg="#1d4ed8", src="", src_label="← 全篇（自己搭的骨架）",
             html='<span class="mk-own">整治"指尖上的形式主义"，要</span><span class="mk-copy">减负</span><span class="mk-own">与</span><span class="mk-copy">增效</span><span class="mk-own">并举、标本兼治。</span>',
             note='"减负""增效"是材料里的词，其余是自己搭的框 —— 一句总起，阅卷人立刻知道你有几条。'),
        dict(kind="action", label="一 · 清理整合平台", bg="#ecfdf5", fg="#047857", src="zj4a,zj3a,zj3b", src_label="← 第 4 段 + 第 3 段反推",
             html='<span class="mk-own">一是清理整合平台。由党委办牵头</span><span class="mk-copy">成立工作专班</span><span class="mk-own">，</span><span class="mk-copy">全面摸排政务App和工作群</span><span class="mk-own">；</span><span class="mk-copy">关停整合功能重复的App</span><span class="mk-own">，</span><span class="mk-copy">清理长期不更新的"僵尸应用"</span><span class="mk-own">，</span><span class="mk-copy">保留一个统一的"掌上政务"平台</span><span class="mk-own">，推动</span><span class="mk-copy">数据互联互通</span><span class="mk-own">、避免</span><span class="mk-cond">重复填报</span><span class="mk-own">。</span>',
             note='把第 4 段的做法句和第 3 段的问题反推拼成一条 —— 这就是对策题最标准的动作。'),
        dict(kind="action", label="二 · 严控增量负担", bg="#ecfdf5", fg="#047857", src="zj4b,zj1,zj2a", src_label="← 第 4 段 + 第 1、2 段反推",
             html='<span class="mk-own">二是严控增量负担。出台规定，</span><span class="mk-copy">除中央和省级明确要求外，一律不得新增面向基层的打卡、留痕事项</span><span class="mk-own">，并将此项要求</span><span class="mk-copy">纳入年度督查内容</span><span class="mk-own">；</span><span class="mk-cond">精简合并工作群</span><span class="mk-own">，让干部有时间下基层。</span>',
             note='"精简合并工作群"是反推 —— 材料用两段讲这个负担，对策里必须回应它，否则等于没听见前两段。'),
        dict(kind="action", label="三 · 改进考核方式", bg="#ecfdf5", fg="#047857", src="zj5", src_label="← 第 5 段",
             html='<span class="mk-own">三是改进考核方式。</span><span class="mk-copy">考核评价要从"看痕迹"转向"看实绩"</span><span class="mk-own">，</span><span class="mk-copy">多听群众评价、多看工作成效</span><span class="mk-own">。</span>',
             note='整句搬运，两个引号全部保住 —— 白送的分，一个字都别改。'),
        dict(kind="action", label="四 · 畅通反映渠道", bg="#ecfdf5", fg="#047857", src="zj5", src_label="← 第 5 段",
             html='<span class="mk-own">四是畅通反映渠道。</span><span class="mk-copy">让干部敢于对不合理的要求说"不"</span><span class="mk-own">，从源头减少层层加码。</span>',
             note='收束半句是自己加的，不采分，但让这一条站得住。'),
    ],
    ratio_note=('<b>你的「抄」占比 63.0%，比升格版的 55.6% 还高。单看这个数字，你的材料利用能力完全没问题 —— 前五道题练出来的抄写习惯还在。</b><br><br>'
                '这一题丢分不在比例，在<b>位置</b>：189 字材料原词里，有 55 字抄进了不采分的问题概括段。'
                '升格版把问题概括整段删掉，腾出的篇幅用来搭「一是……二是……三是……四是……」的骨架 —— '
                '所以它的「自」从 33.7% 涨到 40.5%，<b>涨的全是结构，不是空话</b>。'),
    structure_sub="对策题的结构比什么都简单：题目问几个动作，答案就分几块。",
    structure=[
        dict(tone="define", cls="d", label="① 题目只要一件事", body='<span class="mk-own">就「如何整治」</span><span class="mk-copy">提出对策建议</span> → 只写对策'),
        dict(tone="problem", cls="p", label="② 你却先写了一件事（0 分）", body='<span class="mk-own">问题概括</span> <b>119 字</b>（39.7%）→ 不采分，还挤掉了篇幅'),
        dict(tone="action", cls="a", label="③ 再写要对的事（采分）", body='<span class="mk-copy">关停整合 App</span>、<span class="mk-copy">保留统一平台</span>、<span class="mk-copy">严控打卡留痕</span>、<span class="mk-copy">考核转向实绩</span> → <b>7 个完整 + 1 个不完整</b>'),
        dict(tone="conclusion", cls="c", label="④ 正确结构", body='<span class="mk-own">一句总起</span> + <span class="mk-own">四五条编号对策，每条一个中心句</span>'),
    ],
    structure_note=('<b>前半段是散文，后半段突然冒出 1./2./3. —— 阅卷人翻到中间才发现你在列对策。</b><br>'
                    '正确做法：从第一句就进入「我建议……」，并把对策分条编号，每条第一句点明做什么。'),
    gaps=[
        dict(item='<b>成立工作专班、明确牵头部门</b>', src='第 4 段：该市成立由市委办牵头的工作专班', how='<b>对策公式第一格</b> —— "谁来做"，答不上来就是空话', value='2 分'),
        dict(item='<b>全面摸排政务 App 和工作群</b>', src='第 4 段：对全市政务 App 和工作群全面摸排', how='<b>做法句直抄</b> —— 它排在"关停整合"前面，是前提', value='2 分'),
        dict(item='「僵尸应用」的<b>引号</b>与「清理」二字', src='第 3 段：成了<b>"僵尸应用"</b>', how='<b>引号即采分词</b>；你写的"处理"太笼统，材料原词是"清理"', value='表述分'),
        dict(item='（反推）精简工作群、减少打卡签到', src='第 1、2 段：30 多个工作群／干部被"绑"在手机上', how='<b>从问题反推</b> —— 材料花两段讲这个负担，对策必须回应', value='未列入本表采分点'),
    ],
    bad=[
        '「<b>东部某市开展了专项整治</b>，1. 关停整合……」—— 你在<b>介绍某市做了什么</b>，题目要的是<b>你提出建议</b>。删掉"东部某市"，经验才能变成普适对策。',
        '对策只有 3 条编号加一段散文，<b>条数太少</b>。十个采分点至少要摊到 4~5 条，一条讲清一件事。',
        '<b>没有总起句</b>，也没有条内中心句，阅卷人得自己从你的句子里找采分点 —— 找漏了就是你没写。',
        '问题概括占了 <b>40% 篇幅</b>，是这次最大的浪费。压成一句「当前基层 App 多、打卡多、数据不互通」就够。',
    ],
    takeaway_sub='这道题只需要带走一件事。',
    takeaways=[
        '<b>动笔前先数一遍：题目问了几个动作？问几个，答案就分几块。</b>'
        '只问「提出对策建议」，就只写对策；问「概括问题并提出建议」，才写问题+对策两段。'
        '这一题你花了 119 字写题目没问的东西 —— 那不是不会写，是没看清题。'
    ],
    verdict=('<b>成绩：15 / 20。</b>十个采分点，写全了七个、写残了一个（15 分）。<br>'
             '漏掉的两条 —— 「成立专班、全面摸排」和「精简工作群」—— 都卡在同一个地方：'
             '<b>119 字（39.7%）的篇幅去写了题目根本没问的问题概括</b>。<br>'
             '这一题的失分和你的写作能力<b>完全无关</b>，全在「问什么答什么」上。'
             '把问题概括压成一句话，你就能拿 18~19 分。'),
    compare_sub='把 20 分拆成 10 个采分点，逐项对照。注意看两个「漏」—— 它们都来自同一个原因：篇幅被问题概括吃掉了。',
    ref_warn=REF_WARN,
    reference=[
        '整治"指尖上的形式主义"，要减负与增效并举、标本兼治。',
        '一是清理整合平台。由党委办牵头成立工作专班，全面摸排政务 App 和工作群；关停整合功能重复的 App，清理长期不更新的"僵尸应用"，保留一个统一的"掌上政务"平台，推动数据互联互通、避免重复填报。',
        '二是严控增量负担。出台规定，除中央和省级明确要求外，一律不得新增面向基层的打卡、留痕事项，并将此项要求纳入年度督查内容；精简合并工作群，让干部有时间下基层。',
        '三是改进考核方式。考核评价要从"看痕迹"转向"看实绩"，多听群众评价、多看工作成效。',
        '四是畅通反映渠道。让干部敢于对不合理的要求说"不"，从源头减少层层加码。',
    ],
    compare=[
        dict(point='成立工作专班、明确牵头部门', ref='成立由市委办牵头的工作专班', mine='（完全没写）', j='miss',
             note='第 4 段第 1 句 —— 对策公式的第一格"谁来做"，整条丢失'),
        dict(point='全面摸排政务 App 和工作群', ref='对全市政务 App 和工作群全面摸排', mine='（完全没写）', j='miss',
             note='第 4 段第 1 句 —— 排在"关停整合"之前，是它的前提条件'),
        dict(point='关停整合功能重复的 App', ref='关停整合功能重复的 App 47 个', mine='关停整合功能重复的App', j='hit',
             note='第 4 段 —— 一字不差，抄对了'),
        dict(point='清理长期不更新的"僵尸应用"', ref='清理"僵尸应用"', mine='处理僵尸应用', j='part',
             note='第 3 段 —— 意思到了，但引号丢了、"处理"太笼统，材料原词是"清理"'),
        dict(point='保留一个统一的政务平台', ref='保留一个统一的"掌上政务"平台', mine='保留一个统一的"掌上政务"平台', j='hit',
             note='第 4 段 —— 连引号带平台名一起搬，抄得很准'),
        dict(point='推动数据互联互通、避免重复填报', ref='（第 3 段问题反推）推动数据互联互通、避免重复填报', mine='做到数据互通', j='hit',
             note='第 4 段 + 第 3 段 —— 意思到位，但只写"数据互通"，漏了"避免重复填报"这半截'),
        dict(point='严控新增打卡留痕、纳入年度督查', ref='一律不得新增面向基层的打卡、留痕事项，并将此项要求纳入年度督查内容', mine='一律不得新增面向基层的打卡、留痕事项，并将此项要求纳入年度督查内容', j='hit',
             note='第 4 段 —— 完整搬运，一个"一律"、一个"将"都没漏'),
        dict(point='考核评价从"看痕迹"转向"看实绩"', ref='考核评价要从"看痕迹"转向"看实绩"', mine='考核评价应当从看痕迹转向看实绩', j='hit',
             note='第 5 段 —— 意思完全对，但两个引号都丢了；带引号的提法丢了引号就是丢了信号'),
        dict(point='多听群众评价、多看工作成效', ref='多听群众评价、多看工作成效', mine='多听群众评价，多看工作成效', j='hit',
             note='第 5 段 —— 抄对了，顿号换成逗号不影响采分'),
        dict(point='畅通基层反映渠道、敢说"不"', ref='畅通基层反映渠道，让干部敢于对不合理的要求说"不"', mine='要畅通基层反映渠道，让干部敢于对不合理的要求说"不"', j='hit',
             note='第 5 段 —— 抄对了，引号也保住了'),
    ],
)

P7 = dict(
    slug="p7", file="练习7-提出对策-图解.html",
    kicker="视觉识别 · 结果分析 07",
    title="练习 7 三色解剖", sub="指尖上的形式主义 · 概括表现 + 提出建议（变式）",
    h1="三色解剖：审题对了，但「概括」把采分词吃掉了",
    chips=["得分 21 / 25", "第 3 课 · 变式题"],
    student_hint="材料一个字没变，只换了题目。结构这次完全正确 —— 但篇幅配比和「概括掉原词」两个问题露出来了。",
    material=ZJ,
    student=[
        dict(kind="meaning", label="表现 · 190 字 · 占 49.4%", bg="#eff6ff", fg="#1d4ed8", wc="190 字 · 该占 1/3",
             html='<span class="mk-own">当前基层</span><span class="mk-copy">"指尖上的形式主义"</span><span class="mk-own">问题突出，主要表现为：一是</span><span class="mk-cond">政务线上平台泛滥</span><span class="mk-own">，</span><span class="mk-copy">各类政务APP、工作群</span><span class="mk-cond">数量过多</span><span class="mk-own">，基层干部需耗费</span><span class="mk-cond">大量时间</span><span class="mk-copy">打卡签到</span><span class="mk-own">、</span><span class="mk-cond">上传素材</span><span class="mk-own">，挤占一线工作时间。二是</span><span class="mk-copy">重留痕轻实效</span><span class="mk-own">，工作过度依赖</span><span class="mk-copy">拍照、录视频、截屏积分</span><span class="mk-own">等</span><span class="mk-cond">留痕操作</span><span class="mk-own">，脱离实际工作需求，弱化工作实效。三是</span><span class="mk-cond">平台建设混乱</span><span class="mk-own">，各部门</span><span class="mk-copy">自建平台</span><span class="mk-own">、</span><span class="mk-copy">数据不互通</span><span class="mk-own">，</span><span class="mk-cond">报表材料重复上报</span><span class="mk-own">，且部分APP长期不更新，沦为</span><span class="mk-copy">"僵尸应用"</span><span class="mk-own">，加重基层负担。</span>',
             note='四个表现点<b>全部写到了</b>，而且「打卡签到」「重留痕轻实效」「数据不互通」「僵尸应用」都是材料原词 —— 这一段可以拿满分。<br>唯一的问题：<b>它写得太长了。</b>190 字占了全文 49.4%，而表现只该占 1/3。'),
        dict(kind="action", label="建议 · 195 字 · 占 50.6%", bg="#ecfdf5", fg="#047857", wc="195 字 · 该占 2/3",
             html='<span class="mk-own">对此，提出如下整治建议：一是开展专项摸排整治，</span><span class="mk-cond">组建专项工作专班</span><span class="mk-own">，</span><span class="mk-cond">全面梳理排查</span><span class="mk-own">各类政务平台，</span><span class="mk-copy">整合关停</span><span class="mk-own">功能重复、</span><span class="mk-cond">低效闲置的APP</span><span class="mk-own">，搭建统一规范的政务平台。二是规范线上工作要求，</span><span class="mk-copy">严控新增基层打卡、留痕事项</span><span class="mk-own">，将减负工作</span><span class="mk-copy">纳入年度督查</span><span class="mk-own">，杜绝随意加码。三是优化考核评价机制，</span><span class="mk-cond">摒弃唯痕迹的考核模式</span><span class="mk-own">，以</span><span class="mk-copy">工作实绩</span><span class="mk-own">、</span><span class="mk-copy">群众评价</span><span class="mk-own">作为核心考核标准。四是</span><span class="mk-copy">畅通基层反馈渠道</span><span class="mk-own">，保障基层干部话语权，</span><span class="mk-cond">允许基层抵制不合理工作要求。</span>',
             note='结构对、条数够、有编号 —— 比练习 6 进步很大。<br>但<b>「抄」只有 20%</b>：材料里明明写着「对全市政务App和<b>工作群</b>全面摸排」，你概括成「各类政务平台」，<b>「工作群」三个字就没了</b>；材料写「保留一个统一的<b>"掌上政务"平台</b>」，你换成「搭建统一规范的政务平台」，<b>引号提法也丢了</b>。'),
    ],
    upgrade=[
        dict(kind="define", label="总起", bg="#eff6ff", fg="#1d4ed8", src="", src_label="← 全篇（自己搭的骨架）",
             html='<span class="mk-own">整治"指尖上的形式主义"，要</span><span class="mk-copy">减负</span><span class="mk-own">与</span><span class="mk-copy">增效</span><span class="mk-own">并举。</span>',
             note='一句总起，阅卷人立刻知道你要分几条。'),
        dict(kind="meaning", label="一 · 表现（压到 1/3）", bg="#eff6ff", fg="#1d4ed8", src="zj1,zj2a,zj3a,zj3b", src_label="← 第 1、2、3 段",
             html='<span class="mk-own">当前基层</span><span class="mk-copy">"指尖上的形式主义"</span><span class="mk-own">主要表现为：一是</span><span class="mk-copy">政务App、微信公众号、工作群</span><span class="mk-cond">泛滥</span><span class="mk-own">，干部</span><span class="mk-copy">打卡签到、上传照片</span><span class="mk-cond">耗时多，挤占下基层时间</span><span class="mk-own">；二是</span><span class="mk-copy">只重留痕不重实效</span><span class="mk-own">，</span><span class="mk-copy">走访拍照、开会录像、学习截屏积分</span><span class="mk-own">；三是各部门</span><span class="mk-copy">自建平台、数据不互通</span><span class="mk-own">，</span><span class="mk-copy">同一份材料反复填、重复报</span><span class="mk-own">，部分App</span><span class="mk-copy">长期不更新</span><span class="mk-own">，成了</span><span class="mk-copy">"僵尸应用"</span><span class="mk-own">。</span>',
             note='同样四个点，压到 125 字 —— 每个点只留「材料原词 + 一个短判断」，不解释、不铺陈。省下的 60 字正好够补一条建议。'),
        dict(kind="action", label="二 · 清理整合平台", bg="#ecfdf5", fg="#047857", src="zj4a,zj3a,zj3b", src_label="← 第 4 段 + 第 3 段反推",
             html='<span class="mk-own">一是清理整合平台。由市委办牵头</span><span class="mk-copy">成立工作专班</span><span class="mk-own">，</span><span class="mk-copy">对全市政务App和工作群全面摸排</span><span class="mk-own">；</span><span class="mk-copy">关停整合功能重复的App</span><span class="mk-own">，</span><span class="mk-cond">精简合并工作群</span><span class="mk-own">，</span><span class="mk-copy">清理"僵尸应用"</span><span class="mk-own">，</span><span class="mk-copy">保留一个统一的"掌上政务"平台</span><span class="mk-own">，推动</span><span class="mk-copy">数据互联互通</span><span class="mk-own">、避免</span><span class="mk-cond">重复填报</span><span class="mk-own">。</span>',
             note='材料里的「政务App<b>和工作群</b>」原样搬进来，「工作群」就不会丢；「掌上政务」「僵尸应用」两个引号提法也一个不落。'),
        dict(kind="action", label="三 · 严控增量负担", bg="#ecfdf5", fg="#047857", src="zj4b,zj1,zj2a", src_label="← 第 4 段 + 第 1、2 段反推",
             html='<span class="mk-own">二是严控增量负担。</span><span class="mk-copy">除中央和省级明确要求外，一律不得新增面向基层的打卡、留痕事项</span><span class="mk-own">，并</span><span class="mk-copy">纳入年度督查内容</span><span class="mk-own">。</span>',
             note='整句搬运，一个字不改 —— 这是白送的分。'),
        dict(kind="action", label="四 · 改进考核方式", bg="#ecfdf5", fg="#047857", src="zj5", src_label="← 第 5 段",
             html='<span class="mk-own">三是改进考核方式。</span><span class="mk-copy">考核评价要从"看痕迹"转向"看实绩"</span><span class="mk-own">，</span><span class="mk-copy">多听群众评价、多看工作成效</span><span class="mk-own">。</span>',
             note='专家建议句就是标准答案 —— 两个引号全保住。'),
        dict(kind="action", label="五 · 畅通渠道", bg="#ecfdf5", fg="#047857", src="zj5", src_label="← 第 5 段",
             html='<span class="mk-own">四是畅通渠道。</span><span class="mk-copy">畅通基层反映渠道</span><span class="mk-own">，</span><span class="mk-copy">让干部敢于对不合理的要求说"不"</span><span class="mk-own">。</span>',
             note='也是整句搬运。你写的是「畅通基层<b>反馈</b>渠道」，材料是「<b>反映</b>渠道」—— 一字之差，阅卷人扫的时候仍然认得出。'),
    ],
    ratio_note=('<b>这道题最值得看的数字是篇幅比：表现 190 字（49.4%）／建议 195 字（50.6%）—— 几乎一比一。</b><br><br>'
                '而题目两个动作的<b>分值不相等</b>：表现 4 个点约占 10 分，建议 8 个点约占 15 分。'
                '分数多的地方，篇幅就该多。黄金比是<b>表现 1/3、建议 2/3</b>。<br><br>'
                '你多写的这 60 字表现，正好是一条完整建议的篇幅 —— 而你漏掉的那两条（推动数据互联互通、精简工作群），'
                '加起来也就 60 字。<b>不是没时间写，是篇幅被表现吃掉了。</b>'),
    structure_sub="审题这一关你过了。这次的结构问题只剩「配比」。",
    structure=[
        dict(tone="define", cls="d", label="① 题目两个动作", body='<span class="mk-copy">概括</span>主要表现 ＋ <span class="mk-copy">就如何整治提出建议</span> → <b>两段，你都写了 ✓</b>'),
        dict(tone="problem", cls="p", label="② 但两段一样长", body='表现 <b>190 字</b>（49.4%）／建议 <b>195 字</b>（50.6%）→ <b>配比错了</b>'),
        dict(tone="action", cls="a", label="③ 正确的配比", body='表现 <b>约 130 字</b>（1/3）／建议 <b>约 260 字</b>（2/3）→ 25 分里 15 分在建议上'),
        dict(tone="conclusion", cls="c", label="④ 自检动作", body='<span class="mk-own">写完两段，数字数：建议段的字数应该是表现段的两倍</span>'),
    ],
    structure_note=('<b>练习 6 你把功夫花在了题目没问的地方；练习 7 你写对了地方，但配比反了。</b><br>'
                    '这是同一件事的两个层次 —— 先解决「写不写」，再解决「写多少」。审题那关你已经过了。'),
    gaps=[
        dict(item='<b>推动数据互联互通、避免重复填报</b>', src='第 3 段：数据不互通，同一份材料要反复填、重复报', how='<b>问题与对策必须一一咬合</b> —— 表现里写了「数据不互通」，建议里就得有回响', value='约 2 分'),
        dict(item='<b>精简合并工作群</b>', src='第 1 段：加入了 30 多个工作群', how='你把「政务App和工作群」<b>概括成「各类政务平台」</b>，「工作群」三个字被概括掉了', value='约 2 分'),
        dict(item='「掌上政务」的<b>引号</b>，以及「保留」≠「搭建」', src='第 4 段：<b>保留一个统一的"掌上政务"平台</b>', how='<b>带引号的提法原样抄</b>；材料说的是保留已有的，不是新建', value='表述分'),
        dict(item='「僵尸应用」<b>用「清理」而不是「低效闲置」</b>', src='第 3 段：成了<b>"僵尸应用"</b>', how='带引号的提法要连着<b>材料原词的动作</b>一起搬', value='表述分'),
    ],
    bad=[
        '表现段写成了 190 字，比升格版多出 60 字 —— <b>这 60 字正好是你漏掉的那两条建议</b>。表现是铺垫，不是主角。',
        '把「政务App和<b>工作群</b>」概括成「各类政务平台」，<b>采分词在概括的过程中蒸发了</b>。这是第 1 课「概括层级过高」的老毛病，换了个题型又冒出来。',
        '<b>建议段「抄」只有 20%</b>（练习 6 是 74%）。材料已经把动作句、对象句都写好了，你却在用自己的话重说一遍 —— 每重说一次，就多一次丢词的风险。',
        '「搭建统一规范的政务平台」—— 材料是<b>保留</b>现有平台，不是新建。「搭建」会把你自己推到与材料相反的方向。',
    ],
    takeaway_sub='这一道题只需要带走一件事。',
    takeaways=[
        '<b>写建议时，材料里的「动作词 + 对象词」原样抄进你的句子，不要概括。</b>'
        '你把「政务 App 和<b>工作群</b>」概括成「各类政务平台」，三个字一没，后面的「精简工作群」也就跟着没了；'
        '你把「保留一个统一的<b>"掌上政务"</b>平台」说成「搭建统一规范的政务平台」，引号提法又丢一个。'
        '<b>概括是给「问题」用的，不是给「对策」用的 —— 对策要的是精确，不是简洁。</b>'
    ],
    verdict=('<b>成绩：21 / 25。</b>表现 4 个点全部写全写准（10 分），建议 8 个点里 5 个完整、2 个不完整、1 个漏（11 分）。<br>'
             '<b>和练习 6 相比，审题的问题彻底解决了</b> —— 题目问两个动作，你就写了两块，一个字都没跑偏。这是这一课最重要的收获。<br>'
             '剩下的两个毛病都在建议段：<b>篇幅只给了 50%（该给 2/3）</b>，'
             '<b>而且材料原词被自己的概括吃掉了</b>。改掉这两点，这题能拿 24~25 分。'),
    compare_sub='25 分拆成 12 个采分点（表现 4 + 建议 8），逐项对照。注意两个「漏／残」的共同点：材料原词在概括中蒸发了。',
    ref_warn=REF_WARN,
    reference=[
        '整治"指尖上的形式主义"，要减负与增效并举、标本兼治。',
        '当前基层"指尖上的形式主义"主要表现为：一是政务App、微信公众号、工作群泛滥，干部打卡签到、上传照片耗时多，挤占下基层时间；二是只重留痕不重实效，走访拍照、开会录像、学习截屏积分，干部被"绑"在手机上；三是各部门自建平台、数据不互通，同一份材料反复填、重复报，部分App上线后长期不更新，成了"僵尸应用"。',
        '一是清理整合平台。由市委办牵头成立工作专班，对全市政务App和工作群全面摸排；关停整合功能重复的App，精简合并工作群，清理长期不更新的"僵尸应用"，保留一个统一的"掌上政务"平台，推动数据互联互通、避免重复填报。',
        '二是严控增量负担。除中央和省级明确要求外，一律不得新增面向基层的打卡、留痕事项，并将此项要求纳入年度督查内容，让干部有时间下基层。',
        '三是改进考核方式。考核评价要从"看痕迹"转向"看实绩"，多听群众评价、多看工作成效。',
        '四是畅通反映渠道。畅通基层反映渠道，让干部敢于对不合理的要求说"不"。',
    ],
    compare=[
        dict(point='平台泛滥、打卡占时间', ref='各类政务App、微信公众号、工作群大量涌现；每天光打卡、签到、上传照片就要花两个多小时', mine='政务线上平台泛滥…耗费大量时间打卡签到、上传素材，挤占一线工作时间', j='hit', note='第 1 段。两个事实都写到了，还补了「挤占一线工作时间」——这就是把材料读到心里去了'),
        dict(point='重留痕轻实效', ref='很多App只重留痕不重实效；干部被"绑"在手机上，下村入户的时间反而少了', mine='重留痕轻实效…依赖拍照、录视频、截屏积分…弱化工作实效', j='hit', note='第 2 段。材料原词基本全在，这一段写得漂亮'),
        dict(point='数据不互通、重复填报', ref='各部门各自建平台，数据不互通，同一份材料要反复填、重复报', mine='各部门自建平台、数据不互通，报表材料重复上报', j='hit', note='第 3 段前半。「自建平台」「数据不互通」都是原词'),
        dict(point='App 长期不更新成"僵尸应用"', ref='有的App上线后长期不更新，成了"僵尸应用"', mine='部分APP长期不更新，沦为"僵尸应用"', j='hit', note='第 3 段后半。<b>带引号的提法守住了</b> —— 练习 6 丢的就是这个引号，这次记住了'),
        dict(point='组建专班、明确牵头', ref='成立了由市委办牵头的工作专班', mine='组建专项工作专班', j='hit', note='第 4 段。<b>练习 6 漏掉的就是这一条，这次补上了</b> —— 上一题的批改你真的吸收了'),
        dict(point='全面摸排（含工作群）', ref='对全市政务App和工作群全面摸排', mine='全面梳理排查各类政务平台', j='part', note='摸排这个动作写到了，但把「政务App和<b>工作群</b>」概括成「各类政务平台」——<b>「工作群」三个字在概括中蒸发了</b>'),
        dict(point='关停整合功能重复的 App', ref='关停整合功能重复的App 47个', mine='整合关停功能重复、低效闲置的APP', j='hit', note='第 4 段。动作词和对象词都在，还主动加了「低效闲置」去覆盖僵尸应用'),
        dict(point='保留统一平台（"掌上政务"）', ref='保留一个统一的"掌上政务"平台', mine='搭建统一规范的政务平台', j='part', note='意思摸到了，但两处走样：<b>带引号的「掌上政务」丢了</b>；材料是「保留」现有平台，你写「搭建」——方向反了'),
        dict(point='推动数据互联互通', ref='（第 3 段反推）数据不互通，材料反复填重复报', mine='（没写）', j='miss', note='<b>表现段里写了「数据不互通」，建议段却没有回响</b>。问题和对策要一一咬合：你写问题不是为了写问题，是为了给对策铺路'),
        dict(point='严控新增打卡、留痕 + 纳入督查', ref='一律不得新增面向基层的打卡、留痕事项，并将此项要求纳入年度督查内容', mine='严控新增基层打卡、留痕事项，将减负工作纳入年度督查', j='hit', note='第 4 段。两个点压成一条，动作准确'),
        dict(point='考核转向实绩、多听群众评价', ref='考核评价要从"看痕迹"转向"看实绩"，多听群众评价、多看工作成效', mine='摒弃唯痕迹的考核模式，以工作实绩、群众评价作为核心考核标准', j='hit', note='第 5 段。整句换了说法，但「工作实绩」「群众评价」两个采分词都保住了'),
        dict(point='畅通渠道、敢说"不"', ref='畅通基层反映渠道，让干部敢于对不合理的要求说"不"', mine='畅通基层反馈渠道，保障基层干部话语权，允许基层抵制不合理工作要求', j='hit', note='第 5 段。「反映」写成「反馈」是一字之差，阅卷人仍认得出；「抵制不合理要求」是「敢于说不」的转述，意思到位'),
    ],
)

ALL = [P1, P2, P3, P5, P6, P7]


if __name__ == "__main__":
    raise SystemExit(main())
