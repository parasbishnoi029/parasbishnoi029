import re
import os
import urllib.request

USERNAME = "parasbishnoi029"

def update_streak():
    print("--- Extracting Streak Data from Local File ---")
    try:
        # Ensure the file actually exists
        if not os.path.exists('assets/temp-streak.svg'):
            raise Exception("temp-streak.svg does not exist! The GitHub Action failed to download it.")

        with open('assets/temp-streak.svg', 'r', encoding='utf-8') as f:
            svg = f.read()

        # Bulletproof regex that finds any class containing 'stat'
        stats = re.findall(r'<text[^>]*class="[^"]*stat[^"]*"[^>]*>\s*([^<]+?)\s*</text>', svg)
        dates_raw = re.findall(r'<text[^>]*class="[^"]*stagger[^"]*"[^>]*>\s*([^<]+?)\s*</text>', svg)

        print(f"DEBUG Stats Found: {stats}")

        if len(stats) >= 3:
            total, current, longest = stats[0].strip(), stats[1].strip(), stats[2].strip()
        else:
            raise Exception("Could not find the 3 numbers in the local SVG.")
            
        # Safely extract the dates by looking for date-like characters
        dates = [d for d in dates_raw if "-" in d or "Present" in d or "," in d]
        if len(dates) >= 3:
            total_d, current_d, longest_d = dates[0].strip(), dates[1].strip(), dates[2].strip()
        else:
            total_d, current_d, longest_d = "N/A", "N/A", "N/A"

    except Exception as e:
        print(f"❌ FAILED TO EXTRACT STREAK: {e}")
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

# ... (Keep your update_languages() function exactly as it was) ...

if __name__ == "__main__":
    update_streak()
    # update_languages()
