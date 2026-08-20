#!/usr/bin/env python3
"""Generate a self-hosted GitHub stats SVG for the profile README.
No third-party servers. Reads the GitHub API directly and writes metrics.svg
into the repo root so the README can embed it from the same repo."""
import base64
import json
import os
import urllib.request

USER = os.environ.get("USER", "SNNN-011")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"


def api(path):
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-metrics")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def get_all(path):
    out, page = [], 1
    while True:
        data = api(f"{path}?per_page=100&page={page}")
        if not data:
            break
        out.extend(data)
        if len(data) < 100:
            break
        page += 1
    return out


# ---- gather data ----
user = api(f"/users/{USER}")
repos = get_all(f"/users/{USER}/repos")
repos = [r for r in repos if not r.get("fork")]
public = user.get("public_repos", 0)
followers = user.get("followers", 0)
following = user.get("following", 0)

langs = {}
for r in repos:
    lang = r.get("language")
    if lang:
        langs[lang] = langs.get(lang, 0) + 1
top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:8]

total_stars = sum(r.get("stargazers_count", 0) for r in repos)
total_forks = sum(r.get("forks_count", 0) for r in repos)

# contribution count (last year) via search
try:
    c = api(f'/search/commits?q=author:{USER}')  # needs no special scope for count field
    commits = c.get("total_count", 0)
except Exception:
    commits = 0

# ---- build SVG ----
W, H = 460, 220
rows = [
    ("Public repos", str(public)),
    ("Followers", str(followers)),
    ("Following", str(following)),
    ("Total stars", str(total_stars)),
    ("Total forks", str(total_forks)),
    ("Commits (1y)", str(commits)),
]
lang_line = "  ·  ".join(f"{k} ({v})" for k, v in top_langs) or "—"
lang_line = (lang_line[:72] + "…") if len(lang_line) > 72 else lang_line

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
svg.append(f'<rect width="{W}" height="{H}" rx="14" fill="#0d1117" stroke="#30363d"/>')
svg.append(f'<text x="20" y="34" fill="#58a6ff" font-family="Fira Code,monospace" font-size="18" font-weight="bold">📊 {USER} stats</text>')
y = 70
for label, val in rows:
    svg.append(f'<text x="20" y="{y}" fill="#8b949e" font-family="monospace" font-size="14">{label}</text>')
    svg.append(f'<text x="{W-20}" y="{y}" fill="#c9d1d9" font-family="monospace" font-size="14" text-anchor="end" font-weight="bold">{val}</text>')
    y += 24
svg.append(f'<text x="20" y="{H-16}" fill="#7ee787" font-family="monospace" font-size="12">top langs: {lang_line}</text>')
svg.append('</svg>')

with open("metrics.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("metrics.svg written")
