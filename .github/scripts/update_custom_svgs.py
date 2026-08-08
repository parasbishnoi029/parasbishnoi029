"""
Injects real GitHub stats (streak + top languages) into custom SVG templates.

Key differences from the original version:
  - Retries each upstream fetch a few times before giving up (the public
    streak-stats.demolab.com / github-readme-stats.vercel.app instances are
    shared and frequently rate-limited or return an error card).
  - Detects when the upstream response is an *error* card instead of a real
    stats card (no data-testid attributes present) and treats that as a
    failed fetch rather than "0 contributions".
  - On failure, the existing assets/stats-*.svg files are left untouched
    instead of being overwritten with zeros/blanks, so your profile never
    regresses to a broken-looking card just because an upstream service
    hiccuped.
  - Fails the job (non-zero exit) when a fetch could not be completed after
    retries, so the Action run shows red instead of a misleading green
    check. Set FAIL_ON_ERROR = False below if you'd rather it stay green
    and just skip the update.
"""

import os
import re
import time
import urllib.error
import urllib.request

USERNAME = "parasbishnoi029"

# How many times to retry a failed/errored fetch before giving up.
MAX_RETRIES = 3
# Seconds to wait between retries (grows a little each attempt).
RETRY_BACKOFF_SECONDS = 5
# If True, the script exits with a non-zero status when a fetch ultimately
# fails, so the GitHub Actions run is marked failed/red instead of green.
FAIL_ON_ERROR = True

HEADERS = {"User-Agent": "Mozilla/5.0"}


