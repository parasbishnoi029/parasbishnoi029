import urllib.request
import re
import os

USERNAME = "parasbishnoi029"

def update_streak():
    print("--- Fetching Streak Data ---")
    try:
        url = f"https://github-readme-streak-stats.herokuapp.com/?user={USERNAME}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        svg = urllib.request.urlopen(req).read().decode('utf-8')

        # More aggressive regex to catch numbers anywhere in the stat fields
        stats = re.findall(r'<text[^>]*class="stat[^>]*>([^<]+)</text>', svg)
        dates = re.findall(r'<text[^>]*class="stagger[^>]*>([^<]+)</text>', svg)

        print(f"Found Raw Stats: {stats}")
        print(f"Found Raw Dates: {dates}")

        if len(stats) >= 3 and len(dates) >= 3:
            total, current, longest = stats[0].strip(), stats[1].strip(), stats[2].strip()
            total_d, current_d, longest_d = dates[0].strip(), dates[1].strip(), dates[2].strip()
        else:
            raise Exception("Regex did not find enough data fields in the SVG.")
    except Exception as e:
        print(f"FAILED TO FETCH STREAK: {e}")
        total, current, longest = "0", "0", "0"
        total_d, current_d, longest_d = "N/A", "N/A", "N/A"

    try:
        with open('assets/streak-template.svg', 'r', encoding='utf-8') as f:
            data = f.read()

        data = data.replace('{{TOTAL_COMMITS}}', total).replace('{{TOTAL_DATES}}', total_d)
        data = data.replace('{{CURRENT_STREAK}}', current).replace('{{CURRENT_DATES}}', current_d)
        data = data.replace('{{LONGEST_STREAK}}', longest).replace('{{LONGEST_DATES}}', longest_d)

        os.makedirs('assets', exist_ok=True)
        with open('assets/stats-streak.svg', 'w', encoding='utf-8') as f:
            f.write(data)
        print("Streak SVG successfully saved!")
    except Exception as e:
        print(f"FAILED TO SAVE STREAK FILE: {e}")

if __name__ == "__main__":
    update_streak()
    # (Keep your languages function here too)
