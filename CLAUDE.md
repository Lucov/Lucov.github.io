# CLAUDE.md

This file provides guidance for AI assistants working on this repository.

## Project Overview

Static personal blog hosted on GitHub Pages (`Lucov.github.io`) with integrated Samsung Health data display. Built with **pure HTML5, CSS3, and vanilla JavaScript** — no frameworks, no build system, no package manager.

## Repository Structure

```
├── index.html                  # Homepage: blog post listings + health stats sidebar
├── about.html                  # About page
├── posts/                      # Blog post HTML files
│   ├── welcome.html
│   └── getting-started.html
├── style.css                   # Single stylesheet (CSS Grid, responsive)
├── health-stats.js             # HealthStats class — fetches and renders health-data.json
├── health-data.json            # Health metrics data (auto-updated by CI or manually)
├── assets/                     # SVG and PNG images
├── fetch-health-connect.py     # Google Health Connect API fetcher (Python)
├── update-health-data.py       # Samsung Health CSV processor (Python)
├── discover-health-data.py     # Health API exploration utility
├── test-health-stats.js        # Node.js test suite for health data validation
├── requirements.txt            # Python deps (google-auth, requests)
├── .github/workflows/
│   └── update-health-data.yml  # Daily health data sync (GitHub Actions)
└── *.md                        # Documentation files
```

## Key Commands

### Testing
```bash
node test-health-stats.js       # Validate health-data.json structure and freshness
```

### Health Data (manual update)
```bash
pip install -r requirements.txt
python update-health-data.py --sleep sleep.csv --heart heart.csv --steps steps.csv
```

### Health Data (API fetch)
```bash
python fetch-health-connect.py  # Requires credentials.json and token.pickle
```

### Serving locally
Open `index.html` directly in a browser, or use any static file server:
```bash
python -m http.server 8000
```

## Architecture & Conventions

### No Build System
Files are served directly as-is by GitHub Pages. There is no bundler, transpiler, minifier, or preprocessor. Edit files directly.

### HTML Structure
- Each page is a standalone HTML file with full `<!DOCTYPE html>` structure
- Pages share the same `<header>` and `<footer>` markup (copy between files — no templating)
- Blog posts live in `posts/` as individual HTML files
- New posts must also have a preview added to `index.html` in the `<section class="posts">` block

### CSS
- Single `style.css` file, no preprocessor
- System font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, ...`
- Two-column layout via CSS Grid: `.content-wrapper { grid-template-columns: 1fr 360px }`
- Responsive breakpoints at 1024px and 768px
- Health status colors: green (`#10b981`), blue (`#3b82f6`), amber (`#f59e0b`), red (`#ef4444`)

### JavaScript
- `health-stats.js` contains a single `HealthStats` class, initialized on `DOMContentLoaded`
- Fetches `health-data.json` with cache-busting query parameter
- 48-hour freshness threshold — stale data hides the health card
- No external JS dependencies

### Health Data Schema (`health-data.json`)
```json
{
  "lastUpdated": "ISO 8601 timestamp",
  "dailyStats": {
    "date": "YYYY-MM-DD",
    "sleep": { "duration", "score", "deepSleep", "remSleep", "lightSleep", "bedTime", "wakeTime" },
    "energy": { "score", "level" },
    "heartRate": { "resting", "average", "max", "min", "weeklyResting" },
    "activity": { "steps", "calories", "activeMinutes", "weeklySteps" },
    "stress": { "average", "level" }
  },
  "weeklyTrends": {
    "averageSleepScore", "averageEnergyScore", "averageSleepDuration",
    "averageRestingHR", "averageSteps"
  }
}
```

### Python Scripts
- Target Python 3.6+
- Dependencies in `requirements.txt` (google-auth ecosystem + requests)
- `fetch-health-connect.py` — OAuth-authenticated API fetcher, outputs `health-data.json`
- `update-health-data.py` — Parses Samsung Health CSV exports into `health-data.json`
- `discover-health-data.py` — Utility for exploring available Google Fit data sources

## CI/CD

- **GitHub Actions** workflow (`.github/workflows/update-health-data.yml`) runs daily at 8 AM UTC
- Fetches health data via Health Connect API, auto-commits `health-data.json` if changed
- Uses GitHub Secrets: `GOOGLE_CREDENTIALS`, `GOOGLE_TOKEN`
- Can also be triggered manually via `workflow_dispatch`

## Security & Sensitive Files

**Never commit these** (protected by `.gitignore`):
- `credentials.json` — Google OAuth client credentials
- `token.pickle` — OAuth refresh token
- `token.txt` — Token in text form
- `health-data-diagnostics.json` — Debug diagnostics output

## Development Workflow

- Feature branches use naming convention: `claude/<feature-name>-<id>`
- Changes are integrated via pull requests with merge commits
- No linter or formatter is configured — follow existing code style
- No automated test runner in CI — run `node test-health-stats.js` manually

## Adding Content

### New Blog Post
1. Create `posts/<slug>.html` following the structure of existing posts
2. Add a `<article class="post-preview">` entry to `index.html` (newest first)
3. Include post date in `<p class="post-meta">` format

### Modifying Styles
All styles are in `style.css`. The health card uses the `#health-stats-card` selector and related `.health-*` classes.

### Modifying Health Display
The `HealthStats` class in `health-stats.js` handles all rendering. Set `this.debug = true` in the constructor for verbose console logging during development.
