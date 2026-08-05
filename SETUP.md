# Setup guide

## 1. Create the special profile repository

Create a **public** GitHub repository named exactly `parasbishnoi029`. GitHub only displays this README as the profile README when the owner name and repository name match exactly.

Copy this package into that repository, commit, and push to the `main` branch.

## 2. Replace the deliberate placeholders

Before publishing, edit `README.md` and replace:

- `YOUR_EMAIL`
- `YOUR_LINKEDIN`
- Any featured-project URL whose repository slug differs from the guessed slug
- The Command Center text if it does not accurately describe you

Do not claim a stack or project responsibility you cannot defend. A clean, true README beats a flashy fiction.

## 3. Enable the workflows

Go to the repository’s **Actions** tab and enable workflows if GitHub asks. Run each workflow once using **Run workflow**.

| Workflow | What it produces | Notes |
| :-- | :-- | :-- |
| `snake.yml` | Animated contribution snake on the `output` branch | First run creates the branch used by the image URL. |
| `summary.yml` | Summary-card files in `profile-summary-card-output` | This runs independently; the README currently uses the stable public card endpoint. You may switch to the generated files later. |
| `metrics.yml` | WakaTime content inside the marked README section | Requires the secret below. |

## 4. Add the WakaTime secret (optional)

1. Create a WakaTime account and copy its API key.
2. In this repository open **Settings → Secrets and variables → Actions**.
3. Add repository secret `WAKATIME_API_KEY` with that value.
4. Run **Update developer metrics** once. It updates only the content between `START_SECTION:waka` and `END_SECTION:waka`.

Without this secret, disable `metrics.yml`; otherwise its scheduled runs will fail. That is expected behaviour, not a GitHub bug.

## 5. “3D contribution graph” — what is actually possible

GitHub READMEs are static Markdown/HTML. They cannot host safe interactive JavaScript, WebGL, or a truly interactive 3D graph. The honest alternatives are:

- Use the included activity graph and animated snake for a GitHub-native profile.
- Publish a real 3D visualization on Parasfolio, then link to it from the README.
- Embed a rendered GIF or SVG preview that links to the live visualization.

Do not use an iframe: GitHub strips it from READMEs.

## 6. Recommended final checks

1. Confirm every external image loads on the profile page.
2. Ensure your featured repositories are public or replace private links.
3. Pin the four featured projects on your GitHub profile as well; README cards are not a replacement for GitHub pins.
4. Re-run the snake workflow after changing your username (if that ever happens).
