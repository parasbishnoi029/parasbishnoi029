import re
import os
import urllib.request

USERNAME = "parasbishnoi029"

def update_streak():
    print("--- Extracting Streak Data from Local File ---")
    try:
        # Read the temporary file we safely generated in the YAML step
        with open('assets/temp-streak.svg', 'r', encoding='utf-8') as f:
            svg = f.read()

        # Extract the numbers from the local file
        stats = re.findall(r'<text[^>]*class="stat[^>]*>\s*([^<]+?)\s*</text>', svg)
        dates = re.findall(r'<text[^>]*class="stagger[^>]*>\s*([^<]+?)\s*</text>', svg)

        if len(stats) >= 3 and len(dates) >= 3:
            total, current, longest = stats[0], stats[1], stats[2]
            total_d, current_d, longest_d = dates[0], dates[1], dates[2]
        else:
            raise Exception("Regex did not find the numbers in the temporary SVG.")
            
    except Exception as e:
        print(f"❌ FAILED TO EXTRACT STREAK: {e}")
        total, current, longest = "ERROR", "ERROR", "ERROR"
        total_d, current_d, longest_d = "ERROR", "ERROR", "ERROR"

    # Open your custom beautiful template
    try:
        with open('assets/streak-template.svg', 'r', encoding='utf-8') as f:
            data = f.read()

        data = data.replace('{{TOTAL_COMMITS}}', total).replace('{{TOTAL_DATES}}', total_d)
        data = data.replace('{{CURRENT_STREAK}}', current).replace('{{CURRENT_DATES}}', current_d)
        data = data.replace('{{LONGEST_STREAK}}', longest).replace('{{LONGEST_DATES}}', longest_d)

        # Save the final masterpiece
        os.makedirs('assets', exist_ok=True)
        with open('assets/stats-streak.svg', 'w', encoding='utf-8') as f:
            f.write(data)
        print("✅ Streak SVG successfully saved!")
    except Exception as e:
        print(f"❌ FAILED TO SAVE STREAK FILE: {e}")


def update_languages():
    print("--- Fetching Language Data ---")
    try:
        url = f"https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&langs_count=6&layout=compact"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        svg = urllib.request.urlopen(req).read().decode('utf-8')

        colors = re.findall(r'<circle[^>]*fill="([^"]+)"[^>]*/>', svg)
        names = re.findall(r'<text data-testid="lang-name"[^>]*>([^<]+)</text>', svg)
        percents = re.findall(r'<text data-testid="lang-progress"[^>]*>([\d.]+)%</text>', svg)
    except Exception as e:
        print(f"Error fetching languages: {e}")
        return

    try:
        with open('assets/languages-template.svg', 'r', encoding='utf-8') as f:
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

            data = data.replace(f'{{{{LANG{i+1}_NAME}}}}', name)
            data = data.replace(f'{{{{LANG{i+1}_COLOR}}}}', color)
            data = data.replace(f'{{{{LANG{i+1}_PERCENT}}}}', f"{pct_str}%")
            data = data.replace(f'{{{{LANG{i+1}_X}}}}', f"{top_x:.2f}")
            data = data.replace(f'{{{{LANG{i+1}_BAR_WIDTH}}}}', f"{bar_width:.2f}")
            data = data.replace(f'{{{{LANG{i+1}_ANIM_WIDTH}}}}', f"{anim_width:.2f}")

            top_x += bar_width

        with open('assets/stats-languages.svg', 'w', encoding='utf-8') as f:
            f.write(data)
        print("✅ Languages SVG updated!")
    except Exception as e:
        print(f"❌ FAILED TO SAVE LANGUAGES: {e}")

if __name__ == "__main__":
    update_streak()
    update_languages()
