#!/usr/bin/env python3
"""Build the self-hosted animated SVGs used by the profile README.

    python3 scripts/build_assets.py          # writes ./assets/*.svg

Standard library only. Every SVG is safe for GitHub's image proxy: no
scripts, no external fonts or images, just inline CSS + SMIL animation.
Looping effects are switched off for viewers with "reduce motion" enabled,
and every element's resting state is its final, readable state.

The ASCII portrait lives in assets/portrait.txt (generated once from a photo
with scripts/make_ascii.py) so this script needs no imaging libraries.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono','DejaVu Sans Mono',monospace")
SANS = ("'Segoe UI',-apple-system,BlinkMacSystemFont,Inter,'Helvetica Neue',"
        "Arial,sans-serif")
ADV = 0.6  # monospace advance width (em); textLength pins every font to it
BOLD = ' font-weight="700"'

C = {
    "bg0": "#0d1117", "bg1": "#111722", "tile": "#131b29", "tile2": "#0f1623",
    "line": "#30363d", "line2": "#1f2a3a",
    "text": "#e6edf3", "fg": "#c9d1d9", "muted": "#7d8590", "dim": "#484f58",
    "cyan": "#22d3ee", "cyan2": "#67e8f9", "green": "#3fb950", "green2": "#56d364",
    "amber": "#e3b341", "red": "#f85149", "violet": "#a78bfa", "blue": "#58a6ff",
}

# ----------------------------------------------------------------- profile --
NAME = "Nagarajan Thathasamy"
HANDLE = "nagarajan@soc"
STATS = [  # value, label, sub, accent
    ("3+ yrs", "in the SOC", "SOC analyst -> L2/L3 SecOps", "cyan"),
    ("40,000+", "endpoints defended", "AWS · Azure · on-prem", "green"),
    ("1,000+", "alerts triaged / month", "24/7 SOC · within SLA", "amber"),
    ("1.6M+", "events searched < 1 s", "LogSec case-based SIEM", "violet"),
    ("7,000+", "leaked secrets surfaced", "GIT Recon exposure scanner", "red"),
    ("-40%", "critical-vuln backlog", "CVE tracking · patch coordination", "blue"),
]
ARSENAL = [
    "CrowdStrike Falcon", "Falcon LogScale", "ManageEngine Log360",
    "Falcon AIDR", "SpyCloud", "Microsoft Sentinel", "IBM QRadar",
    "FortiSIEM", "Cynet XDR", "Forcepoint DLP", "Magnet AXIOM",
    "Cellebrite", "Nessus", "Qualys", "AWS GuardDuty", "Python",
    "Sigma", "YARA", "MITRE ATT&CK",
]


# ----------------------------------------------------------------- helpers --
def f(x: float) -> str:
    """Compact number formatting for SVG attributes."""
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def esc(s: str) -> str:
    return escape(s, {'"': "&quot;"})


def svg_open(w, h, title, desc, extra_css=""):
    css = f"""
text{{font-family:{MONO}}}
.sans{{font-family:{SANS}}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes hold{{0%,99%{{opacity:0}}100%{{opacity:1}}}}
@keyframes f0{{0%,33%{{opacity:1}}33.1%,100%{{opacity:0}}}}
@keyframes f1{{0%,33%{{opacity:0}}33.1%,66%{{opacity:1}}66.1%,100%{{opacity:0}}}}
@keyframes f2{{0%,66%{{opacity:0}}66.1%,99.9%{{opacity:1}}100%{{opacity:0}}}}
.blink{{animation:blink 1.05s step-end infinite}}
.pulse{{animation:pulse 1.8s ease-in-out infinite}}
{extra_css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(w)}" height="{f(h)}" '
            f'viewBox="0 0 {f(w)} {f(h)}" role="img" aria-labelledby="t d">'
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
            f'<style>{css}</style>')


def mono_text(x, y, s, fs, fill, extra="", cls=""):
    """Monospace text pinned to the ADV grid so columns line up in any font."""
    s = s.rstrip()
    if not s:
        return ""
    lead = len(s) - len(s.lstrip(" "))
    body = s.lstrip(" ")
    cw = fs * ADV
    c = f' class="{cls}"' if cls else ""
    return (f'<text{c} x="{f(x + lead * cw)}" y="{f(y)}" font-size="{f(fs)}" fill="{fill}" '
            f'xml:space="preserve" textLength="{f(len(body) * cw)}" '
            f'lengthAdjust="spacing"{extra}>{esc(body)}</text>')


def window(x, y, w, h, title, gid):
    """macOS-style terminal window chrome."""
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{C["bg1"]}"/><stop offset="1" stop-color="{C["bg0"]}"/>'
        f'</linearGradient>'
        f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="14" fill="url(#{gid})"/>'
        f'<rect x="{f(x + .5)}" y="{f(y + .5)}" width="{f(w - 1)}" height="{f(h - 1)}" rx="14" '
        f'fill="none" stroke="{C["line"]}"/>'
        f'<line x1="{f(x)}" y1="{f(y + 36)}" x2="{f(x + w)}" y2="{f(y + 36)}" stroke="{C["line"]}"/>'
        f'<circle cx="{f(x + 22)}" cy="{f(y + 18)}" r="6" fill="#ff5f56"/>'
        f'<circle cx="{f(x + 42)}" cy="{f(y + 18)}" r="6" fill="#ffbd2e"/>'
        f'<circle cx="{f(x + 62)}" cy="{f(y + 18)}" r="6" fill="#27c93f"/>'
        f'<text x="{f(x + w / 2)}" y="{f(y + 23)}" font-size="14" fill="{C["muted"]}" '
        f'text-anchor="middle">{esc(title)}</text>'
    )


