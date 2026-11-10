# -*- coding: utf-8 -*-
"""Build web-ready image assets for the RobotIC site from the source material folder."""
import os
import glob
import math

from PIL import Image, ImageDraw, ImageFilter

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "img"))

BG = (11, 12, 14)  # site background


def ensure(*parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(p, exist_ok=True)
    return p


def open_rgba(path):
    return Image.open(path).convert("RGBA")


def flatten(im, bg=(255, 255, 255)):
    canvas = Image.new("RGB", im.size, bg)
    canvas.paste(im, (0, 0), im)
    return canvas


def trim(im, tol=8):
    """Trim uniform border (works for white or transparent backgrounds)."""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    diff = Image.new("RGBA", im.size, (0, 0, 0, 0))
    # use alpha channel when present
    alpha = im.getchannel("A")
    has_alpha = alpha.getextrema()[0] < 250
    if has_alpha:
        bbox = alpha.getbbox()
        if bbox:
            return im.crop(bbox)
    # otherwise treat near-white as background
    rgb = im.convert("RGB")
    mask = Image.new("L", im.size, 0)
    px = rgb.load()
    m = mask.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r < 255 - tol or g < 255 - tol or b < 255 - tol:
                m[x, y] = 255
    bbox = mask.getbbox()
    return im.crop(bbox) if bbox else im


def white_matte(im, threshold=200):
    """Turn a dark logo on white into a white silhouette with alpha."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    out = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    sp = rgb.load()
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = sp[x, y]
            # darkness -> alpha
            a = int(max(0, min(255, (255 - (0.299 * r + 0.587 * g + 0.114 * b)) * 1.35)))
            if a > 6:
                op[x, y] = (255, 255, 255, a)
    return out


def gap_row(im, start_frac, end_frac, min_gap=8):
    """Return the y of the first fully transparent row band inside the logo."""
    a = im.getchannel("A")
    w, h = im.size
    px = a.load()
    start = int(h * start_frac)
    end = int(h * end_frac)
    blank = 0
    for y in range(start, end):
        empty = True
        for x in range(0, w, 2):
            if px[x, y] > 8:
                empty = False
                break
        if empty:
            blank += 1
            if blank >= min_gap:
                return y - blank + 1
        else:
            blank = 0
    return end


def save_photo(im, rel, width, quality=82, bg=(161, 166, 170)):
    """Resize a studio render and store as JPEG."""
    if im.mode == "RGBA":
        im = flatten(im, bg)
    else:
        im = im.convert("RGB")
    if im.width > width:
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    return path


def save_png(im, rel):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "PNG", optimize=True)
    return path


def hero_image(src, rel, width=2000, flip=False):
    """Studio render prepared as a hero plate: light grade + bottom fade."""
    im = flatten(open_rgba(src)).convert("RGB")
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)

    overlay = Image.new("RGBA", im.size, (8, 9, 11, 16))
    w, hh = im.size
    # bottom fade so the plate melts into the page background
    fade = Image.new("RGBA", im.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    for y in range(hh):
        t = max(0.0, (y / hh - 0.68) / 0.32)
        fd.line([(0, y), (w, y)], fill=(11, 12, 14, int(250 * (t ** 1.35))))

    out = Image.alpha_composite(Image.alpha_composite(im.convert("RGBA"), overlay), fade).convert("RGB")
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path, "JPEG", quality=84, optimize=True, progressive=True)
    return path


def og_image(rel):
    """1200x630 social card built from the team render."""
    src = os.path.join(SRC, "24赛季机器人渲染图", "合照 (1).png")
    im = flatten(open_rgba(src)).convert("RGB")
    target = (1200, 630)
    scale = max(target[0] / im.width, target[1] / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left = (im.width - target[0]) // 2
    top = (im.height - target[1]) // 2
    im = im.crop((left, top, left + target[0], top + target[1]))
    overlay = Image.new("RGBA", target, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(target[1]):
        alpha = int(150 * (1 - y / target[1]) ** 1.4)
        od.line([(0, y), (target[0], y)], fill=(8, 9, 11, alpha))
    im = Image.alpha_composite(im.convert("RGBA"), overlay)
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.convert("RGB").save(path, "JPEG", quality=88, optimize=True)
    return path


def main():
    ensure()
    report = []

    # ---------- brand marks ----------
    emblem = trim(open_rgba(os.path.join(SRC, "队徽", "RobotIC队徽（白底）.png")))
    # knock the white background out
    rgb = emblem.convert("RGB")
    w, h = rgb.size
    rgba = Image.new("RGBA", (w, h))
    sp, dp = rgb.load(), rgba.load()
    for y in range(h):
        for x in range(w):
            r, g, b = sp[x, y]
            a = 255 - min(r, g, b)
            if a < 10:
                dp[x, y] = (0, 0, 0, 0)
            else:
                dp[x, y] = (r, g, b, min(255, int(a * 1.25)))
    logo = rgba.resize((round(w * 900 / w), round(h * 900 / w)), Image.LANCZOS)
    report.append(save_png(logo, "logo-robotic.png"))
    report.append(save_png(white_matte(emblem), "logo-robotic-white.png"))

    # favicon: the lock-up on a transparent canvas
    side = int(max(rgba.size) * 1.02)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2), rgba)
    square = square.resize((512, 512), Image.LANCZOS)
    report.append(save_png(square, "favicon.png"))

    # ---------- sponsor logos (placed on white chips in the UI) ----------
    sp_dir = ensure("sponsors")
    wera_src = os.path.join(SRC, "赞助商", "wera白色.jpg")
    wera = trim(open_rgba(wera_src))
    wera = flatten(wera, (255, 255, 255))
    wera = wera.resize((560, round(wera.height * 560 / wera.width)), Image.LANCZOS)
    report.append(save_png(wera, "sponsors/wera.png"))
    mps = trim(open_rgba(os.path.join(SRC, "赞助商", "mmexport1765703947885.jpg")))
    mps = flatten(mps, (255, 255, 255))
    report.append(save_png(mps.resize((600, round(mps.height * 600 / mps.width)), Image.LANCZOS), "sponsors/mps.png"))
    for f, name in [("eSUN.svg", "esun"), ("mammotion.svg", "mammotion")]:
        src = os.path.join(SRC, "赞助商", f)
        with open(src, "rb") as fh:
            data = fh.read()
        dest = os.path.join(OUT, "sponsors", name + ".svg")
        with open(dest, "wb") as fh:
            fh.write(data)
        report.append(dest)

    # ---------- QR codes ----------
    for f, name in [("wechat.png", "wechat"), ("bilibili.png", "bilibili"), ("rednote.png", "rednote"), ("QQ群.png", "qq")]:
        im = open_rgba(os.path.join(SRC, "社交媒体二维码", f))
        im = im.resize((360, 360), Image.LANCZOS)
        report.append(save_png(im, os.path.join("qr", name + ".png")))

    # ---------- robots ----------
    robots = [
        ("26赛季机器人渲染图/R2机器人.png", "robots/r2-26.jpg", 1400),
        ("26赛季机器人渲染图/R1机器人第二张.png", "robots/r1-26.jpg", 1400),
        ("24赛季机器人渲染图/R1/1.png", "robots/r1-24.jpg", 1400),
        ("24赛季机器人渲染图/r2/1.png", "robots/r2-24.jpg", 1400),
        ("23赛季机器人渲染图/R1 (1).png", "robots/r1-23.jpg", 1400),
        ("23赛季机器人渲染图/RR (1).png", "robots/rr-23.jpg", 1400),
    ]
    for src, out, w in robots:
        report.append(save_photo(open_rgba(os.path.join(SRC, src)), out, w))

    # ---------- hero ----------
    report.append(hero_image(os.path.join(SRC, "26赛季机器人渲染图", "R2机器人.png"), "hero-r2.jpg", 2200))
    report.append(hero_image(os.path.join(SRC, "26赛季机器人渲染图", "R1机器人第二张.png"), "join-hero.jpg", 1800, flip=True))

    # ---------- gallery ----------
    gallery = [
        ("24赛季机器人渲染图/合照 (1).png", "gallery/team-01.jpg"),
        ("24赛季机器人渲染图/合照 (3).png", "gallery/team-02.jpg"),
        ("24赛季机器人渲染图/合照 (5).png", "gallery/team-03.jpg"),
        ("24赛季机器人渲染图/历史 (1).png", "gallery/history-01.jpg"),
        ("24赛季机器人渲染图/历史 (2).png", "gallery/history-02.jpg"),
        ("24赛季机器人渲染图/r2/3.png", "gallery/detail-01.jpg"),
        ("24赛季机器人渲染图/r2/6.png", "gallery/detail-02.jpg"),
        ("24赛季机器人渲染图/R1/4.png", "gallery/detail-03.jpg"),
        ("23赛季机器人渲染图/R1 (3).png", "gallery/detail-04.jpg"),
        ("24赛季机器人渲染图/R1/8.png", "gallery/detail-05.jpg"),
    ]
    for src, out in gallery:
        report.append(save_photo(open_rgba(os.path.join(SRC, src)), out, 1200, quality=78))

    report.append(og_image("og-cover.jpg"))

    total = sum(os.path.getsize(p) for p in report if os.path.exists(p))
    print("files:", len(report), "total MB:", round(total / 1048576, 2))
    for p in report:
        print("  ", round(os.path.getsize(p) / 1024, 1), "KB", os.path.relpath(p, OUT))


if __name__ == "__main__":
    main()
