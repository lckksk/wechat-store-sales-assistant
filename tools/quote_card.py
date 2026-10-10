# -*- coding: utf-8 -*-
"""
金句卡统一渲染模板（鲸默读书）
用法：
  python quote_card.py --quote "金句内容" --source "出处" --out 输出.png [--theme cream] [--tag "底部小字"]
尺寸 1242x1660（3:4），适配公众号小绿书。
主题：cream(治愈/认知默认) / sage(清新) / night(深夜独白) / ink(国学·深色)
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

W, H = 1242, 1660
MARGIN = 130
F_QUOTE = "C:/Windows/Fonts/STKAITI.TTF"   # 华文楷体：书卷气
F_SMALL = "C:/Windows/Fonts/msyh.ttc"      # 微软雅黑：辅助信息

THEMES = {
    "cream": {"bg": (247, 243, 234), "ink": (62, 56, 48), "accent": (172, 142, 102), "soft": (155, 145, 128)},
    "sage":  {"bg": (236, 241, 234), "ink": (54, 68, 57),  "accent": (112, 138, 106), "soft": (132, 142, 128)},
    "night": {"bg": (30, 34, 44),    "ink": (226, 229, 236), "accent": (150, 168, 205), "soft": (125, 130, 145)},
    "ink":   {"bg": (243, 238, 226), "ink": (45, 42, 38),  "accent": (158, 62, 48),  "soft": (150, 142, 126)},
}

NO_LINE_START = "。，；！？、」』））：,.;!?)]}"  # 禁止出现在行首的标点

def wrap(draw, text, font, max_w):
    """先按标点切成短句，短句尽量整行排；超长句再按字断，行首不留标点"""
    lines = []
    for para in text.split("\n"):
        # 1) 按标点切分成自然短句
        segs, cur = [], ""
        for ch in para:
            cur += ch
            if ch in "，。；！？、：,.;:!?":
                segs.append(cur)
                cur = ""
        if cur:
            segs.append(cur)
        # 2) 短句装箱：放不下就断行
        line = ""
        for seg in segs:
            if not line:
                line = seg
            elif d.textlength(line + seg, font=font) <= max_w:
                line += seg
            else:
                lines.append(line)
                line = seg
            # 短句本身超宽 → 按字断
            while d.textlength(line, font=font) > max_w * 1.02:
                cut = ""
                for ch in line:
                    if d.textlength(cut + ch, font=font) <= max_w:
                        cut += ch
                    else:
                        break
                rest = line[len(cut):]
                # 行首标点回退
                while rest and rest[0] in NO_LINE_START and cut:
                    cut += rest[0]
                    rest = rest[1:]
                lines.append(cut)
                line = rest
        if line:
            lines.append(line)
    return lines

def spaced(draw, cx, y, text, font, fill, gap=14):
    """以 cx 为水平中心、y 为顶边，绘制带字距的文字"""
    widths = [draw.textlength(c, font=font) for c in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = cx - total / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=font, fill=fill)
        x += w + gap

def render(quote, source, out, theme="cream", tag="每天读一点 · 把书读薄"):
    T = THEMES[theme]
    img = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(img)

    # ── 双线边框 ──
    d.rectangle([44, 44, W - 44, H - 44], outline=T["accent"], width=2)
    d.rectangle([58, 58, W - 58, H - 58], outline=T["accent"], width=1)

    cx = W // 2

    # ── 顶部品牌 ──
    f_brand = ImageFont.truetype(F_SMALL, 34)
    spaced(d, cx, 130, "鲸默读书", f_brand, T["ink"], gap=16)
    d.line([cx - 60, 200, cx + 60, 200], fill=T["accent"], width=2)

    # ── 正文：先切自然短句，再选能容纳最长短句的最大字号 ──
    quote_max_h = 760
    y_start = 440

    def split_segs(text):
        out, cur = [], ""
        for ch in text:
            cur += ch
            if ch in "，。；！？、：,.;:!?":
                out.append(cur)
                cur = ""
        if cur:
            out.append(cur)
        return out

    all_segs = []
    for para in quote.split("\n"):
        all_segs.append(split_segs(para))

    for size in (92, 84, 76, 70, 64, 58, 52):
        f_q = ImageFont.truetype(F_QUOTE, size)
        longest = max(d.textlength(s, font=f_q)
                      for segs in all_segs for s in segs)
        if longest <= (W - 2 * MARGIN) * 1.02:
            break
    line_h = int(size * 1.62)

    # 装箱：短句同行合并，放不下另起一行
    lines = []
    for segs in all_segs:
        line = ""
        for s in segs:
            if not line:
                line = s
            elif d.textlength(line + s, font=f_q) <= (W - 2 * MARGIN) * 1.02:
                line += s
            else:
                lines.append(line)
                line = s
        if line:
            lines.append(line)

    total_h = len(lines) * line_h
    if total_h > quote_max_h:  # 兜底：行数太多再缩一号
        for size2 in (52, 48, 44):
            f_q = ImageFont.truetype(F_QUOTE, size2)
            line_h = int(size2 * 1.62)
            lines = wrap(d, quote, f_q, W - 2 * MARGIN)
            total_h = len(lines) * line_h
            if total_h <= quote_max_h:
                break
    y = y_start + (quote_max_h - total_h) / 2

    # ── 开头引号（贴正文首行上方，与右下 closing 对角呼应） ──
    f_mark = ImageFont.truetype(F_QUOTE, 130)
    mark1 = "\u201C"
    d.text((MARGIN - 10, y - 105), mark1, font=f_mark, fill=T["accent"])

    for ln in lines:
        d.text((cx - d.textlength(ln, font=f_q) / 2, y), ln, font=f_q, fill=T["ink"])
        y += line_h

    # ── 收尾引号（与左上 opening 对称，右下角） ──
    f_mark2 = ImageFont.truetype(F_QUOTE, 130)
    mark2 = "\u201D"
    d.text((W - MARGIN - d.textlength(mark2, font=f_mark2), y - 40), mark2, font=f_mark2, fill=T["accent"])
    y += 110

    # ── 出处 ──
    if source:
        f_src = ImageFont.truetype(F_SMALL, 34)
        d.text((cx - d.textlength(source, font=f_src) / 2, y), source, font=f_src, fill=T["soft"])

    # ── 底部 ──
    # 装饰菱形
    dx, dy = cx, H - 190
    d.polygon([(dx, dy - 9), (dx + 9, dy), (dx, dy + 9), (dx - 9, dy)], fill=T["accent"])
    if tag:
        f_tag = ImageFont.truetype(F_SMALL, 30)
        d.text((cx - d.textlength(tag, font=f_tag) / 2, H - 160), tag, font=f_tag, fill=T["soft"])

    img.save(out, quality=95)
    print("saved:", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quote", required=True)
    ap.add_argument("--source", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--theme", default="cream", choices=list(THEMES))
    ap.add_argument("--tag", default="每天读一点 · 把书读薄")
    a = ap.parse_args()
    render(a.quote, a.source, a.out, a.theme, a.tag)
