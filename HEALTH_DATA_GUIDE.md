# Samsung Health Data Integration Guide

This guide explains how to display your Samsung Health data (sleep, heart rate, steps, stress) on your blog.

## Overview

Your blog now displays a beautiful health stats card on the homepage showing:
- **Sleep Score** - Quality rating with duration and sleep stage breakdown
- **Resting Heart Rate** - With daily average and status
- **Steps** - Daily step count with active minutes and calories
- **Stress Level** - Average stress score with level indicator
- **7-Day Trends** - Weekly averages for all metrics

## How It Works

1. **Samsung Health App** → Export your health data as CSV files
2. **Python Script** → Process CSV files and update `health-data.json`
3. **Blog** → JavaScript automatically displays the data on your homepage

## Setup Instructions

### Step 1: Export Data from Samsung Health

1. Open the **Samsung Health** app on your phone
2. Tap the **menu icon (☰)** in the top-right
3. Go to **Settings** > **Download my data**
4. Select the data types you want:
   - ✓ Sleep
   - ✓ Heart Rate
   - ✓ Steps
   - ✓ Stress
5. Choose date range (recommend: Last 30 days)
6. Tap **Request data**
7. You'll receive a download link via email or in-app notification
8. Download and extract the ZIP file

### Step 2: Locate Your CSV Files

After extracting the ZIP, you'll find CSV files like:
- `com.samsung.health.sleep.yyyymmdd.csv` - Sleep data
- `com.samsung.shealth.tracker.heart_rate.yyyymmdd.csv` - Heart rate
- `com.samsung.health.step_daily_trend.yyyymmdd.csv` - Steps
- `com.samsung.health.stress.yyyymmdd.csv` - Stress

### Step 3: Update Your Blog Data

Transfer the CSV files to your blog directory and run:

```bash
python update-health-data.py \
  --sleep com.samsung.health.sleep.20260102.csv \
  --heart com.samsung.shealth.tracker.heart_rate.20260102.csv \
  --steps com.samsung.health.step_daily_trend.20260102.csv \
  --stress com.samsung.health.stress.20260102.csv
```

Or just update specific metrics:

```bash
# Update only sleep data
python update-health-data.py --sleep sleep.csv

# Update sleep and heart rate
python update-health-data.py --sleep sleep.csv --heart heart.csv
```

### Step 4: Verify and Deploy

1. Open `health-data.json` to verify the data looks correct
2. Open `index.html` in a browser to preview
3. Commit and push changes:
   ```bash
   git add health-data.json
   git commit -m "Update health stats for $(date +%Y-%m-%d)"
   git push
   ```

## Automating Updates

### Option 1: Manual Updates (Recommended for Privacy)

Update whenever you want to share new data:
1. Export from Samsung Health
2. Run the Python script
3. Push to GitHub

### Option 2: Scheduled Updates

Create a reminder to update weekly or monthly. Samsung Health allows batch exports, so you can download a month's worth of data at once.

### Option 3: GitHub Actions (Advanced)

You could set up a GitHub Action to automatically update from Samsung Health API, but this requires:
- Samsung Health API access (requires developer account)
- OAuth authentication setup
- Storing credentials securely

For most users, manual updates are simpler and give you more control over what's shared.

## Customization

### Change the Card Colors

Edit `style.css` and modify the gradient:

```css
#health-stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  /* Try other gradients:
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  */
}
```

### Hide Specific Metrics

Edit `health-stats.js` and comment out the metrics you don't want to display.

### Adjust the Data Structure

Edit `health-data.json` directly for manual updates:

```json
{
  "lastUpdated": "2026-01-02T08:00:00Z",
  "dailyStats": {
    "date": "2026-01-02",
    "sleep": {
      "duration": 7.5,
      "score": 85,
      ...
    }
  }
}
```

## Privacy Considerations

**Important:** This feature displays your health data publicly on your blog. Consider:

1. **What to share:** You can choose which metrics to display
2. **How often:** Update frequency is entirely up to you
3. **Granularity:** The card shows daily stats and 7-day averages (not detailed logs)
4. **Control:** You manually export and update (nothing automatic)

To remove the health card entirely:
1. Delete or comment out `<div id="health-stats-card">` in `index.html`
2. Remove `<script src="health-stats.js">` from the HTML

## Troubleshooting

### "Unable to load health data"

- Check that `health-data.json` exists in your blog root
- Verify the JSON is valid (use a JSON validator)
- Check browser console for errors

### Data looks incorrect

- Verify CSV field names match what the script expects
- Samsung Health CSV format can vary by version
- Edit `update-health-data.py` and adjust field names if needed

### Script errors

```bash
# Check Python version (needs 3.6+)
python --version

# Run with verbose error output
python -u update-health-data.py --sleep sleep.csv
```

## File Reference

- `health-data.json` - Your health data (update this regularly)
- `health-stats.js` - JavaScript to display the data
- `update-health-data.py` - Script to process Samsung Health exports
- `index.html` - Homepage with health card
- `style.css` - Styling for the health card

## Questions?

The health data feature is designed to be simple and privacy-focused. You have complete control over what data is shared and when it's updated.

For Samsung Health export issues, refer to Samsung's official documentation.