class FetchFailed(Exception):
    """Raised when we could not get usable data after all retries."""


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def fetch_with_retry(url: str, validate):
    """
    Fetch `url`, retrying on network errors and on responses that fail
    `validate(svg) -> bool` (used to detect error cards that returned
    HTTP 200 but no real stats).
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            svg = _http_get(url)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_error = e
            print(f"  attempt {attempt}/{MAX_RETRIES} network error: {e}")
        else:
            if validate(svg):
                return svg
            last_error = "response did not look like a valid stats card"
            print(f"  attempt {attempt}/{MAX_RETRIES} got a response but it "
                  f"failed validation (likely an upstream error card)")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise FetchFailed(f"giving up on {url}: {last_error}")


def _looks_like_streak_card(svg: str) -> bool:
    return 'data-testid="total-contributions"' in svg


def _looks_like_langs_card(svg: str) -> bool:
    return 'data-testid="lang-name"' in svg


def update_streak():
    print("--- Fetching Streak Data ---")
    url = f"https://streak-stats.demolab.com/?user={USERNAME}&disable_animations=true"

    try:
        svg = fetch_with_retry(url, _looks_like_streak_card)
    except FetchFailed as e:
        print(f"❌ FAILED TO FETCH STREAK after {MAX_RETRIES} attempts: {e}")
        print("↪️  Leaving assets/stats-streak.svg untouched.")
        if FAIL_ON_ERROR:
            raise
        return

    total_m = re.search(r'data-testid="total-contributions"[^>]*>\s*([^<]+?)\s*<', svg)
    current_m = re.search(r'data-testid="current-streak"[^>]*>\s*([^<]+?)\s*<', svg)
    longest_m = re.search(r'data-testid="longest-streak"[^>]*>\s*([^<]+?)\s*<', svg)

    total_d_m = re.search(r'data-testid="total-contributions-dates"[^>]*>\s*([^<]+?)\s*<', svg)
    current_d_m = re.search(r'data-testid="current-streak-dates"[^>]*>\s*([^<]+?)\s*<', svg)
    longest_d_m = re.search(r'data-testid="longest-streak-dates"[^>]*>\s*([^<]+?)\s*<', svg)

    # At this point _looks_like_streak_card already confirmed the card is
    # real, so missing individual fields would be a genuine template change
    # upstream worth knowing about rather than a rate limit — still guard
    # against overwriting with blanks in that edge case.
    if not (total_m and current_m and longest_m):
        print("❌ Card looked valid but one of the three numbers is missing "
              "(upstream template may have changed). Leaving file untouched.")
        if FAIL_ON_ERROR:
            raise FetchFailed("streak card fields missing after validation")
        return

    total, current, longest = total_m.group(1), current_m.group(1), longest_m.group(1)
    total_d = total_d_m.group(1) if total_d_m else "N/A"
    current_d = current_d_m.group(1) if current_d_m else "N/A"
    longest_d = longest_d_m.group(1) if longest_d_m else "N/A"

    print(f"DEBUG - Found: Total({total}), Current({current}), Longest({longest})")

    try:
        with open("assets/streak-template.svg", "r", encoding="utf-8") as f:
            data = f.read()

        data = data.replace("{{TOTAL_COMMITS}}", total).replace("{{TOTAL_DATES}}", total_d)
        data = data.replace("{{CURRENT_STREAK}}", current).replace("{{CURRENT_DATES}}", current_d)
        data = data.replace("{{LONGEST_STREAK}}", longest).replace("{{LONGEST_DATES}}", longest_d)

        os.makedirs("assets", exist_ok=True)
        with open("assets/stats-streak.svg", "w", encoding="utf-8") as f:
            f.write(data)
        print("✅ Streak SVG successfully saved!")
    except Exception as e:
        print(f"❌ FAILED TO SAVE STREAK FILE: {e}")
        if FAIL_ON_ERROR:
            raise


def update_languages():
    print("--- Fetching Language Data ---")
    url = (
        f"https://github-readme-stats.vercel.app/api/top-langs/"
        f"?username={USERNAME}&langs_count=6&layout=compact"
    )

    try:
        svg = fetch_with_retry(url, _looks_like_langs_card)
    except FetchFailed as e:
        print(f"❌ FAILED TO FETCH LANGUAGES after {MAX_RETRIES} attempts: {e}")
        print("↪️  Leaving assets/stats-languages.svg untouched.")
        if FAIL_ON_ERROR:
            raise
        return

    colors = re.findall(r'<circle[^>]*fill="([^"]+)"[^>]*/>', svg)
    names = re.findall(r'<text data-testid="lang-name"[^>]*>([^<]+)</text>', svg)
    percents = re.findall(r'<text data-testid="lang-progress"[^>]*>([\d.]+)%</text>', svg)

    if not names:
        print("❌ Card looked valid but no language names were parsed out of it "
              "(upstream template may have changed). Leaving file untouched.")
        if FAIL_ON_ERROR:
            raise FetchFailed("language card fields missing after validation")
        return

    print(f"DEBUG - Found {len(names)} language(s): {', '.join(names)}")

    try:
        with open("assets/languages-template.svg", "r", encoding="utf-8") as f:
            data = f.read()

        top_x = 0.0
        for i in range(6):
            if i < len(names):
                name, color, pct_str = names[i], colors[i], percents[i]
                pct_float = float(pct_str)
            else:
                name, color, pct_str, pct_float = "", "#000000", "0.0", 0.0

            bar_width = 460.0 * (pct_float / 100.0)
            anim_width = 180.0 * (pct_float / 100.0)

            data = data.replace(f"{{{{LANG{i+1}_NAME}}}}", name)
            data = data.replace(f"{{{{LANG{i+1}_COLOR}}}}", color)
            data = data.replace(f"{{{{LANG{i+1}_PERCENT}}}}", f"{pct_str}%")
            data = data.replace(f"{{{{LANG{i+1}_X}}}}", f"{top_x:.2f}")
            data = data.replace(f"{{{{LANG{i+1}_BAR_WIDTH}}}}", f"{bar_width:.2f}")
            data = data.replace(f"{{{{LANG{i+1}_ANIM_WIDTH}}}}", f"{anim_width:.2f}")

            top_x += bar_width

        with open("assets/stats-languages.svg", "w", encoding="utf-8") as f:
            f.write(data)
        print("✅ Languages SVG updated!")
    except Exception as e:
        print(f"❌ FAILED TO SAVE LANGUAGES: {e}")
        if FAIL_ON_ERROR:
            raise


if __name__ == "__main__":
    errors = []
    for step in (update_streak, update_languages):
        try:
            step()
        except FetchFailed as e:
            errors.append(str(e))

    if errors and FAIL_ON_ERROR:
        print("\n--- Summary: one or more updates failed, failing the job ---")
        for e in errors:
            print(f" - {e}")
        raise SystemExit(1)
