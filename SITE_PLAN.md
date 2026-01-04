# Site Plan

A personal website with two core functionalities: **Blog** and **Health Card**.

---

## 1. Blog

**Purpose:** A simple platform to post and share text entries.

### Goals
- Write and publish text posts with minimal friction
- Clean, readable presentation
- No database or CMS overhead - static HTML files

### Current Implementation
- Posts are individual HTML files in `/posts/`
- Homepage (`index.html`) displays post previews with links
- Manual process: create HTML file, add preview card to homepage

### How to Post
1. Create a new HTML file in `/posts/` (copy existing post as template)
2. Add a preview card to `index.html`
3. Commit and push

---

## 2. Health Card

**Purpose:** Display Samsung Health stats at a glance - the same information you'd see on your phone or watch, accessible from anywhere.

### Goals
- Pull health data from Samsung Health
- Display stats in a convenient, readable card format
- See the same metrics available on phone/watch:
  - **Sleep:** score, duration, deep/REM breakdown, bed/wake times
  - **Energy:** score and level
  - **Heart Rate:** resting BPM, average, min/max
  - **Steps:** daily count, active minutes, calories
  - **Stress:** level score
  - **Weekly Trends:** averages over 7 days

### Current Implementation

**Data Flow:**
```
Samsung Health → Health Connect → Google Fitness API → GitHub Actions → health-data.json → Website
```

**Automation:**
- GitHub Actions runs daily at 8 AM UTC
- Fetches data via Google Fitness API (which reads from Health Connect)
- Updates `health-data.json` and auto-commits
- Frontend JavaScript loads JSON and renders the card

**Display Logic:**
- Shows card only when data is fresh (within 48 hours)
- Hides card entirely if data is stale or missing
- Color-codes metrics by quality (green/blue/amber/red)

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Hosting | GitHub Pages (static) |
| Data Pipeline | Python + Google Fitness API |
| Automation | GitHub Actions |

---

## File Structure

```
/
├── index.html           # Homepage: blog posts + health card sidebar
├── about.html           # About page
├── posts/               # Blog post files
│   └── *.html
├── style.css            # Site-wide styles
├── health-stats.js      # Health card display logic
├── health-data.json     # Latest health data (auto-updated)
├── fetch-health-connect.py  # API fetcher script
└── .github/workflows/   # GitHub Actions automation
```

---

## Summary

| Feature | What It Does |
|---------|--------------|
| **Blog** | Post text entries as simple HTML files |
| **Health Card** | Pull Samsung Health stats and display them as a convenient card with the same info as your phone/watch |
