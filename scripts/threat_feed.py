#!/usr/bin/env python3
"""Render assets/threat-feed.svg from CISA's Known Exploited Vulnerabilities feed.

    python3 scripts/threat_feed.py              # live data
    python3 scripts/threat_feed.py --file kev.json

Runs daily from .github/workflows/threat-feed.yml. Standard library only.
If every source is unreachable the existing SVG is kept untouched, so the
profile never shows a broken card.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import ADV, ASSETS, BOLD, C, HANDLE, esc, f, mono_text, svg_open, typed, window  # noqa: E402

SOURCES = (
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    "https://raw.githubusercontent.com/cisagov/kev-data/main/known_exploited_vulnerabilities.json",
)
OUT = ASSETS / "threat-feed.svg"
LATEST = 6


def fetch() -> dict:
    last = None
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "kev-watch/1.0 (+https://github.com/Nagarajant37)",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            if data.get("vulnerabilities"):
                print(f"fetched {len(data['vulnerabilities'])} KEVs from {url}")
                return data
        except Exception as e:  # network, HTTP or JSON errors -> try next source
            last = e
            print(f"warn: {url}: {e}", file=sys.stderr)
    raise RuntimeError(f"all KEV sources failed ({last})")


def clip(s: str, n: int) -> str:
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def render(data: dict, today: dt.date) -> str:
    vulns = sorted(data["vulnerabilities"],
                   key=lambda v: (v.get("dateAdded", ""), v.get("cveID", "")), reverse=True)
    rows = vulns[:LATEST]
    total = len(vulns)
    cutoff = (today - dt.timedelta(days=30)).isoformat()
    recent = sum(1 for v in vulns if v.get("dateAdded", "") >= cutoff)
    ransom = sum(1 for v in vulns if str(v.get("knownRansomwareCampaignUse", "")).lower() == "known")

    W = 1200
    fs, cw = 14, 14 * ADV
    head_y, col_y, row0, rh = 82, 152, 176, 40
    H = row0 + len(rows) * rh + 70
    cols = [  # (x, width in chars)
        (32, 10), (32 + 12 * cw, 16), (32 + 30 * cw, 30), (32 + 62 * cw, 50), (32 + 114 * cw, 9),
    ]
    css = f"""
