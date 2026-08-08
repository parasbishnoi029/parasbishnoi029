"""
Computes streak + top-language stats directly from GitHub's own GraphQL API
(no streak-stats.demolab.com, no github-readme-stats.vercel.app, no
third-party Action at all) and injects them into the existing custom
animated SVG templates.

Needs only the GITHUB_TOKEN that GitHub Actions already provides.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

USERNAME = os.environ.get("GH_USERNAME", "parasbishnoi029")
TOKEN = os.environ.get("GITHUB_TOKEN")

GRAPHQL_URL = "https://api.github.com/graphql"


def graphql(query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": USERNAME,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GraphQL HTTP error {e.code}: {e.read().decode('utf-8', 'ignore')}")

    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------

CREATED_AT_QUERY = """
query($login: String!) {
  user(login: $login) { createdAt }
}
"""

CALENDAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


def fetch_all_contribution_days() -> dict:
    """Returns {date_str: contribution_count} for the account's entire history."""
    data = graphql(CREATED_AT_QUERY, {"login": USERNAME})
    created_at = datetime.fromisoformat(data["user"]["createdAt"].replace("Z", "+00:00"))
    start_year = created_at.year

    today = datetime.utcnow()
    days = {}

    year = start_year
    while year <= today.year:
        window_from = datetime(year, 1, 1)
        window_to = min(datetime(year, 12, 31, 23, 59, 59), today)
        if window_from > today:
            break

        data = graphql(
            CALENDAR_QUERY,
            {
                "login": USERNAME,
                "from": window_from.isoformat() + "Z",
                "to": window_to.isoformat() + "Z",
            },
        )
        weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for week in weeks:
            for day in week["contributionDays"]:
                days[day["date"]] = day["contributionCount"]

        year += 1

    return days


def compute_streaks(days: dict):
    sorted_dates = sorted(days.keys())
    total = sum(days.values())

    # Longest streak: longest run of consecutive calendar days with count > 0.
    longest = 0
    longest_start = longest_end = None
    run = 0
    run_start = None
    prev_date = None
    for d_str in sorted_dates:
        d = date.fromisoformat(d_str)
        contiguous = prev_date is not None and (d - prev_date).days == 1
        if days[d_str] > 0:
            if run == 0 or not contiguous:
                run_start = d
            run += 1
            if run > longest:
                longest = run
                longest_start, longest_end = run_start, d
        else:
            run = 0
        prev_date = d

    # Current streak: walk backwards from today (or yesterday, if today has
    # no contribution yet) while contributions continue.
    today = date.today()
    cursor = today if days.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)

    current = 0
    current_end = cursor
    while days.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    current_start = cursor + timedelta(days=1) if current > 0 else None

    def fmt(d):
        return d.strftime("%b %-d, %Y") if d else "N/A"

    return {
        "total": str(total),
        "total_dates": f"{fmt(date.fromisoformat(sorted_dates[0]))} - {fmt(date.fromisoformat(sorted_dates[-1]))}" if sorted_dates else "N/A",
        "current": str(current),
        "current_dates": f"{fmt(current_start)} - {fmt(current_end)}" if current else "N/A",
        "longest": str(longest),
        "longest_dates": f"{fmt(longest_start)} - {fmt(longest_end)}" if longest else "N/A",
    }


def update_streak_svg(stats: dict):
    with open("assets/streak-template.svg", "r", encoding="utf-8") as f:
        template = f.read()

    template = template.replace("{{TOTAL_COMMITS}}", stats["total"]).replace("{{TOTAL_DATES}}", stats["total_dates"])
    template = template.replace("{{CURRENT_STREAK}}", stats["current"]).replace("{{CURRENT_DATES}}", stats["current_dates"])
    template = template.replace("{{LONGEST_STREAK}}", stats["longest"]).replace("{{LONGEST_DATES}}", stats["longest_dates"])

    os.makedirs("assets", exist_ok=True)
    with open("assets/stats-streak.svg", "w", encoding="utf-8") as f:
        f.write(template)
    print(f"✅ Streak SVG updated — total={stats['total']} current={stats['current']} longest={stats['longest']}")


# ---------------------------------------------------------------------------
# Top languages
# ---------------------------------------------------------------------------

LANGUAGES_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(
      first: 50
      after: $cursor
      ownerAffiliations: [OWNER]
      isFork: false
      privacy: PUBLIC
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        languages(first: 10, orderBy: { field: SIZE, direction: DESC }) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
  }
}
"""


def fetch_top_languages(max_pages: int = 4):
    totals = {}   # name -> bytes
    colors = {}   # name -> hex color
    cursor = None

    for _ in range(max_pages):
        data = graphql(LANGUAGES_QUERY, {"login": USERNAME, "cursor": cursor})
        repos = data["user"]["repositories"]
        for repo in repos["nodes"]:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                totals[name] = totals.get(name, 0) + edge["size"]
                colors[name] = edge["node"]["color"] or "#000000"

        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    total_bytes = sum(totals.values()) or 1
    return [
        {"name": name, "color": colors[name], "percent": (size / total_bytes) * 100}
        for name, size in ranked[:6]
    ]


def update_languages_svg(langs: list):
    with open("assets/languages-template.svg", "r", encoding="utf-8") as f:
        template = f.read()

    top_x = 0.0
    for i in range(6):
        if i < len(langs):
            lang = langs[i]
            name, color, pct = lang["name"], lang["color"], lang["percent"]
        else:
            name, color, pct = "", "#000000", 0.0

        bar_width = 460.0 * (pct / 100.0)
        anim_width = 180.0 * (pct / 100.0)

        template = template.replace(f"{{{{LANG{i+1}_NAME}}}}", name)
        template = template.replace(f"{{{{LANG{i+1}_COLOR}}}}", color)
        template = template.replace(f"{{{{LANG{i+1}_PERCENT}}}}", f"{pct:.1f}%")
        template = template.replace(f"{{{{LANG{i+1}_X}}}}", f"{top_x:.2f}")
        template = template.replace(f"{{{{LANG{i+1}_BAR_WIDTH}}}}", f"{bar_width:.2f}")
        template = template.replace(f"{{{{LANG{i+1}_ANIM_WIDTH}}}}", f"{anim_width:.2f}")

        top_x += bar_width

    with open("assets/stats-languages.svg", "w", encoding="utf-8") as f:
        f.write(template)
    print(f"✅ Languages SVG updated — {', '.join(l['name'] for l in langs)}")


if __name__ == "__main__":
    if not TOKEN:
        print("❌ GITHUB_TOKEN is not set in the environment.")
        sys.exit(1)

    try:
        print("--- Computing streak from GitHub's own contribution calendar ---")
        days = fetch_all_contribution_days()
        stats = compute_streaks(days)
        update_streak_svg(stats)
    except Exception as e:
        print(f"❌ FAILED TO COMPUTE STREAK: {e}")
        sys.exit(1)

    try:
        print("--- Computing top languages from your repositories ---")
        langs = fetch_top_languages()
        update_languages_svg(langs)
    except Exception as e:
        print(f"❌ FAILED TO COMPUTE LANGUAGES: {e}")
        sys.exit(1)
