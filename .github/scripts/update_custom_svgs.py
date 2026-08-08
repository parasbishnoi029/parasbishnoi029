import urllib.request
import re
import os

# 1. FETCH THE REAL DATA FROM THE STANDARD STREAK TOOL
username = "parasbishnoi029" # Put your username here
url = f"https://github-readme-streak-stats.herokuapp.com/?user={username}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(req).read().decode('utf-8')

# 2. EXTRACT THE NUMBERS USING REGEX
# (This finds the numbers inside the standard SVG that the tool generates)
try:
    total_commits = re.search(r'Total Contributions.*?<text[^>]*>([\d,]+)</text>', response, re.DOTALL).group(1)
    current_streak = re.search(r'Current Streak.*?<text[^>]*>([\d,]+)</text>', response, re.DOTALL).group(1)
    longest_streak = re.search(r'Longest Streak.*?<text[^>]*>([\d,]+)</text>', response, re.DOTALL).group(1)
except Exception as e:
    print("Error parsing stats, using fallbacks.", e)
    total_commits, current_streak, longest_streak = "0", "0", "0"

print(f"Found Stats -> Total: {total_commits}, Current: {current_streak}, Longest: {longest_streak}")

# 3. OPEN YOUR BEAUTIFUL CUSTOM TEMPLATE
with open('templates/streak-template.svg', 'r', encoding='utf-8') as file:
    template_data = file.read()

# 4. REPLACE THE PLACEHOLDERS WITH REAL DATA
template_data = template_data.replace('{{TOTAL_COMMITS}}', total_commits)
template_data = template_data.replace('{{CURRENT_STREAK}}', current_streak)
template_data = template_data.replace('{{LONGEST_STREAK}}', longest_streak)

# 5. SAVE THE FINAL FILE TO YOUR ASSETS FOLDER
os.makedirs('assets', exist_ok=True)
with open('assets/stats-streak.svg', 'w', encoding='utf-8') as file:
    file.write(template_data)

print("Custom Streak SVG successfully updated!")
