#!/usr/bin/env python3
"""Generates the installer bitmaps (assets/installer/*.bmp) from the Parrot app icon.

Usage: python3 scripts/make-installer-art.py      (needs Pillow and DejaVu Sans Bold)
The generated BMPs are committed, so the build does not need this script.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICON = ROOT / "themes/browser/branding/librewolf/default256.png"
OUT = ROOT / "assets/installer"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

DARK = (25, 25, 25)  # same as the WinUpdater window


def icon(size):
    return Image.open(ICON).convert("RGBA").resize((size, size), Image.LANCZOS)


def banner():
    # 164x314 = welcome/finish page bitmap (24-bit BMP)
    w, h = 164, 314
    im = Image.new("RGB", (w, h), DARK)
    px = im.load()
    for y in range(h):  # subtle vertical gradient
        v = round(32 - 14 * y / h)
        for x in range(w):
            px[x, y] = (v, v, v)
    ic = icon(124)
    im.paste(ic, ((w - 124) // 2, 52), ic)
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(FONT, 30)
    small = ImageFont.truetype(FONT, 14)
    d.text((w / 2, 212), "Parrot", font=big, fill=(255, 255, 255), anchor="mm")
    d.text((w / 2, 244), "Browser", font=small, fill=(154, 154, 154), anchor="mm")
    im.save(OUT / "banner.bmp", "BMP")


def header(name, bg):
    # 150x57 = header bitmap shown on the right side of the inner pages
    w, h = 150, 57
    im = Image.new("RGB", (w, h), bg)
    ic = icon(44)
    im.paste(ic, (w - 44 - 12, (h - 44) // 2), ic)
    im.save(OUT / name, "BMP")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    banner()
    header("header-dark.bmp", DARK)
    header("header-light.bmp", (255, 255, 255))
    for p in sorted(OUT.glob("*.bmp")):
        print(p.name, Image.open(p).size, p.stat().st_size)