def typed(uid, x, y, segments, fs, begin, per=0.045, cursor=True, keep_cursor=False,
          cursor_color=None):
    """A line typed character by character (SMIL clip, GitHub-safe).

    segments: list of (text, fill). Resting state = fully typed, so renderers
    without SMIL still show the text. Returns (svg, end_time)."""
    cw = fs * ADV
    text = "".join(s for s, _ in segments)
    n = len(text)
    total = begin + n * per
    W = n * cw
    vals = ["0"] + [f(k * cw) for k in range(1, n + 1)]
    keys = ["0"] + [f"{(begin + k * per) / total:.4f}" for k in range(1, n + 1)]
    keys[-1] = "1"
    out = [f'<clipPath id="{uid}"><rect x="{f(x)}" y="{f(y - fs * 1.05)}" '
           f'width="{f(W)}" height="{f(fs * 1.45)}">'
           f'<animate attributeName="width" values="{";".join(vals)}" '
           f'keyTimes="{";".join(keys)}" calcMode="discrete" dur="{f(total)}s" '
           f'fill="freeze"/></rect></clipPath><g clip-path="url(#{uid})">']
    col = 0
    for s, fill in segments:
        if s.strip():
            out.append(mono_text(x + col * cw, y, s, fs, fill))
        col += len(s)
    out.append("</g>")
    if cursor:
        cc = cursor_color or C["fg"]
        cx_vals = [f(x)] + [f(x + k * cw) for k in range(1, n + 1)]
        out.append(
            f'<rect x="{f(x + W)}" y="{f(y - fs * .85)}" width="{f(cw * .9)}" height="{f(fs * 1.05)}" '
            f'fill="{cc}" opacity="0">'
            f'<animate attributeName="x" values="{";".join(cx_vals)}" keyTimes="{";".join(keys)}" '
            f'calcMode="discrete" dur="{f(total)}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{f(begin)}s"/>'
            + ("" if keep_cursor else f'<set attributeName="opacity" to="0" begin="{f(total + .35)}s"/>')
            + "</rect>")
    return "".join(out), total


def scrambled(s: str, rnd: random.Random) -> str:
    pool = "0123456789ABCDEF#%@$&"
    return "".join(rnd.choice(pool) if ch.isalnum() else ch for ch in s)


