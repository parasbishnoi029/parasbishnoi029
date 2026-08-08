import urllib.request
import re
import os

USERNAME = "parasbishnoi029"

def update_streak():
    print("--- Fetching Streak Data ---")
    try:
        # UPDATED TO THE STABLE DEMOLAB SERVER!
        url = f"https://streak-stats.demolab.com/?user={USERNAME}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        svg = urllib.request.urlopen(req).read().decode('utf-8')

        # Improved regex to ignore accidental spaces
        stats = re.findall(r'<text[^>]*class="stat[^>]*>\s*([^<]+?)\s*</text>', svg)
        dates = re.findall(r'<text[^>]*class="stagger[^>]*>\s*([^<]+?)\s*</text>', svg)

        print(f"DEBUG - Found Stats: {stats}")
        print(f"DEBUG - Found Dates: {dates}")

        if len(stats) >= 3 and len(dates) >= 3:
            total, current, longest = stats[0], stats[1], stats[2]
            total_d, current_d, longest_d = dates[0], dates[1], dates[2]
        else:
            raise Exception("Regex did not find the expected 3 numbers in the SVG.")
            
    except Exception as e:
        print(f"❌ FAILED TO FETCH STREAK: {e}")
        total, current, longest = "ERROR", "ERROR", "ERROR"
        total_d, current_d, longest_d = "ERROR", "ERROR", "ERROR"

    try:
        with open('assets/streak-template.svg', 'r', encoding='utf-8') as f:
            data = f.read()

        data = data.replace('{{TOTAL_COMMITS}}', total).replace('{{TOTAL_DATES}}', total_d)
        data = data.replace('{{CURRENT_STREAK}}', current).replace('{{CURRENT_DATES}}', current_d)
        data = data.replace('{{LONGEST_STREAK}}', longest).replace('{{LONGEST_DATES}}', longest_d)

        os.makedirs('assets', exist_ok=True)
        with open('assets/stats-streak.svg', 'w', encoding='utf-8') as f:
            f.write(data)
        print("✅ Streak SVG successfully saved!")
    except Exception as e:
        print(f"❌ FAILED TO SAVE STREAK FILE: {e}")

# ... (Keep your update_languages function down here as it was) ...

if __name__ == "__main__":
    update_streak()
    # update_languages() # Un-comment if you are running languages too
