# My Blog

A simple, clean blog built with HTML and CSS, featuring Samsung Health data integration.

## Features

- 📝 Clean, minimal blog design
- 📊 Samsung Health stats card (sleep, heart rate, steps, stress)
- 📱 Fully responsive layout
- ⚡ Fast, static site (no external dependencies)

## Structure

- `index.html` - Homepage with health stats and blog post listings
- `about.html` - About page
- `posts/` - Individual blog posts
- `style.css` - Site stylesheet
- `health-stats.js` - Health data display logic
- `health-data.json` - Your health data (update regularly)
- `update-health-data.py` - Script to process Samsung Health exports
- `assets/` - Images and other assets

## Adding New Posts

1. Create a new HTML file in the `posts/` directory
2. Add a preview of the post to `index.html`
3. Follow the existing post structure for consistency

## Health Data Integration

Your blog displays a health stats card showing:
- Sleep score and duration
- Resting heart rate
- Daily steps and activity
- Stress levels
- 7-day trends

### Two Ways to Update Health Data

**Option 1: Automatic (Health Connect API)** ⭐ Recommended
- Set up once, updates automatically daily
- Uses Health Connect API (Samsung Health syncs to it)
- Requires Google Cloud project setup
- **See [HEALTH_CONNECT_SETUP.md](HEALTH_CONNECT_SETUP.md)**

```bash
# One-time setup
pip install -r requirements.txt
python fetch-health-connect.py  # Authenticate
# Then GitHub Actions updates automatically daily
```

**Option 2: Manual (CSV Export)**
- More privacy control, update when you want
- Export CSV from Samsung Health app
- Run Python script to process files
- **See [HEALTH_DATA_GUIDE.md](HEALTH_DATA_GUIDE.md)**

```bash
python update-health-data.py --sleep sleep.csv --heart heart.csv --steps steps.csv
```