# ----------------------------------------------------------------- whoami ---
def build_whoami() -> str:
    rows = (ASSETS / "portrait.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    cols = max(len(r) for r in rows)

    LW, GAP, RW = 760, 24, 800          # left pane, gap, right pane
    W = LW + GAP + RW
    pad = 24
    cw = (LW - 2 * pad) / cols           # ascii cell width
    fs = cw / ADV
    lh = cw * 2.0                        # cells are 1:2 like the converter
    top = 36 + 16
    art_h = len(rows) * lh
    H = int(math.ceil(top + art_h + 14 + 52))
    rnd = random.Random(37)

    css = """
.tile{animation:rise .55s cubic-bezier(.2,.7,.2,1) both}
.chip{animation:rise .4s ease-out both}
.scan{animation:scan 7s linear 5.2s infinite both}
@keyframes scan{0%{transform:translateY(0);opacity:0}6%{opacity:1}94%{opacity:1}100%{transform:translateY(%(art)spx);opacity:0}}
.bar{animation:grow 1.1s cubic-bezier(.2,.7,.2,1) both}
@keyframes grow{from{stroke-dashoffset:var(--len)}to{stroke-dashoffset:0}}
""".replace("%(art)s", f(art_h))
    out = [svg_open(
        W, H,
        f"{NAME} — ASCII portrait and SecOps stats",
        "Left: an ASCII-art portrait of Nagarajan Thathasamy drawn line by line in a "
        "terminal running ./portrait.sh. Right: ./stats.sh --secops showing 3+ years in "
        "the SOC, 40,000+ endpoints defended, 1,000+ alerts triaged per month, 1.6M+ "
        "events searched in under a second, 7,000+ leaked secrets surfaced and a 40% cut "
        "in critical-vulnerability backlog, followed by his security tool arsenal.",
        css)]
    out.append("<defs>")
    out.append(f'<linearGradient id="ink" x1="0" y1="{f(top)}" x2="0" y2="{f(top + art_h)}" '
               f'gradientUnits="userSpaceOnUse">'
               f'<stop offset="0" stop-color="{C["cyan2"]}"/>'
               f'<stop offset=".45" stop-color="#d7e3ee"/>'
               f'<stop offset="1" stop-color="{C["green2"]}"/></linearGradient>')
    out.append(f'<linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0" stop-color="{C["cyan"]}" stop-opacity="0"/>'
               f'<stop offset="1" stop-color="{C["cyan"]}" stop-opacity=".14"/></linearGradient>')
    out.append(f'<clipPath id="artclip"><rect x="0" y="{f(top - 4)}" width="{f(LW)}" '
               f'height="{f(art_h + 8)}"/></clipPath>')
    out.append("</defs>")

    # ---------------- left pane: portrait ----------------
    out.append(window(0, 0, LW, H, f"{HANDLE}: ~$ ./portrait.sh", "wl"))
    dt = 0.052
    t0 = 0.35
    for i, r in enumerate(rows):
        y = top + i * lh + lh * 0.78
        b = t0 + i * dt
        if not r.strip():
            continue
        x0 = pad
        rw = len(r) * cw
        uid = f"r{i}"
        out.append(
            f'<clipPath id="{uid}"><rect x="{f(x0)}" y="{f(y - lh * .8)}" height="{f(lh)}" '
            f'width="{f(rw)}"><animate attributeName="width" values="0;0;{f(rw)}" '
            f'keyTimes="0;{b / (b + dt):.4f};1" dur="{f(b + dt)}s" fill="freeze"/></rect></clipPath>'
            f'<g clip-path="url(#{uid})">'
            f'{mono_text(x0, y, r, fs, "url(#ink)")}</g>'
            f'<rect y="{f(y - lh * .62)}" width="{f(cw)}" height="{f(lh * .72)}" fill="{C["cyan2"]}" '
            f'opacity="0"><animate attributeName="x" values="{f(x0)};{f(x0)};{f(x0 + rw)}" '
            f'keyTimes="0;{b / (b + dt):.4f};1" dur="{f(b + dt)}s" fill="freeze"/>'
            f'<set attributeName="opacity" to=".9" begin="{f(b)}s"/>'
            f'<set attributeName="opacity" to="0" begin="{f(b + dt)}s"/></rect>')
    t_art = t0 + len(rows) * dt
    # CRT scan sweep over the finished portrait
    out.append(f'<g clip-path="url(#artclip)"><rect class="scan" x="0" y="{f(top - 60)}" '
               f'width="{f(LW)}" height="46" fill="url(#scanG)"/></g>')
    # bottom prompt
    by = H - 26
    out.append(f'<line x1="0" y1="{f(H - 52)}" x2="{f(LW)}" y2="{f(H - 52)}" stroke="{C["line"]}"/>')
    prompt = f"{HANDLE}:~$ "
    fs_b = 17
    s_who, t_who = typed("who", pad, by, [(prompt, C["green"]), ("whoami ", C["fg"])],
                         fs_b, begin=t_art + .1, per=.05, cursor=False)
    out.append(s_who)
    name_x = pad + len(prompt + "whoami ") * fs_b * ADV
    out.append(f'<g style="animation:fade .4s {f(t_who + .25)}s both">'
               f'{mono_text(name_x, by, NAME, fs_b, C["text"], extra=BOLD)}</g>')
    cur_x = name_x + (len(NAME) + 1) * fs_b * ADV
    out.append(f'<g style="animation:fade .01s {f(t_who + .3)}s both"><rect class="blink" '
               f'x="{f(cur_x)}" y="{f(by - 14)}" width="{f(fs_b * ADV)}" height="18" '
               f'fill="{C["cyan2"]}"/></g>')

    # ---------------- right pane: stats ----------------
    X = LW + GAP
    out.append(window(X, 0, RW, H, f"{HANDLE}: ~$ ./stats.sh --secops", "wr"))
    px = X + 28
    s1, t1 = typed("c1", px, 76, [("$ ", C["green"]), ("./stats.sh --secops", C["fg"])],
                   18, begin=.3, per=.045)
    out.append(s1)
    tw, th, tg = (RW - 56 - 16) / 2, 104, 12
    ty0 = 96
    for k, (val, label, sub, acc) in enumerate(STATS):
        col, row = k % 2, k // 2
        tx = px + col * (tw + 16)
        ty = ty0 + row * (th + tg)
        d = t1 + .15 + k * .22
        a = C[acc]
        out.append(f'<g class="tile" style="animation-delay:{f(d)}s">')
        out.append(f'<rect x="{f(tx)}" y="{f(ty)}" width="{f(tw)}" height="{th}" rx="10" '
                   f'fill="{C["tile"]}" stroke="{C["line2"]}"/>')
        out.append(f'<rect x="{f(tx)}" y="{f(ty + 14)}" width="3" height="{th - 28}" rx="1.5" fill="{a}"/>')
        out.append(mono_text(tx + 18, ty + 28, "$ " + label, 14.5, C["muted"]))
        # value with a short decode flicker
        vy = ty + 69
        for j, cls in enumerate(("f0", "f1", "f2")):
            out.append(f'<g opacity="0" style="animation:{cls} .5s {f(d + .1)}s both">'
                       f'{mono_text(tx + 18, vy, scrambled(val, rnd), 38, a)}</g>')
        out.append(f'<g style="animation:hold .5s {f(d + .1)}s both">'
                   f'{mono_text(tx + 18, vy, val, 38, a, extra=BOLD)}</g>')
        out.append(mono_text(tx + 18, ty + 91, sub, 13, C["fg"], extra=' opacity=".75"'))
        # live meter
        mx, my, ml = tx + tw - 76, ty + 26, 56
        out.append(f'<line x1="{f(mx)}" y1="{f(my)}" x2="{f(mx + ml)}" y2="{f(my)}" stroke="{C["line2"]}" '
                   f'stroke-width="4" stroke-linecap="round"/>'
                   f'<line class="bar" x1="{f(mx)}" y1="{f(my)}" x2="{f(mx + ml)}" y2="{f(my)}" stroke="{a}" '
                   f'stroke-width="4" stroke-linecap="round" stroke-dasharray="{ml}" '
                   f'style="--len:{ml};animation-delay:{f(d + .2)}s"/>')
        out.append(f'<circle class="pulse" cx="{f(tx + tw - 12)}" cy="{f(my)}" r="3.5" fill="{a}" '
                   f'style="animation-delay:{f(k * .3)}s"/>')
        out.append("</g>")
    ay = ty0 + 3 * th + 2 * tg + 40
    s2, t2 = typed("c2", px, ay, [("$ ", C["green"]), ("cat arsenal.txt", C["fg"])],
                   18, begin=t1 + .25 + 6 * .22 + .3, per=.045)
    out.append(s2)
    # chips flow layout
    cx, cy = px, ay + 18
    chip_fs = 14
    maxx = X + RW - 28
    for j, name in enumerate(ARSENAL):
        wchip = len(name) * chip_fs * ADV + 24
        if cx + wchip > maxx:
            cx, cy = px, cy + 38
        d = t2 + .1 + j * .05
        hue = ["cyan", "green", "amber", "violet", "blue"][j % 5]
        out.append(f'<g class="chip" style="animation-delay:{f(d)}s">'
                   f'<rect x="{f(cx)}" y="{f(cy)}" width="{f(wchip)}" height="30" rx="15" '
                   f'fill="{C["tile"]}" stroke="{C["line"]}"/>'
                   f'<circle cx="{f(cx + 12)}" cy="{f(cy + 15)}" r="3" fill="{C[hue]}"/>'
                   f'{mono_text(cx + 19, cy + 20, name, chip_fs, C["fg"])}</g>')
        cx += wchip + 8
    t_chips = t2 + .1 + len(ARSENAL) * .05
    # certification line
    cy += 74
    s3, t3 = typed("c3", px, cy, [("$ ", C["green"]), ("cat certs.txt", C["fg"])],
                   18, begin=t_chips + .25, per=.045)
    out.append(s3)
    out.append(f'<g style="animation:fade .4s {f(t3 + .2)}s both">'
               f'{mono_text(px, cy + 28, "[ok] Microsoft SC-200 · Security Operations Analyst (2024)", 14.5, C["green2"])}'
               f'{mono_text(px, cy + 51, "[ok] Seceon Certified Professional (2023)", 14.5, C["green2"])}</g>')
    assert cy + 51 < H - 60, f"right pane overflows: {cy + 51} vs {H - 60}"
    # status bar
    out.append(f'<line x1="{f(X)}" y1="{f(H - 52)}" x2="{f(X + RW)}" y2="{f(H - 52)}" stroke="{C["line"]}"/>')
    out.append(mono_text(px, by, f"{HANDLE}:~$ status", 17, C["muted"]))
    sx = px + len(f"{HANDLE}:~$ status ") * 17 * ADV
    out.append(f'<circle class="pulse" cx="{f(sx + 6)}" cy="{f(by - 6)}" r="6" fill="{C["green"]}"/>')
    out.append(mono_text(sx + 20, by, "monitoring · every alert is a lead", 17, C["green2"]))
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------- hero ---
TICKER = [  # illustrative detections that describe the day job
    ("EDR", "T1059.001 encoded PowerShell on a workstation", "host contained"),
    ("SIEM", "T1110 brute force · 412 failed logons in 5 min", "source blocked"),
    ("AIDR", "prompt-injection attempt inside an AI tool", "policy enforced"),
    ("LEAK", "employee credential found in a dark-web dump", "password reset"),
    ("DLP", "T1567 upload to personal cloud storage", "quarantined"),
    ("DFIR", "disk + memory timeline rebuilt", "RCA filed"),
    ("VULN", "CVSS 9.8 on an internet-facing asset", "patched within SLA"),
]
BLIPS = [  # (angle deg, radius fraction, ATT&CK technique)
    (34, .64, "T1059.001"), (118, .80, "T1110"), (198, .44, "T1566"),
    (262, .72, "T1003"), (320, .34, "T1567"),
]


def build_hero() -> str:
    W, H = 1200, 340
    cx, cy, R = 182, 148, 104
    T = 4.0
    band_y = 292
    tfs = 14
    tcw = tfs * ADV

    # ticker content (one copy), measured on the monospace grid
    spans, n = [], 0
    for tag, msg, res in TICKER:
        for s, col in ((f"[{tag}] ", C["amber"]), (msg, C["fg"]), ("  ->  ", C["muted"]),
                       (res, C["green2"]), ("      //      ", C["dim"])):
            spans.append(f'<tspan fill="{col}">{esc(s)}</tspan>')
            n += len(s)
    L = n * tcw
    tick_dur = L / 46.0

    css = f"""
.sweep{{transform-origin:{cx}px {cy}px;animation:spin {T}s linear infinite}}
.orbit{{transform-origin:{cx}px {cy}px;animation:spin 40s linear infinite reverse}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.blip{{animation:blip {T}s linear infinite}}
@keyframes blip{{0%{{opacity:1}}55%{{opacity:.1}}100%{{opacity:.1}}}}
.ripple{{animation:ripple {T}s ease-out infinite}}
@keyframes ripple{{0%{{transform:scale(.3);opacity:.9}}35%{{transform:scale(3.2);opacity:0}}100%{{transform:scale(3.2);opacity:0}}}}
.ticker{{animation:tick {f(tick_dur)}s linear infinite}}
@keyframes tick{{to{{transform:translateX(-{f(L)}px)}}}}
.scanl{{animation:scanl 6.5s linear infinite}}
@keyframes scanl{{from{{transform:translateY(-90px)}}to{{transform:translateY({H}px)}}}}
.gA{{animation:gA 7s linear 2.2s infinite both}}
.gB{{animation:gB 7s linear 2.2s infinite both}}
@keyframes gA{{0%,88%{{opacity:0;transform:none}}88.5%{{opacity:.9;transform:translate(-6px,1px)}}89.5%{{opacity:.9;transform:translate(5px,-1px)}}90.5%{{opacity:.9;transform:translate(-3px,0)}}91.5%,100%{{opacity:0;transform:none}}}}
@keyframes gB{{0%,88%{{opacity:0;transform:none}}88.5%{{opacity:.85;transform:translate(6px,-1px)}}89.5%{{opacity:.85;transform:translate(-4px,1px)}}90.5%{{opacity:.85;transform:translate(3px,0)}}91.5%,100%{{opacity:0;transform:none}}}}
.chip{{animation:rise .5s ease-out both}}
"""
    out = [svg_open(
        W, H, f"{NAME} — Security Engineer",
        "Animated SOC-console banner: a radar sweep lights up MITRE ATT&CK technique "
        "blips while the name Nagarajan Thathasamy decodes in, followed by 'Security "
        "Engineer // Detection Engineering // Incident Response // DFIR', the tagline "
        "'every alert is a lead' and a scrolling ticker of detections being contained.",
        css)]
    out.append("<defs>")
    out.append(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>')
    out.append(f'<linearGradient id="bgH" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b111c"/>'
               f'<stop offset="1" stop-color="{C["bg0"]}"/></linearGradient>')
    out.append(f'<radialGradient id="glowR" cx="{cx}" cy="{cy}" r="{R * 1.6}" gradientUnits="userSpaceOnUse">'
               f'<stop offset="0" stop-color="{C["cyan"]}" stop-opacity=".16"/>'
               f'<stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></radialGradient>')
    out.append(f'<radialGradient id="glowT" cx="760" cy="150" r="520" gradientUnits="userSpaceOnUse">'
               f'<stop offset="0" stop-color="#1d4ed8" stop-opacity=".10"/>'
               f'<stop offset="1" stop-color="#1d4ed8" stop-opacity="0"/></radialGradient>')
    out.append('<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">'
               f'<path d="M28 0H0V28" fill="none" stroke="{C["cyan"]}" stroke-opacity=".07"/></pattern>')
    out.append(f'<linearGradient id="scanH" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0" stop-color="{C["cyan"]}" stop-opacity="0"/>'
               f'<stop offset=".5" stop-color="{C["cyan"]}" stop-opacity=".06"/>'
               f'<stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient>')
    out.append(f'<linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0">'
               f'<stop offset="0" stop-color="#090e17"/><stop offset=".78" stop-color="#090e17"/>'
               f'<stop offset="1" stop-color="#090e17" stop-opacity="0"/></linearGradient>')
    out.append('<filter id="soft" x="-50%" y="-50%" width="200%" height="200%">'
               '<feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/>'
               '<feMergeNode in="SourceGraphic"/></feMerge></filter>')
    out.append("</defs>")
    out.append('<g clip-path="url(#card)">')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#bgH)"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#grid)"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#glowT)"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R * 1.6}" fill="url(#glowR)"/>')

    # ---- radar
    for k, (rr, op) in enumerate(((1, .55), (.75, .22), (.5, .22), (.25, .22))):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{f(R * rr)}" fill="none" stroke="{C["cyan"]}" '
                   f'stroke-opacity="{op}" stroke-width="{1.4 if k == 0 else 1}"/>')
    out.append(f'<path d="M{cx - R} {cy}H{cx + R}M{cx} {cy - R}V{cy + R}" stroke="{C["cyan"]}" stroke-opacity=".16"/>')
    ticks = []
    for d in range(0, 360, 6):
        a = math.radians(d)
        r2 = R + (10 if d % 30 == 0 else 5)
        ticks.append(f"M{f(cx + R * math.cos(a))} {f(cy + R * math.sin(a))}"
                     f"L{f(cx + r2 * math.cos(a))} {f(cy + r2 * math.sin(a))}")
    out.append(f'<path d="{"".join(ticks)}" stroke="{C["cyan"]}" stroke-opacity=".45"/>')
    out.append(f'<circle class="orbit" cx="{cx}" cy="{cy}" r="{R + 18}" fill="none" stroke="{C["cyan"]}" '
               f'stroke-opacity=".3" stroke-dasharray="2 7"/>')
    for d, lab in ((0, "090"), (90, "180"), (180, "270"), (270, "000")):
        a = math.radians(d)
        tx, ty = cx + (R + 26) * math.cos(a), cy + (R + 26) * math.sin(a) + 3.5
        out.append(f'<text x="{f(tx)}" y="{f(ty)}" font-size="10" fill="{C["muted"]}" text-anchor="middle">{lab}</text>')
    # sweep wedge (many thin slices = conic fade)
    sl = []
    span, nsl = 64, 32
    for k in range(nsl):
        a0 = math.radians(-span + k * span / nsl)
        a1 = math.radians(-span + (k + 1) * span / nsl + .3)
        op = (k + 1) / nsl
        sl.append(f'<path d="M{cx} {cy}L{f(cx + R * math.cos(a0))} {f(cy + R * math.sin(a0))}'
                  f'A{R} {R} 0 0 1 {f(cx + R * math.cos(a1))} {f(cy + R * math.sin(a1))}Z" '
                  f'fill="{C["cyan"]}" fill-opacity="{f(.30 * op ** 2.2)}"/>')
    out.append(f'<g class="sweep">{"".join(sl)}<line x1="{cx}" y1="{cy}" x2="{cx + R}" y2="{cy}" '
               f'stroke="{C["cyan2"]}" stroke-width="2" filter="url(#soft)"/></g>')
    for ang, rf, tech in BLIPS:
        a = math.radians(ang)
        bx, by_ = cx + R * rf * math.cos(a), cy + R * rf * math.sin(a)
        delay = ang / 360 * T - T
        out.append(f'<g class="blip" style="animation-delay:{f(delay)}s">'
                   f'<circle cx="{f(bx)}" cy="{f(by_)}" r="3.6" fill="{C["amber"]}" filter="url(#soft)"/>'
                   f'<text x="{f(bx + 8)}" y="{f(by_ - 6)}" font-size="11" fill="{C["amber"]}">{tech}</text></g>'
                   f'<circle class="ripple" cx="{f(bx)}" cy="{f(by_)}" r="4" fill="none" stroke="{C["amber"]}" '
                   f'style="transform-origin:{f(bx)}px {f(by_)}px;animation-delay:{f(delay)}s"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="3.2" fill="{C["cyan2"]}"/>')

    # ---- identity block
    x0 = 360
    hud = "SOC://CONSOLE  //  NODE: CHENNAI-IN  //  SHIFT: 24x7"
    out.append(mono_text(x0, 62, hud, 13, C["muted"], extra=' letter-spacing="0"'))
    live = "MONITORING"
    lx = 1160 - len(live) * 13 * ADV
    out.append(f'<circle class="pulse" cx="{f(lx - 12)}" cy="57.5" r="4.5" fill="{C["green"]}"/>')
    out.append(mono_text(lx, 62, live, 13, C["green2"]))
    # name: wipe-in, then periodic RGB glitch
    name = NAME.upper()
    nfs, nlen, ny = 60, 798, 132
    attrs = (f'x="{x0}" y="{ny}" font-size="{nfs}" font-weight="800" '
             f'textLength="{nlen}" lengthAdjust="spacingAndGlyphs" letter-spacing="1"')
    out.append(f'<clipPath id="nameclip"><rect x="{x0 - 4}" y="{ny - nfs}" height="{nfs + 18}" width="{nlen + 12}">'
               f'<animate attributeName="width" values="0;0;{nlen + 12}" keyTimes="0;.25;1" dur="1.25s" '
               f'calcMode="spline" keySplines="0 0 1 1;.2 .7 .2 1" fill="freeze"/></rect></clipPath>')
    out.append('<g clip-path="url(#nameclip)">')
    out.append(f'<text class="sans gA" {attrs} fill="{C["cyan"]}" opacity="0">{esc(name)}</text>')
    out.append(f'<text class="sans gB" {attrs} fill="{C["red"]}" opacity="0">{esc(name)}</text>')
    out.append(f'<text class="sans" {attrs} fill="{C["text"]}">{esc(name)}</text>')
    out.append('</g>')
    out.append(f'<rect x="{x0}" y="{ny - nfs + 2}" width="3" height="{nfs + 10}" fill="{C["cyan2"]}" opacity="0" '
               f'filter="url(#soft)"><animate attributeName="x" values="{x0};{x0};{x0 + nlen + 8}" keyTimes="0;.25;1" '
               f'dur="1.25s" calcMode="spline" keySplines="0 0 1 1;.2 .7 .2 1" fill="freeze"/>'
               f'<set attributeName="opacity" to=".95" begin=".31s"/><set attributeName="opacity" to="0" begin="1.3s"/></rect>')
    sub, t_sub = typed("sub", x0 + 2, 178, [("SECURITY ENGINEER // DETECTION ENGINEERING // INCIDENT RESPONSE // DFIR", C["cyan"])],
                       16.5, begin=1.25, per=.018, cursor=True, cursor_color=C["cyan"])
    out.append(sub)
    tag, t_tag = typed("tag", x0 + 2, 226, [("> ", C["green"]), ("every alert is a lead", C["green2"])],
                       25, begin=t_sub + .25, per=.055, cursor=True, keep_cursor=True, cursor_color=C["green2"])
    out.append(tag)
    # blinking cursor after the tagline once typing has finished
    end_x = x0 + 2 + len("> every alert is a lead") * 25 * ADV + 4
    out.append(f'<g style="animation:fade .01s {f(t_tag + .4)}s both"><rect class="blink" x="{f(end_x)}" y="205" '
               f'width="13" height="26" fill="{C["green2"]}"/></g>')
    chips = ["3+ YRS SOC", "40K+ ENDPOINTS", "MITRE ATT&CK", "AI SECURITY", "SC-200"]
    chx = x0
    for j, ch in enumerate(chips):
        wch = len(ch) * 13 * ADV + 28
        out.append(f'<g class="chip" style="animation-delay:{f(t_tag + .1 + j * .12)}s">'
                   f'<rect x="{f(chx)}" y="248" width="{f(wch)}" height="28" rx="6" fill="{C["cyan"]}" '
                   f'fill-opacity=".06" stroke="{C["cyan"]}" stroke-opacity=".35"/>'
                   f'{mono_text(chx + 14, 266.5, ch, 13, C["fg"])}</g>')
        chx += wch + 10

    # ---- ticker band
    out.append(f'<rect x="0" y="{band_y}" width="{W}" height="{H - band_y}" fill="#090e17"/>')
    out.append(f'<line x1="0" y1="{band_y}" x2="{W}" y2="{band_y}" stroke="{C["line"]}"/>')
    ty = band_y + 29
    copy = (f'<text y="{f(ty)}" font-size="{tfs}" xml:space="preserve" textLength="{f(L)}" '
            f'lengthAdjust="spacing" x="%s">{"".join(spans)}</text>')
    out.append(f'<g class="ticker">{copy % f(240)}{copy % f(240 + L)}</g>')
    out.append(f'<rect x="0" y="{band_y + 1}" width="240" height="{H - band_y - 1}" fill="url(#fadeL)"/>')
    out.append(f'<circle class="pulse" cx="30" cy="{ty - 5}" r="5" fill="{C["red"]}"/>')
    out.append(mono_text(44, ty, "LIVE DETECTIONS", 13, C["text"]))

    # ---- overlays
    out.append(f'<rect class="scanl" x="0" y="0" width="{W}" height="90" fill="url(#scanH)"/>')
    br = []
    for (x, y, dx, dy) in ((14, 14, 1, 1), (W - 14, 14, -1, 1), (14, band_y - 12, 1, -1), (W - 14, band_y - 12, -1, -1)):
        br.append(f"M{x} {y + 22 * dy}V{y}H{x + 22 * dx}")
    out.append(f'<path d="{"".join(br)}" fill="none" stroke="{C["cyan"]}" stroke-opacity=".6" stroke-width="2"/>')
    out.append("</g>")
    out.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{C["line"]}"/>')
    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------- pipeline ---
PIPE = [
    ("01", "INGEST", "log-source", "onboarding"),
    ("02", "PARSE", "custom parsers", "& field mapping"),
    ("03", "DETECT", "Sigma · IOAs", "correlation rules"),
    ("04", "TRIAGE", "L2/L3 analysis", "ATT&CK mapping"),
    ("05", "RESPOND", "contain", "eradicate · recover"),
    ("06", "LEARN", "RCA · tuning", "fewer false +ves"),
]


def hexagon(x, y, r):
    pts = []
    for k in range(6):
        a = math.radians(-90 + 60 * k)
        pts.append(f"{f(x + r * math.cos(a))},{f(y + r * math.sin(a))}")
    return " ".join(pts)


def build_pipeline() -> str:
    W, H = 1200, 310
    xs = [120 + i * 192 for i in range(6)]
    y = 168
    T = 6.0
    span = xs[-1] - xs[0]
    css = f"""
.flow{{stroke-dasharray:6 12;animation:flow 1.1s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-18}}}}
.loop{{stroke-dasharray:5 9;animation:loopf 1.4s linear infinite}}
@keyframes loopf{{to{{stroke-dashoffset:-14}}}}
.pk{{animation:pk {T}s linear infinite}}
@keyframes pk{{0%{{transform:translateX(0);opacity:0}}3%{{opacity:1}}97%{{opacity:1}}100%{{transform:translateX({span}px);opacity:0}}}}
.glow{{animation:glow {T / 3}s linear infinite}}
@keyframes glow{{0%{{opacity:1}}45%{{opacity:0}}100%{{opacity:0}}}}
.node{{animation:rise .6s cubic-bezier(.2,.7,.2,1) both}}
"""
    out = [svg_open(
        W, H, "Detection engineering lifecycle",
        "Animated pipeline: Ingest (log-source onboarding) -> Parse (custom parsers) -> Detect "
        "(Sigma, IOAs, correlation rules) -> Triage (L2/L3, MITRE ATT&CK mapping) -> Respond "
        "(contain, eradicate, recover) -> Learn (RCA, tuning), with a feedback loop from Learn "
        "back to Detect.", css)]
    out.append("<defs>"
               f'<linearGradient id="bgP" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b111c"/>'
               f'<stop offset="1" stop-color="{C["bg0"]}"/></linearGradient>'
               '<filter id="gl" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="5"/></filter>'
               '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2" result="b"/>'
               '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
               f'<marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
               f'<path d="M0 0L10 5L0 10z" fill="{C["amber"]}"/></marker>'
               "</defs>")
    out.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#bgP)"/>'
               f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{C["line"]}"/>')
    out.append(mono_text(40, 44, "DETECTION ENGINEERING LIFECYCLE", 14, C["cyan"], extra=' letter-spacing="0"'))
    right = "mapped to MITRE ATT&CK · Cyber Kill Chain · NIST CSF"
    out.append(mono_text(1160 - len(right) * 12.5 * ADV, 44, right, 12.5, C["muted"]))
    # rails
    for i in range(5):
        a, b = xs[i] + 40, xs[i + 1] - 40
        out.append(f'<line x1="{a}" y1="{y}" x2="{b}" y2="{y}" stroke="{C["line"]}" stroke-width="2"/>'
                   f'<line class="flow" x1="{a}" y1="{y}" x2="{b}" y2="{y}" stroke="{C["cyan"]}" '
                   f'stroke-opacity=".75" stroke-width="2"/>')
    # feedback loop LEARN -> DETECT
    lx0, lx1 = xs[5], xs[2]
    out.append(f'<path class="loop" d="M{lx0} {y - 44}C{lx0} {y - 104} {lx1} {y - 104} {lx1} {y - 46}" fill="none" '
               f'stroke="{C["amber"]}" stroke-opacity=".75" stroke-width="1.6" marker-end="url(#arr)"/>')
    lab = "feedback loop · tune rules · cut false positives"
    out.append(mono_text((lx0 + lx1) / 2 - len(lab) * 12 * ADV / 2, y - 58, lab, 12, C["amber"]))
    # packets (behind nodes)
    for k in range(3):
        out.append(f'<g class="pk" style="animation-delay:{f(-k * T / 3)}s">'
                   f'<circle cx="{xs[0]}" cy="{y}" r="5" fill="{C["cyan2"]}" filter="url(#soft)"/></g>')
    for i, (num, title, sub, sub2) in enumerate(PIPE):
        x = xs[i]
        hit = (x - xs[0]) / span * T
        d = (hit % (T / 3)) - T / 3
        out.append(f'<g class="node" style="animation-delay:{f(.15 + i * .12)}s">')
        out.append(f'<polygon class="glow" points="{hexagon(x, y, 40)}" fill="{C["cyan"]}" fill-opacity=".35" '
                   f'filter="url(#gl)" style="animation-delay:{f(d)}s"/>')
        out.append(f'<polygon points="{hexagon(x, y, 36)}" fill="{C["tile"]}" stroke="{C["cyan"]}" stroke-opacity=".7" stroke-width="1.6"/>')
        out.append(f'<polygon points="{hexagon(x, y, 28)}" fill="none" stroke="{C["cyan"]}" stroke-opacity=".22"/>')
        out.append(mono_text(x - 2 * 16 * ADV / 2, y + 6, num, 16, C["cyan2"], extra=' font-weight="700"'))
        out.append(mono_text(x - len(title) * 16 * ADV / 2, y + 74, title, 16, C["text"], extra=' font-weight="700"'))
        out.append(mono_text(x - len(sub) * 12.5 * ADV / 2, y + 98, sub, 12.5, C["muted"]))
        out.append(mono_text(x - len(sub2) * 12.5 * ADV / 2, y + 116, sub2, 12.5, C["muted"]))
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- divider ---
def build_divider() -> str:
    W, H = 1200, 34
    css = """
.pkt{animation:pkt 4.5s cubic-bezier(.5,0,.5,1) infinite}
@keyframes pkt{0%{transform:translateX(0);opacity:0}8%{opacity:1}92%{opacity:1}100%{transform:translateX(1060px);opacity:0}}
"""
    label = "0x4E54"
    lw = len(label) * 12 * ADV + 24
    out = [svg_open(W, H, "section divider", "A thin network line with a data packet travelling across it.", css)]
    out.append(f'<defs><linearGradient id="ln" x1="0" y1="0" x2="1" y2="0">'
               f'<stop offset="0" stop-color="{C["cyan"]}" stop-opacity="0"/>'
               f'<stop offset=".5" stop-color="{C["cyan"]}" stop-opacity=".55"/>'
               f'<stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient>'
               f'<linearGradient id="pg" x1="0" y1="0" x2="1" y2="0">'
               f'<stop offset="0" stop-color="{C["cyan2"]}" stop-opacity="0"/>'
               f'<stop offset="1" stop-color="{C["cyan2"]}"/></linearGradient></defs>')
    out.append(f'<rect x="40" y="16.5" width="{W - 80}" height="1" fill="url(#ln)"/>')
    out.append(f'<g class="pkt"><rect x="40" y="15.5" width="60" height="3" rx="1.5" fill="url(#pg)"/></g>')
    out.append(f'<rect x="{f(600 - lw / 2)}" y="6" width="{f(lw)}" height="22" rx="11" fill="{C["bg0"]}" '
               f'stroke="{C["line"]}"/>')
    out.append(mono_text(600 - len(label) * 12 * ADV / 2, 21.5, label, 12, C["muted"]))
    out.append("</svg>")
    return "".join(out)


# ----------------------------------------------------------------- footer ---
def build_footer() -> str:
    W, H = 1200, 170
    base = 64
    pts = [(40, base)]
    x = 40
    while x < W - 200:
        x += 120
        pts += [(x, base), (x + 10, base - 6), (x + 20, base), (x + 30, base),
                (x + 36, base + 10), (x + 44, base - 42), (x + 52, base + 18), (x + 58, base),
                (x + 74, base), (x + 86, base - 9), (x + 98, base)]
        x += 98
    pts.append((W - 40, base))
    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
    P = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    seg = 220
    css = f"""
.trace{{stroke-dasharray:{seg} {f(P + seg)};animation:ecg 3.8s linear infinite}}
@keyframes ecg{{from{{stroke-dashoffset:{seg}}}to{{stroke-dashoffset:-{f(P)}}}}}
"""
    line1 = "detect early  ·  respond fast  ·  learn always"
    line2 = f"{NAME} · Security Engineer · Chennai, India"
    out = [svg_open(W, H, "footer", f"A heartbeat line above the motto '{line1}'.", css)]
    out.append('<defs><filter id="soft" x="-5%" y="-50%" width="110%" height="200%">'
               '<feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/>'
               '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    out.append(f'<path d="{d}" fill="none" stroke="{C["cyan"]}" stroke-opacity=".2" stroke-width="2"/>')
    out.append(f'<path class="trace" d="{d}" fill="none" stroke="{C["cyan2"]}" stroke-width="2.4" '
               f'stroke-linecap="round" stroke-linejoin="round" filter="url(#soft)"/>')
    out.append(mono_text(600 - len(line1) * 18 * ADV / 2, 122, line1, 18, C["fg"]))
    out.append(f'<text x="600" y="150" class="sans" font-size="13.5" fill="{C["muted"]}" '
               f'text-anchor="middle">{esc(line2)}</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- buttons ---
def _icon(kind, x, y, col):
    if kind == "profile":
        return (f'<rect x="{x}" y="{y}" width="26" height="22" rx="4" fill="none" stroke="{col}" stroke-width="2"/>'
                f'<circle cx="{x + 9}" cy="{y + 9}" r="3.4" fill="{col}"/>'
                f'<path d="M{x + 3.5} {y + 18.5}c1.2-4 9.8-4 11 0" fill="none" stroke="{col}" stroke-width="2"/>'
                f'<path d="M{x + 17} {y + 8}h5M{x + 17} {y + 13}h5" stroke="{col}" stroke-width="2"/>')
    if kind == "globe":
        c = (x + 13, y + 11)
        return (f'<circle cx="{c[0]}" cy="{c[1]}" r="11" fill="none" stroke="{col}" stroke-width="2"/>'
                f'<ellipse cx="{c[0]}" cy="{c[1]}" rx="5" ry="11" fill="none" stroke="{col}" stroke-width="1.6"/>'
                f'<path d="M{x + 2} {y + 11}h22M{x + 4} {y + 5.5}h18M{x + 4} {y + 16.5}h18" stroke="{col}" stroke-width="1.4"/>')
    if kind == "mail":
        return (f'<rect x="{x}" y="{y + 1}" width="26" height="20" rx="3" fill="none" stroke="{col}" stroke-width="2"/>'
                f'<path d="M{x + 1} {y + 3}l12 9 12-9" fill="none" stroke="{col}" stroke-width="2"/>')
    if kind == "shield":
        return (f'<path d="M{x + 13} {y - 1}L{x + 24} {y + 3}V{y + 10}C{x + 24} {y + 17} {x + 19} {y + 21} {x + 13} {y + 23}'
                f'C{x + 7} {y + 21} {x + 2} {y + 17} {x + 2} {y + 10}V{y + 3}Z" '
                f'fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>'
                f'<path d="M{x + 8} {y + 11}l3.6 3.6 6.6-7" fill="none" stroke="{col}" stroke-width="2.2" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "radar":
        return (f'<circle cx="{x + 13}" cy="{y + 11}" r="11" fill="none" stroke="{col}" stroke-width="2"/>'
                f'<circle cx="{x + 13}" cy="{y + 11}" r="5" fill="none" stroke="{col}" stroke-width="1.6"/>'
                f'<path d="M{x + 13} {y + 11}l8-6" stroke="{col}" stroke-width="2"/>')
    return ""


BUTTONS = [  # file, icon, label, sub, accent
    ("btn-linkedin.svg", "profile", "LINKEDIN", "in/nagarajan-t", "blue"),
    ("btn-portfolio.svg", "globe", "PORTFOLIO", "nagarajant37.github.io", "cyan"),
    ("btn-email.svg", "mail", "EMAIL", "say hello", "green"),
    ("btn-sc200.svg", "shield", "SC-200", "Microsoft certified", "violet"),
]


def build_button(icon, label, sub, accent) -> str:
    a = C[accent]
    w = int(70 + max(len(label) * 16 * ADV, len(sub) * 12.5 * ADV) + 26)
    h = 60
    css = f"""
.shine{{animation:shine 5.5s ease-in-out infinite}}
@keyframes shine{{0%,70%{{transform:translateX(-80px)}}100%{{transform:translateX({w + 80}px)}}}}
"""
    out = [svg_open(w, h, f"{label} — {sub}", f"Button: {label} ({sub}).", css)]
    out.append(f'<defs><clipPath id="b"><rect width="{w}" height="{h}" rx="12"/></clipPath>'
               f'<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0">'
               f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".09"/>'
               f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>')
    out.append(f'<g clip-path="url(#b)"><rect width="{w}" height="{h}" fill="{C["tile2"]}"/>'
               f'<rect width="4" height="{h}" fill="{a}"/>'
               f'<g class="shine"><rect x="0" y="0" width="60" height="{h}" fill="url(#sh)" transform="skewX(-20)"/></g></g>')
    out.append(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{C["line"]}"/>')
    out.append(_icon(icon, 22, 19, a))
    out.append(mono_text(64, 28, label, 16, C["text"], extra=' font-weight="700"'))
    out.append(mono_text(64, 47, sub, 12.5, C["muted"]))
    out.append("</svg>")
    return "".join(out)


BUILDERS = {
    "hero.svg": build_hero,
    "whoami.svg": build_whoami,
    "pipeline.svg": build_pipeline,
    "divider.svg": build_divider,
    "footer.svg": build_footer,
}
for _file, _icon_kind, _label, _sub, _acc in BUTTONS:
    BUILDERS[_file] = (lambda i=_icon_kind, l=_label, s=_sub, a=_acc: build_button(i, l, s, a))


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for name, fn in BUILDERS.items():
        svg = fn()
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name}  ({len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
