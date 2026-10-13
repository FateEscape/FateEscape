"""Erzeugt assets/languages.svg aus den Sprachdaten aller eigenen Repos (inkl. privater).

Token: Umgebungsvariable GH_TOKEN, sonst `gh auth token`.
"""
import json
import os
import subprocess
import urllib.request
from pathlib import Path

USER = "FateEscape"
EXCLUDE = {"Dockerfile", "Shell", "Batchfile", "PowerShell", "Makefile"}
MAX_LANGS = 8
OUT = Path(__file__).resolve().parent.parent / "assets" / "languages.svg"

COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Java": "#b07219",
    "Python": "#3572A5", "C#": "#178600", "C++": "#f34b7d", "HTML": "#e34c26",
    "CSS": "#663399", "SCSS": "#c6538c", "Go": "#00ADD8", "Rust": "#dea584",
    "Kotlin": "#A97BFF", "PHP": "#4F5D95", "Vue": "#41b883", "Svelte": "#ff3e00",
}


def token():
    return os.environ.get("GH_TOKEN") or subprocess.check_output(["gh", "auth", "token"], text=True).strip()


def api(url, tok):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def collect():
    tok = token()
    totals, page = {}, 1
    while True:
        repos = api(f"https://api.github.com/user/repos?affiliation=owner&per_page=100&page={page}", tok)
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo["owner"]["login"] != USER:
                continue
            for lang, size in api(repo["languages_url"], tok).items():
                if lang not in EXCLUDE:
                    totals[lang] = totals.get(lang, 0) + size
        page += 1
    return totals


def render(totals):
    total = sum(totals.values())
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:MAX_LANGS]
    width, bar_x, bar_w = 350, 25, 300

    segments, x = [], bar_x
    for lang, size in top:
        w = bar_w * size / total
        segments.append(f'<rect x="{x:.2f}" y="0" width="{w:.2f}" height="8" fill="{COLORS.get(lang, "#8b949e")}"/>')
        x += w

    items = []
    for i, (lang, size) in enumerate(top):
        col, row = i % 2, i // 2
        ix, iy = 25 + col * 160, 100 + row * 25
        items.append(
            f'<g transform="translate({ix},{iy})" class="item" style="animation-delay:{0.3 + i * 0.1:.1f}s">'
            f'<circle cx="5" cy="-4" r="5" fill="{COLORS.get(lang, "#8b949e")}"/>'
            f'<text x="16" y="0" class="lang">{lang} {100 * size / total:.1f}%</text></g>'
        )

    height = 100 + ((len(top) + 1) // 2) * 25
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
.title {{ font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #22d3ee; animation: fade .8s ease-in-out forwards; }}
.lang {{ font: 400 12px 'Segoe UI', Ubuntu, sans-serif; fill: #38bdae; }}
.item {{ opacity: 0; animation: fade .3s ease-in-out forwards; }}
.bar {{ animation: grow 1s ease-in-out forwards; transform-origin: {bar_x}px 0; transform: scaleX(0); }}
@keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
</style>
<text x="25" y="35" class="title">Meistgenutzte Sprachen</text>
<clipPath id="r"><rect x="{bar_x}" y="0" width="{bar_w}" height="8" rx="5"/></clipPath>
<g transform="translate(0,58)"><g clip-path="url(#r)"><g class="bar">{"".join(segments)}</g></g></g>
{"".join(items)}
</svg>
'''


if __name__ == "__main__":
    data = collect()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(data), encoding="utf-8")
    for lang, size in sorted(data.items(), key=lambda kv: kv[1], reverse=True):
        print(f"{lang:12} {size:>9}")
