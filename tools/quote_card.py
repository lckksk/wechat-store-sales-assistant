# -*- coding: utf-8 -*-
"""
金句卡统一渲染模板（鲸默阅读）v2
用法：
  python quote_card.py --quote "金句内容" --source "出处" --out 输出.png [--theme warm] [--tag "底部小字"]
尺寸 1242x1660（3:4），适配公众号小绿书。
主题：
  warm  = 温馨治愈版（渐变底+光斑+茶杯插画）——图书治愈/心理线默认
  cream = 素雅米白（旧版）
  sage  = 清新豆绿（旧版）
  night = 深夜独白（旧版）
  ink   = 国学·深色（旧版）
"""
import argparse
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1242, 1660
MARGIN = 130
F_QUOTE = "C:/Windows/Fonts/STKAITI.TTF"   # 华文楷体：书卷气
F_SMALL = "C:/Windows/Fonts/msyh.ttc"      # 微软雅黑：辅助信息

THEMES = {
    "warm":  {"bg_top": (253, 248, 236), "bg_bottom": (248, 231, 206),
              "ink": (92, 72, 54), "accent": (203, 122, 70), "soft": (168, 142, 114)},
    "cream": {"bg": (247, 243, 234), "ink": (62, 56, 48), "accent": (172, 142, 102), "soft": (155, 145, 128)},
    "sage":  {"bg": (236, 241, 234), "ink": (54, 68, 57),  "accent": (112, 138, 106), "soft": (132, 142, 128)},
    "night": {"bg": (30, 34, 44),    "ink": (226, 229, 236), "accent": (150, 168, 205), "soft": (125, 130, 145)},
    "ink":   {"bg": (243, 238, 226), "ink": (45, 42, 38),  "accent": (158, 62, 48),  "soft": (150, 142, 126)},
}

NO_LINE_START = "。，；！？、」』））：,.;!?)]}"  # 禁止出现在行首的标点


def blend(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def wrap(draw, text, font, max_w):
    """先按标点切成短句，短句尽量整行排；超长句再按字断，行首不留标点"""
    lines = []
    for para in text.split("\n"):
        segs, cur = [], ""
        for ch in para:
            cur += ch
            if ch in "，。；！？、：,.;:!?":
                segs.append(cur)
                cur = ""
        if cur:
            segs.append(cur)
        line = ""
        for seg in segs:
            if not line:
                line = seg
            elif d.textlength(line + seg, font=font) <= max_w:
                line += seg
            else:
                lines.append(line)
                line = seg
            while d.textlength(line, font=font) > max_w * 1.02:
                cut = ""
                for ch in line:
                    if d.textlength(cut + ch, font=font) <= max_w:
                        cut += ch
                    else:
                        break
                rest = line[len(cut):]
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


def layout_quote(d, quote, max_w, quote_max_h=760):
    """短句装箱 + 字号自适应，返回 (font, lines, line_h)"""
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

    all_segs = [split_segs(p) for p in quote.split("\n")]

    size = 52
    for s in (92, 84, 76, 70, 64, 58, 52):
        f_q = ImageFont.truetype(F_QUOTE, s)
        longest = max(d.textlength(x, font=f_q) for segs in all_segs for x in segs)
        if longest <= max_w * 1.02:
            size = s
            break
    f_q = ImageFont.truetype(F_QUOTE, size)
    line_h = int(size * 1.62)

    lines = []
    for segs in all_segs:
        line = ""
        for sg in segs:
            if not line:
                line = sg
            elif d.textlength(line + sg, font=f_q) <= max_w * 1.02:
                line += sg
            else:
                lines.append(line)
                line = sg
        if line:
            lines.append(line)

    total_h = len(lines) * line_h
    if total_h > quote_max_h:
        for s2 in (52, 48, 44):
            f_q = ImageFont.truetype(F_QUOTE, s2)
            line_h = int(s2 * 1.62)
            lines = wrap(d, quote, f_q, max_w)
            total_h = len(lines) * line_h
            if total_h <= quote_max_h:
                break
    return f_q, lines, line_h


def draw_text_block(d, img, quote, source, T, y_start=440, quote_max_h=760):
    """正文+成对引号+出处，返回出处块底部 y"""
    cx = W // 2
    max_w = W - 2 * MARGIN
    f_q, lines, line_h = layout_quote(d, quote, max_w, quote_max_h)
    total_h = len(lines) * line_h
    y = y_start + (quote_max_h - total_h) / 2

    # 成对引号：开引号贴首行上方，收引号挂末行右下
    accent_soft = blend(T["accent"], T.get("bg", T.get("bg_top")), 0.35)
    f_mark = ImageFont.truetype(F_QUOTE, 130)
    d.text((MARGIN - 10, y - 105), "\u201C", font=f_mark, fill=accent_soft)
    for ln in lines:
        d.text((cx - d.textlength(ln, font=f_q) / 2, y), ln, font=f_q, fill=T["ink"])
        y += line_h
    f_mark2 = ImageFont.truetype(F_QUOTE, 130)
    d.text((W - MARGIN - d.textlength("\u201D", font=f_mark2), y - 40),
           "\u201D", font=f_mark2, fill=accent_soft)
    y += 110

    if source:
        f_src = ImageFont.truetype(F_SMALL, 34)
        d.text((cx - d.textlength(source, font=f_src) / 2, y), source,
               font=f_src, fill=T["soft"])
        y += 60
    return y


# ───────────────────────── warm：温馨治愈版 ─────────────────────────

def cozy_canvas(T):
    """渐变底 + 暖光斑"""
    grad = Image.new("RGB", (1, H))
    for yy in range(H):
        t = yy / (H - 1)
        grad.putpixel((0, yy), blend(T["bg_top"], T["bg_bottom"], t))
    img = grad.resize((W, H)).convert("RGBA")

    bokeh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bokeh)
    blobs = [
        (int(W * 0.14), int(H * 0.10), 150, (247, 208, 160), 120),
        (int(W * 0.90), int(H * 0.20), 110, (244, 194, 148), 100),
        (int(W * 0.86), int(H * 0.72), 150, (247, 206, 158), 110),
        (int(W * 0.10), int(H * 0.64), 100, (246, 212, 170), 95),
        (int(W * 0.52), int(H * 0.955), 120, (243, 196, 150), 85),
        (int(W * 0.33), int(H * 0.045), 70, (250, 224, 186), 90),
    ]
    for bx, by, br, color, alpha in blobs:
        bd.ellipse([bx - br, by - br, bx + br, by + br], fill=color + (alpha,))
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(65))
    img = Image.alpha_composite(img, bokeh)

    # 细碎暖点（星光感）
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    import random
    rnd = random.Random(7)
    for _ in range(26):
        dx, dy = rnd.randint(90, W - 90), rnd.randint(90, H - 90)
        dr = rnd.randint(3, 7)
        dd.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=(255, 236, 205, rnd.randint(120, 200)))
    dots = dots.filter(ImageFilter.GaussianBlur(1.2))
    img = Image.alpha_composite(img, dots)
    return img.convert("RGB")


