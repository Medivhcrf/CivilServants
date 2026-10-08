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
        sents = "".join(f'<span class="s" id="{sid}">{txt}</span>' for sid, txt in p["sents"])
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

    chips = "".join(
        f"<span>{c}</span>" for c in
        [f"你的答案 {st_student['total']} 字", f"升格版 {st_upgrade['total']} 字"] + d["chips"]
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{d['title']} ｜ {d['sub']}</title>
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
    <h2><span class="num">2</span>升格版 · 三色解剖 + 材料溯源（{st_upgrade['total']} 字）</h2>
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
    <h2><span class="num">3</span>整体结构</h2>
    <p class="h2sub">{d['structure_sub']}</p>
    <div class="flow">
{structure_html}
    </div>
    <div class="warn" style="margin-top:18px">{d['structure_note']}</div>
  </section>

  <section class="card">
    <h2><span class="num">4</span>漏点清单</h2>
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
    <h2><span class="num">5</span>带走的一个动作</h2>
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
    kicker="申论 · 练习 1 批改",
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
    kicker="申论 · 练习 2 批改",
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
    kicker="申论 · 练习 3 批改",
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
]

PATTERNS = [
    dict(title="概括层级过高", body="把一整段压成一个短语，采分词全丢。<b>练习 1 只写了 37 / 200 字。</b>",
         fix="每条展开到 35–45 字，写完先数字数", status="已改正（练习 3）"),
    dict(title="漏段落后半截", body="只抓中心句，段落后半截的采分点全漏。<b>练习 3 漏了「培训偏理论」「农房抵押贷款受限」「村集体缺经营主体」。</b>",
         fix="标点切分法：按句号分号切句，一句一勾", status="待巩固"),
    dict(title="用生活经验替换材料原词", body="把「先服务、后收费」读成「先改造，再进行议价」。<b>练习 2 因此丢 1 分。</b>",
         fix="原词搬运，不许「翻译」；带引号的必抄", status="待巩固"),
    dict(title="动宾结构不完整", body="只写方式，丢了核心动作。<b>练习 2 丢了「引入专业物业企业」。</b>",
         fix="每条自检「动词 + 宾语」齐不齐", status="已改正"),
    dict(title="正反两层不对称", body="有反面总起就必须有正面总起。<b>练习 5 正面有、反面没有。</b>",
         fix="写完回头看两层总起是否对仗", status="新出现"),
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
<title>练习档案 ｜ 五次作答的完整解析</title>
<style>{CSS}
.rec{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
</style>
</head>
<body class="plain-mk">

<header>
  <div class="in">
    <span class="kicker">申论 · 练习档案</span>
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
        </tbody>
      </table>
    </div>
    <div class="warn">
      <b>两个规律：</b><br>
      ① <b>归纳概括题，「抄」的占比一路从 10.8% 涨到 66.2%</b> —— 你逐步学会了从材料里割肉，而不是自己概括大意。<br>
      ② <b>综合分析题的起点只有 30%</b> —— 因为这类题要自己搭"是什么—为什么—怎么办"，骨架占比高。
      但升格版是 53.6%，说明<b>肉还是得从材料里割</b>，只是骨架要多写几句。
    </div>
  </section>

  <section class="card">
    <h2><span class="num">3</span>逐题三色解剖</h2>
    <p class="h2sub">点进去看每一份答案的逐句成分、升格版、悬停溯源与漏点清单。</p>
    <div class="rec">
{cards_html}
    </div>
  </section>

  <section class="card">
    <h2><span class="num">4</span>反复出现的失分模式</h2>
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


if __name__ == "__main__":
    raise SystemExit(main())
