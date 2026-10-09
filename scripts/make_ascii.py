#!/usr/bin/env python3
"""Photo -> ASCII portrait rows (assets/portrait.txt).

One-off helper; the README build only needs the resulting text file.

    pip install rembg[cpu] opencv-python-headless pillow numpy
    rembg i photo.jpg cutout.png                     # background removal
    python3 scripts/make_ascii.py cutout.png --crop 312 28 528 262 --cols 150

Dark features (hair, glasses, beard) become dense glyphs, which reads like a
pencil sketch on a dark terminal.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

RAMP = " .,:;-=+*cs%#@"   # sparse -> dense


def to_ascii(path, cols=150, crop=None, upscale=3, passes=5, clahe=2.0, tile=4,
             gamma=1.7, levels=5, edge_w=1.0, edge_block=15, edge_c=6,
             bright_cut=0.08, skin_floor=0.05, outline=0.3, fade_rows=10,
             ramp=RAMP):
    im = Image.open(path).convert("RGBA")
    if crop:
        im = im.crop(crop)
    im = im.resize((im.width * upscale, im.height * upscale), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    rgb, alpha = a[..., :3].astype(np.uint8), a[..., 3] / 255.0

    # edge-preserving smoothing -> flat, cartoon-like tones (cleaner glyphs)
    sm = rgb.copy()
    for _ in range(passes):
        sm = cv2.bilateralFilter(sm, 9, 45, 9)
    gray = cv2.cvtColor(sm, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=clahe, tileGridSize=(tile, tile)).apply(gray)
    g = gray.astype(np.float32) / 255.0
    m = alpha > 0.5
    lo, hi = np.percentile(g[m], 1), np.percentile(g[m], 99)
    norm = np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1)
    if levels:                                   # posterise
        norm = np.round(norm * levels) / levels
    ink = (1.0 - norm) ** gamma                  # dark -> dense

    if edge_w:                                   # sketch lines
        e = cv2.adaptiveThreshold(cv2.medianBlur(gray, 7), 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
                                  edge_block, edge_c)
        ink = np.maximum(ink, edge_w * (255 - e).astype(np.float32) / 255.0)
    if skin_floor:                               # keep sunlit skin faintly textured
        sat = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[..., 1].astype(np.float32) / 255.0
        ink = np.maximum(ink, skin_floor * np.clip((sat - 0.18) / 0.12, 0, 1))
    ink = np.where(ink < bright_cut, 0.0, ink)
    ink = np.where(m, ink, 0.0)

    h, w = ink.shape
    rows = int(round(h / ((w / cols) * 2.0)))    # glyph cells are ~1:2
    small = cv2.resize(ink, (cols, rows), interpolation=cv2.INTER_AREA)
    a_s = cv2.resize(alpha, (cols, rows), interpolation=cv2.INTER_AREA)
    if outline:                                  # faint silhouette
        a8 = (a_s * 255).astype(np.uint8)
        mag = np.hypot(cv2.Sobel(a8, cv2.CV_32F, 1, 0), cv2.Sobel(a8, cv2.CV_32F, 0, 1))
        small = np.maximum(small, outline * np.clip(mag / 600.0, 0, 1))
    if fade_rows:                                # soften the cut-off at the bottom
        k = min(fade_rows, rows)
        small[-k:] *= np.linspace(1.0, 0.35, k)[:, None]

    n = len(ramp)
    idx = np.clip((small * (n - 1)).round().astype(int), 0, n - 1)
    out = ["".join(ramp[i] for i in r).rstrip() for r in idx]
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cutout", help="background-removed RGBA PNG")
    ap.add_argument("--crop", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--cols", type=int, default=150)
    ap.add_argument("--gamma", type=float, default=1.7)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "assets" / "portrait.txt"))
    a = ap.parse_args()
    rows = to_ascii(a.cutout, cols=a.cols, crop=tuple(a.crop) if a.crop else None, gamma=a.gamma)
    Path(a.out).write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {a.out}: {len(rows)} rows x {max(map(len, rows))} cols")