.row{{animation:rise .5s cubic-bezier(.2,.7,.2,1) both}}
.hl{{animation:hl 6s ease-in-out 2.6s infinite both}}
@keyframes hl{{0%{{transform:translateY(0);opacity:0}}8%{{opacity:1}}92%{{opacity:1}}100%{{transform:translateY({(len(rows) - 1) * rh}px);opacity:0}}}}
"""
    desc = ("Live threat feed, refreshed daily from the CISA Known Exploited Vulnerabilities "
            f"catalog ({total} CVEs, {recent} added in the 30 days before {today.isoformat()}). "
            "Latest additions: " + "; ".join(
                f"{v.get('cveID')} {v.get('vendorProject')} {v.get('product')} (added {v.get('dateAdded')})"
                for v in rows) + ".")
    out = [svg_open(W, H, "Live CISA KEV threat feed", desc, css)]
    out.append("<defs>"
               f'<linearGradient id="hlg" x1="0" y1="0" x2="1" y2="0">'
               f'<stop offset="0" stop-color="{C["cyan"]}" stop-opacity="0"/>'
               f'<stop offset=".5" stop-color="{C["cyan"]}" stop-opacity=".07"/>'
               f'<stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient>'
               "</defs>")
    out.append(window(0, 0, W, H, f"{HANDLE}: ~$ kev-watch — CISA Known Exploited Vulnerabilities", "wk"))
    s, t = typed("k1", 32, head_y, [("$ ", C["green"]), (f"kev-watch --source cisa --latest {len(rows)}", C["fg"])],
                 17, begin=.3, per=.04)
    out.append(s)
    upd = f"updated {today.isoformat()}"
    ux = W - 32 - len(upd) * 13 * ADV
    out.append(mono_text(ux, head_y, upd, 13, C["muted"]))
    out.append(f'<circle class="pulse" cx="{f(ux - 66)}" cy="{head_y - 5}" r="5.5" fill="{C["red"]}"/>')
    out.append(mono_text(ux - 54, head_y, "LIVE", 13, C["red"], extra=' font-weight="700"'))
    summary = (f"{total:,} CVEs exploited in the wild  ·  +{recent} in the last 30 days  ·  "
               f"{ransom:,} used in ransomware campaigns")
    out.append(f'<g style="animation:fade .5s {f(t + .1)}s both">'
               f'{mono_text(32, head_y + 34, summary, 13.5, C["muted"])}</g>')
    out.append(f'<line x1="24" y1="{col_y + 12}" x2="{W - 24}" y2="{col_y + 12}" stroke="{C["line"]}"/>')
    for (x, _), label in zip(cols, ("DATE ADDED", "CVE", "VENDOR / PRODUCT", "VULNERABILITY", "RANSOMWARE")):
        out.append(mono_text(x, col_y, label, 12, C["dim"]))
    out.append(f'<rect class="hl" x="24" y="{row0 - 6}" width="{W - 48}" height="{rh - 8}" rx="6" fill="url(#hlg)"/>')
    for i, v in enumerate(rows):
        y = row0 + i * rh
        d = t + .3 + i * .16
        known = str(v.get("knownRansomwareCampaignUse", "")).lower() == "known"
        out.append(f'<g class="row" style="animation-delay:{f(d)}s">')
        if i % 2 == 0:
            out.append(f'<rect x="24" y="{y - 6}" width="{W - 48}" height="{rh - 8}" rx="6" fill="{C["tile"]}" fill-opacity=".7"/>')
        yy = y + 19
        vp = f"{v.get('vendorProject', '')} · {v.get('product', '')}"
        cells = (
            (v.get("dateAdded", ""), C["muted"], ""),
            (v.get("cveID", ""), C["amber"], ' font-weight="700"'),
            (clip(vp, cols[2][1]), C["text"], ""),
            (clip(v.get("vulnerabilityName", ""), cols[3][1]), C["fg"], ' opacity=".85"'),
        )
        for (x, n), (txt, col, extra) in zip(cols, cells):
            out.append(mono_text(x, yy, clip(txt, n), fs, col, extra=extra))
        bx = cols[4][0]
        if known:
            out.append(f'<rect x="{f(bx - 6)}" y="{yy - 15}" width="{f(5 * 12 * ADV + 14)}" height="21" rx="10.5" '
                       f'fill="{C["red"]}" fill-opacity=".14" stroke="{C["red"]}" stroke-opacity=".55"/>'
                       f'{mono_text(bx + 1, yy, "KNOWN", 12, C["red"], extra=BOLD)}')
        else:
            out.append(mono_text(bx + 1, yy, "unknown", 12, C["dim"]))
        out.append("</g>")
    fy = H - 26
    out.append(f'<line x1="0" y1="{H - 50}" x2="{W}" y2="{H - 50}" stroke="{C["line"]}"/>')
    foot = "# refreshed daily by GitHub Actions  ·  source: cisa.gov/known-exploited-vulnerabilities-catalog"
    out.append(mono_text(32, fy, foot, 13, C["muted"]))
    out.append("</svg>")
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="read KEV JSON from a local file instead of the network")
    ap.add_argument("--date", help="override today's date (YYYY-MM-DD), for testing")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(dt.timezone.utc).date()
    try:
        data = json.loads(Path(a.file).read_text(encoding="utf-8")) if a.file else fetch()
    except Exception as e:
        print(f"::warning::threat feed not refreshed: {e}")
        return 0  # keep the last good SVG
    svg = render(data, today)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ASSETS.parent)} ({len(svg) / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
