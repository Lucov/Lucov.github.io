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

**See [HEALTH_DATA_GUIDE.md](HEALTH_DATA_GUIDE.md) for complete setup instructions.**

Quick update:
```bash
python update-health-data.py --sleep sleep.csv --heart heart.csv --steps steps.csv
```
