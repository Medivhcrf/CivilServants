# -*- coding: utf-8 -*-
"""练习 20 · 答案对照（你的答案 vs 标准答案）→ docx + pdf，彩色标记。"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import make_handout as H
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OK = ("1A7F37", "D7F5DD")
PART = ("7A4D00", "FFF1C9")
MISS = ("B3121F", "FFDBDB")


def shade(p_or_run, fill):
    el = p_or_run._p if hasattr(p_or_run, "_p") else p_or_run._element
    pr = el.get_or_add_pPr() if hasattr(el, "get_or_add_pPr") else el.get_or_add_rPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def add_run(p, text, kind="plain", size=10, bold=False):
    r = p.add_run(text)
    r.font.name = H.FONT
    r.font.size = Pt(size)
    r.bold = bold
    if kind in ("ok", "part", "miss"):
        color, fill = {"ok": OK, "part": PART, "miss": MISS}[kind]
        r.font.color.rgb = RGBColor.from_string(color)
        shade(r, fill)
        if kind == "miss":
            r.font.strike = True
        if kind == "ok":
            r.bold = True
    elif kind == "add":
        r.font.color.rgb = RGBColor.from_string("1A7F37")
        r.underline = True
    elif kind == "muted":
        r.font.color.rgb = RGBColor.from_string("57606A")
    elif kind == "white":
        r.font.color.rgb = RGBColor.from_string("FFFFFF")
        r.bold = True
    return r


def para(doc, segs, size=9.8, after=4, fill=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.42
    if fill:
        shade(p, fill)
    for seg in segs:
        if isinstance(seg, str):
            add_run(p, seg, size=size)
        else:
            add_run(p, seg[0], kind=seg[1], size=size)
    return p


def band(doc, text, fill="1F3A5F"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    shade(p, fill)
    add_run(p, "  " + text, "white", size=13, bold=True)


def table(doc, headers, rows, widths, size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "D0D7DE")
        borders.append(e)
    tblPr.append(borders)
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        H.cell_width(cell, widths[i])
        add_run(cell.paragraphs[0], h, size=size, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            H.cell_width(cells[i], widths[i])
            if isinstance(val, tuple):
                add_run(cells[i].paragraphs[0], val[0], kind=val[1], size=size, bold=True)
            else:
                add_run(cells[i].paragraphs[0], val, size=size)
    return t


def main(out_dir=pathlib.Path(r"E:\Harness")):
    doc = H.new_doc("申论 · 答案对照 · 练习 20")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    add_run(p, "练习 20 · 答案对照", size=20, bold=True)
    para(doc, [("第 2 次限时整卷 · 基层减负 · 2026-11-16 ｜ 你的答案 vs 标准答案 ｜ 总分 ", "muted"), "63 / 100"], size=10, after=8)

    para(doc, [("颜色怎么读：  你写到了", "ok"), "＝绿底（命中采分点）；  ",
               ("写了一半", "part"), "＝黄底（有定性没证据／表述不到位）；  ",
               ("缺", "miss"), "＝红底删除线（完全没有）。标准答案里的绿色下划线文字＝补给你的部分。"],
         size=9.5, fill="F2F4F6", after=8)

    table(doc, ["题目", "分值", "得分", "一句话判定"], [
        ("第 1 题 概括", "15", ("11", "part"), "四条全带数字（首次），缺总括句"),
        ("第 2 题 评析", "20", ("11", "part"), "判断句有了，只写一边，160/300 字"),
        ("第 3 题 倡议书", "20", ("14", "ok"), "格式五件齐，任务写成了上级的动作"),
        ("第 4 题 提纲", "45", ("27", "miss"), "论点可判断，三个分论点重复＋维度不一"),
    ], [5.2, 2.0, 2.0, 8.8])

    # Q1
    band(doc, "第 1 题 · 概括（15 分 · 250 字）")
    para(doc, ["根据给定资料，概括 G 县基层干部负担重的具体表现。（250 字以内，15 分）"], fill="F2F4F6")
    para(doc, [("你的答案（约 250 字）", "muted")], size=9, after=2)
    para(doc, [("（缺总括句）", "miss"), "1、报表总量大。",
               ("G 县一个乡镇去年收上级文件 1470 份；各种报表 86 种。", "ok"),
               ("乡镇干部说一半的时间在填表，剩下的一半在准备填表的材料。", "ok"),
               "2、手机上工作 App 多，",
               ("要求每天打卡、拍照上传、点赞、转发，有的群要求收到回复，晚上十点还在回收到。", "ok"),
               "3、考核名目多，", ("一项工作要准备台账、照片、会议记录、签到表。", "ok"),
               "4、工作人员少，", ("以这个乡镇为例，编制 78 人，在岗 51 人，借调走 9 人，一名干部对接多个上级部门。", "ok")],
         fill="FBFCFD")
    para(doc, [("标准答案（248 字）", "add")], size=9, after=2)
    para(doc, [("G 县基层干部负担重，集中在文件报表、指尖任务、考核留痕、人手不足四块。", "add"),
               "一是文件报表多。", ("年均收文 1470 份、日均 4 份", "add"),
               "，各类报表 86 种、其中 31 种内容重复，干部「一半时间在填表」。二是", ("指尖", "add"),
               "负担重。手机装 11 个 App，每日打卡、拍照、上传、点赞、转发，微信群要求「收到回复」，深夜仍在应答。三是考核留痕重。一项工作要备台账、照片、会议记录、签到表",
               ("四类材料，检查提前一周通知、连夜做档案盒", "add"),
               "。四是力量不足。编制 78 人实在岗 51 人、被借调 9 人，一名干部对接 5 个上级部门。"],
         fill="F2FBF4")
    table(doc, ["采分要素", "你的答案", "判定"], [
        ("总括句（点出四类）", "没有，直接从「1、」开始", ("✘ 缺 · 扣 1", "miss")),
        ("文件＋报表", "1470 份、86 种都写了；漏「31 种重复」", ("✔ 基本到位", "ok")),
        ("指尖负担", "打卡拍照上传点赞、群里收到回复都写了", ("✔ 到位", "ok")),
        ("考核留痕", "四类材料全写；漏「提前一周通知」「连夜做档案盒」", ("◐ 证据少半句", "part")),
        ("人手不足", "78、51、9 写了；「多个部门」没写「5 个」", ("✔ 到位", "ok")),
        ("定性用词", "「报表总量大」只覆盖报表，没覆盖文件", ("◐ 偏窄", "part")),
    ], [4.4, 7.2, 5.4])
    para(doc, ["改法：只在前面加一句总括，其余一字不用动——「G 县负担重，集中在文件报表、指尖任务、考核留痕、人手不足四块。」"], after=6)

    # Q2
    band(doc, "第 2 题 · 评析（20 分 · 300 字）")
    para(doc, ["给定资料三中，有干部说「干得好不如留痕留得好」。请结合给定资料，对这一说法进行评析。（300 字以内，20 分）"], fill="F2F4F6")
    para(doc, [("你的答案（约 160 字）", "muted")], size=9, after=2)
    para(doc, [("干得好不如留痕留得好，本质上就是应付上级。", "ok"),
               "干部一半的时间在填表，剩下的一半在准备填表的材料；手机上的打卡拍照上传点赞转发动作本质上也是在应付上级，",
               ("没有真正的对接群众急需的问题", "part"), "。",
               ("这与减负不是减责任、是把基层从应付上级里解放出来去服务群众的根本原则相违背。", "ok"),
               ("（缺「这话对在哪」，也缺「怎么办」）", "miss")], fill="FBFCFD")
    para(doc, [("标准答案（288 字）", "add")], size=9, after=2)
    para(doc, ["这一说法说对了一半，但把手段当成了目的。", ("对的一面是：", "add"),
               "留痕本身不是错。", ("上级要评估落实、要留证据，台账、照片、会议记录是必要的工作成本；痕迹也是追责依据，不能一概否定。", "add"),
               ("错的一面是：", "add"), "当留痕成为考核的", ("唯一", "add"),
               "依据，就会出现「为留痕而留痕」——",
               ("提前一周通知、连夜做档案盒，甚至减负本身也要报「减负台账」。这时留痕不是工作的副产品，而成了工作的替代品。", "add"),
               ("所以争的不是要不要留痕，而是拿什么评价干部：让考核回到结果，看群众诉求解决率和重点任务完成率。", "add")],
         fill="F2FBF4")
    table(doc, ["结构块", "你的答案", "判定"], [
        ("第一句判断", "「本质上就是应付上级」——成立但一边倒", ("◐ 3 / 4", "part")),
        ("对在哪（合理性）", "完全没有", ("✘ 0 / 4 ← 最大的洞", "miss")),
        ("错在哪（片面性）", "点了「应付上级」「没对接群众问题」", ("✔ 3 / 4", "ok")),
        ("危害／后果", "只说「违背原则」，没有后果", ("◐ 2 / 4", "part")),
        ("结论：怎么办", "没有独立结论句", ("✘ 1 / 4", "miss")),
        ("字数", "约 160 / 300", ("✘ 少写 140 字", "miss")),
    ], [4.4, 7.2, 5.4])
    para(doc, ["改法：评析固定四块——判断（一半对）→ 对在哪 → 错在哪 → 怎么办。你缺的两块正好 140 字。"], after=6)

    # Q3
    band(doc, "第 3 题 · 倡议书（20 分 · 400 字）")
    para(doc, ["假如你是 G 县减负办的工作人员，请以县减负办名义，向全县基层干部写一封「减负不减责」的倡议书。（400 字以内，20 分）"], fill="F2F4F6")
    para(doc, [("你的答案（约 300 字）", "muted")], size=9, after=2)
    para(doc, [("「减负不减责」倡议书 / 全县干部同志：/ 为积极响应中央出台的《整治形式主义为基层减负若干规定》，我们发出如下倡议：", "ok")], fill="FBFCFD")
    para(doc, [("（下面四条，把「上级该做的」写成了「干部要做的」）", "miss"), " 一、",
               ("压缩报表数量，同类事项做到一次采集、多方复用。", "part"), " 二、",
               ("督查检查合并成一次进门、多项联查。", "part"), " 三、",
               ("清退僵尸群，非紧急事项不在下班后发通知。", "part"), " 四、",
               ("考核只看群众诉求解决率、重点任务完成率。", "part")], fill="FBFCFD")
    para(doc, ["我们的干部要从应付上级里解放出来，去服务群众。减负不减责，要落实真正的服务群众。",
               ("（缺号召句）", "miss"), " 倡议单位：G 县减负办 / 2026 年 11 月 17 日"], fill="FBFCFD")
    para(doc, [("标准答案（386 字）", "add")], size=9, after=2)
    para(doc, [("关于「减负不减责、轻装为群众」的倡议书 / 全县基层干部同志们：/ 为落实中央《整治形式主义为基层减负若干规定》，把大家从文山会海、指尖任务中解放出来，腾出手来解决群众急难愁盼，我们发出如下倡议：", "add")], fill="F2FBF4")
    para(doc, ["一、少做「纸面功夫」。检查要留痕的，只备一套基础材料，不再为迎检连夜赶制档案盒；能用实绩说明的，不额外补台账、补照片。二、不刷「指尖分数」。除上级明确要求的，不强制下载、打卡、点赞、转发；工作群只留必要的，非紧急事项不在下班后发通知，不要求「收到回复」。三、多跑「群众门口」。把省下来的时间用到走访、办事上；遇到层层加码、重复报表，向县减负办反映，我们统一协调、坚决纠正。"], fill="F2FBF4")
    para(doc, ["同志们，减负不是减责任，而是把责任落到该落的地方。让我们轻装上阵，把每一分钟都用在群众身上。 G 县减负办 / 2026 年 11 月 17 日"], fill="F2FBF4")
    table(doc, ["要素", "你的答案", "判定"], [
        ("标题", "「减负不减责」倡议书", ("✔ 1 / 1", "ok")),
        ("主送", "全县干部同志（应为全县基层干部同志们）", ("◐ 0.5 / 1", "part")),
        ("依据句", "有，引了中央《规定》", ("✔ 1 / 1", "ok")),
        ("三条以上任务", "四条，且都来自材料五", ("✔ 5 / 6", "ok")),
        ("对象匹配（写给干部→动作落在干部身上）", "四条写的是上级动作：压缩报表、合并督查、清退群、改考核", ("✘ 2 / 6 ← 本题最大失分", "miss")),
        ("号召句", "有，但偏口号", ("◐ 1 / 2", "part")),
        ("落款＋日期", "倡议单位＋日期，齐", ("✔ 1 / 1", "ok")),
        ("字数", "约 300 / 400（偏短但没超）", ("◐ 1 / 1", "part")),
    ], [4.6, 7.0, 5.4])
    para(doc, ["改法（只改主体，不动格式）：四条改成干部自己做的事——① 少做纸面功夫（只备一套基础材料）② 不刷指尖分数（不强制打卡点赞）③ 多跑群众门口（时间用在走访办事）＋遇加码向减负办反映。标题加「关于」，主送加「基层」。"], after=6)

    # Q4
    band(doc, "第 4 题 · 议论文提纲（45 分）")
    para(doc, ["以「减负与增效」为主题，自拟标题。今天只写：标题＋中心论点＋三个分论点＋开头段（150 字）。"], fill="F2F4F6")
    para(doc, [("你的答案", "muted")], size=9, after=2)
    para(doc, ["标题：", ("从应付上级到服务群众（2 / 5）", "part")], fill="FBFCFD")
    para(doc, ["中心论点：", ("减负是减去应付上级的时间，增效是增加解决群众问题的时间与效果。（8 / 10）", "ok")], fill="FBFCFD")
    para(doc, ["分论点 1：", ("干部人数少负担重，如果再去应付上级督查的任务，就没有时间服务群众。（5 / 10）", "part")], fill="FBFCFD")
    para(doc, ["分论点 2：", ("不能让干部服务群众的决心在繁杂的上级任务中磨灭。（4 / 10，与第 1 条重复）", "miss")], fill="FBFCFD")
    para(doc, ["分论点 3：", ("形式主义不可取，上级部门更要做好工作，让基层干部干得顺心安心。（4 / 10，主体跳到上级）", "miss")], fill="FBFCFD")
    para(doc, ["开头段：", ("要积极响应《整治形式主义为基层减负若干规定》，我们的目的是要更多的服务群众，我们要看到基层干部服务群众的决心，也要做到让他们减负的承诺。（约 120 字，4 / 10）", "part")], fill="FBFCFD")
    para(doc, [("标准答案", "add")], size=9, after=2)
    para(doc, ["标题：", ("把干部的分钟还给群众", "add"), "（11 字，有动作、有对比）"], fill="F2FBF4")
    para(doc, ["中心论点：", ("减负不是减少工作量，而是把干部被形式主义占用的时间还给解决群众问题；减的是虚功，增的是实效。", "add")], fill="F2FBF4")
    para(doc, ["分论点一（减文件）：", ("压掉重复报表和层层发文，才有时间走出办公室。", "add")], fill="F2FBF4")
    para(doc, ["分论点二（减考核）：", ("把评价从「留痕够不够」改到「问题解没解」，才敢把功夫下在实处。", "add")], fill="F2FBF4")
    para(doc, ["分论点三（减指尖）：", ("清理重复 App 与打卡转发，才不至于把手机变成第二个办公室。", "add")], fill="F2FBF4")
    para(doc, ["开头段（148 字）：", ("一个乡镇一年收文 1470 份、手机装着 11 个工作 App、一项工作要备四类材料——这些数字背后，是干部被切碎的时间。减负之所以难，不是文件不够多，而是评价的尺子还停在「留痕」上。减负不是减责任，是把时间还给群众；减的是虚功，增的是实效。要让基层轻装上阵，得从文件、考核、指尖三处一起减。", "add")], fill="F2FBF4")
    table(doc, ["要素", "你的答案", "判定"], [
        ("标题 8–14 字带动作", "11 字，有对比但无动作词", ("◐ 2 / 5", "part")),
        ("中心论点可判断", "减去应付的时间／增加解决问题的时间——可判断，很好", ("✔ 8 / 10", "ok")),
        ("三个分论点同一维度", "1、2 都说没时间服务群众（重复）；3 主体变成上级部门", ("✘ 13 / 30 ← 本题最大失分", "miss")),
        ("开头段 150 字四句", "120 字，口号式", ("✘ 4 / 10", "miss")),
    ], [4.4, 7.2, 5.4])
    para(doc, ["改法：分论点改成同一组维度——减文件／减考核／减指尖；开头段四句＝现象（1470 份）→ 本质（尺子停在留痕上）→ 观点（减负不是减责任）→ 引出（从三处一起减）。"], after=6)

    band(doc, "四处失分，一页看完")
    table(doc, ["失分", "题", "扣分", "一句话改法"], [
        ("没有总括句", "第 1 题", "-1", "开头加「负担重，集中在文件报表、指尖任务、考核留痕、人手不足四块」"),
        ("评析只写一边、字数不足", "第 2 题", "-9", "补「对在哪」（留痕是必要成本）与「怎么办」（考核看结果）"),
        ("对象错位", "第 3 题", "-6", "四条改成干部自己做的事，标题加「关于」，主送加「基层」"),
        ("分论点重复、维度不一", "第 4 题", "-18", "先定一组维度（文件／考核／指尖），再写三条"),
    ], [4.2, 1.8, 1.6, 9.4])

    para(doc, [("一句话带走：", "muted"), ("写完抬头问一句「这道题是让谁做什么」", "miss"),
               "——第 3 题栽的就是这一问，主体错了，格式再齐也拿不到内容分。"], size=10, fill="F2F4F6")
    para(doc, ["练习 20 · 2026-11-16 ｜ 第 1 次整卷 24 分 → 第 2 次 63 分（材料更难、文种更全）｜ 生成于 2026-11-17"], size=8.5)

    docx_path = out_dir / "练习20-答案对照.docx"
    doc.save(docx_path)
    pdf_path = out_dir / "练习20-答案对照.pdf"
    ok = H.to_pdf(docx_path, pdf_path)
    print("docx ->", docx_path)
    print("pdf  ->", pdf_path if ok else "FAILED")


if __name__ == "__main__":
    main()