def draw_rounded_frame(d, T):
    """单层圆角细框，替代旧版双直线框"""
    inset, r = 52, 44
    d.rounded_rectangle([inset, inset, W - inset, H - inset], radius=r,
                        outline=blend(T["accent"], T["bg_top"], 0.45), width=3)


def draw_wavy(d, cx, y, half_w, T, amp=6, seg=14, width=3):
    """手绘感波浪线"""
    pts = []
    n = int(half_w * 2 / seg)
    for i in range(n + 1):
        xx = cx - half_w + i * seg
        pts.append((xx, y + amp * math.sin(i * 1.7)))
    d.line(pts, fill=T["accent"], width=width, joint="curve")


def draw_cup(d, cx, top, T):
    """冒热气的茶杯简笔画（杯+托+两缕蒸汽）"""
    accent = T["accent"]
    cup_soft = blend(accent, T["bg_top"], 0.25)
    # 杯托
    d.ellipse([cx - 88, top + 74, cx + 88, top + 100], outline=cup_soft, width=5)
    # 杯身
    d.rounded_rectangle([cx - 58, top + 4, cx + 58, top + 84], radius=26, fill=accent)
    # 杯口
    d.ellipse([cx - 58, top - 10, cx + 58, top + 18], fill=blend(T["bg_top"], (255, 255, 255), 0.5),
              outline=accent, width=5)
    # 杯柄
    d.arc([cx + 48, top + 14, cx + 100, top + 62], start=-75, end=95, fill=accent, width=7)
    # 蒸汽（两缕弯曲细线，向上渐淡）
    steam = blend(T["soft"], T["bg_top"], 0.55)
    for phase, x_off in ((0.0, -18), (1.6, 16)):
        pts = []
        for i in range(9):
            t = i / 8
            pts.append((cx + x_off + 7 * math.sin(t * 5.5 + phase), top - 26 - t * 66))
        d.line(pts, fill=steam, width=4, joint="curve")


def render_warm(quote, source, out, tag="每天读一点 · 把书读薄"):
    T = THEMES["warm"]
    img = cozy_canvas(T)
    d = ImageDraw.Draw(img)
    draw_rounded_frame(d, T)

    cx = W // 2
    # 顶部品牌 + 波浪线
    f_brand = ImageFont.truetype(F_SMALL, 34)
    spaced(d, cx, 128, "鲸默阅读", f_brand, T["ink"], gap=16)
    draw_wavy(d, cx, 208, 78, T)

    # 正文 + 出处
    y_end = draw_text_block(d, img, quote, source, T)

    # 底部：茶杯插画 + 小字
    cup_top = max(y_end + 40, H - 420)
    draw_cup(d, cx, cup_top, T)
    if tag:
        f_tag = ImageFont.truetype(F_SMALL, 30)
        d.text((cx - d.textlength(tag, font=f_tag) / 2, H - 158), tag,
               font=f_tag, fill=T["soft"])

    img.save(out, quality=95)
    print("saved:", out)


# ───────────────────────── 旧版（素色+双线框） ─────────────────────────

def render(quote, source, out, theme="cream", tag="每天读一点 · 把书读薄"):
    T = THEMES[theme]
    img = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([44, 44, W - 44, H - 44], outline=T["accent"], width=2)
    d.rectangle([58, 58, W - 58, H - 58], outline=T["accent"], width=1)
    cx = W // 2

    f_brand = ImageFont.truetype(F_SMALL, 34)
    spaced(d, cx, 130, "鲸默阅读", f_brand, T["ink"], gap=16)
    d.line([cx - 60, 200, cx + 60, 200], fill=T["accent"], width=2)

    draw_text_block(d, img, quote, source, T)

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
    ap.add_argument("--theme", default="warm", choices=list(THEMES))
    ap.add_argument("--tag", default="每天读一点 · 把书读薄")
    a = ap.parse_args()
    if a.theme == "warm":
        render_warm(a.quote, a.source, a.out, a.tag)
    else:
        render(a.quote, a.source, a.out, a.theme, a.tag)
