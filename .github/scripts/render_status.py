"""
Runs inside GitHub Actions. Fetches the most recent public PushEvent for
the user and renders it as a small status-bar SVG. Requires: STATS_TOKEN
with at least public read access, and `requests` (pip install requests).
"""
import os
import sys
import html
import requests
from datetime import datetime, timezone

USERNAME = "parasbishnoi029"
TOKEN = os.environ.get("STATS_TOKEN", "")

headers = {"Accept": "application/vnd.github+json"}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

resp = requests.get(
    f"https://api.github.com/users/{USERNAME}/events/public",
    headers=headers,
    timeout=15,
)
resp.raise_for_status()
events = resp.json()

push = next((e for e in events if e.get("type") == "PushEvent"), None)

if push is None:
    repo_name = "no recent public pushes"
    message = "—"
    when_text = ""
else:
    repo_name = push["repo"]["name"].split("/")[-1]
    commits = push.get("payload", {}).get("commits", [])
    message = commits[-1]["message"].splitlines()[0] if commits else "(no message)"
    created = datetime.strptime(push["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - created
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        when_text = "just now"
    elif hours < 24:
        when_text = f"{hours}h ago"
    else:
        when_text = f"{hours // 24}d ago"

message = message[:60] + ("…" if len(message) > 60 else "")
message = html.escape(message)
repo_name = html.escape(repo_name)

svg = f'''<svg viewBox="0 0 720 56" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bar" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e1b4b"/>
    </linearGradient>
  </defs>
  <rect width="720" height="56" rx="10" fill="url(#bar)"/>
  <circle cx="26" cy="28" r="6" fill="#22c55e">
    <animate attributeName="opacity" values="1;0.35;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  <text x="44" y="23" font-family="Fira Code, monospace" font-size="11"
        letter-spacing="2" fill="#a855f7">LAST SHIPPED</text>
  <text x="44" y="41" font-family="Fira Code, monospace" font-size="13" fill="#f8fafc">
    <tspan fill="#4ade80">{repo_name}</tspan> — {message}
  </text>
  <text x="700" y="32" font-family="Fira Code, monospace" font-size="11"
        fill="#94a3b8" text-anchor="end">{when_text}</text>
</svg>'''

os.makedirs("assets", exist_ok=True)
with open("assets/status-bar.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Rendered status bar: {repo_name} — {message} ({when_text})")
