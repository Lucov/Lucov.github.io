# Health Connect API - Automated Setup Guide

This guide shows you how to automatically sync your Samsung Health data to your blog using the Health Connect API.

## Why Health Connect?

**Health Connect** is Google's unified health data platform that:
- ✅ Samsung Health syncs to it automatically
- ✅ Has a proper API with OAuth authentication
- ✅ Can be automated with GitHub Actions
- ✅ More reliable than CSV exports
- ✅ Updates happen automatically daily

## Setup Overview

1. **Enable Health Connect** on your Android phone
2. **Sync Samsung Health** to Health Connect
3. **Create Google Cloud Project** and enable APIs
4. **Get OAuth credentials**
5. **Authenticate locally** to get initial token
6. **Set up GitHub Actions** for automation

## Step-by-Step Setup

### Part 1: Enable Health Connect on Your Phone

1. **Install Health Connect** (if not already installed)
   - Open Google Play Store
   - Search for "Health Connect by Google"
   - Install the app

2. **Connect Samsung Health**
   - Open Health Connect app
   - Tap "App permissions"
   - Find "Samsung Health"
   - Grant permissions for:
     - Sleep
     - Heart rate
     - Steps
     - Activity

3. **Verify data is syncing**
   - Open Health Connect
   - Check that recent data appears
   - Samsung Health should sync automatically

### Part 2: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com
   - Sign in with your Google account

2. **Create a new project**
   - Click "Select a project" → "New Project"
   - Name: "Health Blog Integration" (or whatever you like)
   - Click "Create"

3. **Enable Google Fitness API**
   - In the search bar, type "Google Fitness API"
   - Click "Enable"
   - This API provides access to Health Connect data

4. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" (unless you have a Google Workspace)
   - Fill in:
     - App name: "My Health Blog"
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"

5. **Add Scopes**
   - Click "Add or Remove Scopes"
   - Search and add:
     - `https://www.googleapis.com/auth/fitness.sleep.read`
     - `https://www.googleapis.com/auth/fitness.heart_rate.read`
     - `https://www.googleapis.com/auth/fitness.activity.read`
   - Click "Update" then "Save and Continue"

6. **Add Test Users**
   - Add your own Google account email
   - Click "Save and Continue"

### Part 3: Create OAuth Credentials

1. **Create OAuth 2.0 Client ID**
   - Go to "APIs & Services" → "Credentials"
   - Click "+ Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Health Blog Desktop Client"
   - Click "Create"

2. **Download credentials**
   - A popup will show your Client ID and Secret
   - Click "Download JSON"
   - Save as `credentials.json` in your blog directory
   - **Important:** Add `credentials.json` to `.gitignore` (don't commit it!)

### Part 4: Initial Authentication (Local)

1. **Install Python dependencies**
   ```bash
   pip install google-auth google-auth-oauthlib google-auth-httplib2 requests
   ```

2. **Run the fetch script locally**
   ```bash
   python fetch-health-connect.py
   ```

3. **Authenticate in browser**
   - A browser window will open
   - Sign in with your Google account
   - Grant permissions for the app
   - You'll see "The authentication flow has completed"

4. **Token saved**
   - A `token.pickle` file is created
   - This contains your authenticated session
   - Keep this secure!

5. **Verify it works**
   - Check that `health-data.json` was updated
   - Open `index.html` in browser to see new data

### Part 5: Set Up GitHub Actions for Automation

1. **Prepare credentials for GitHub**
   ```bash
   # Encode token as base64
   base64 token.pickle > token.txt
   ```

2. **Add GitHub Secrets**
   - Go to your GitHub repository
   - Click "Settings" → "Secrets and variables" → "Actions"
   - Click "New repository secret"

   **Secret 1: GOOGLE_CREDENTIALS**
   - Name: `GOOGLE_CREDENTIALS`
   - Value: Copy entire contents of `credentials.json`
   - Click "Add secret"

   **Secret 2: GOOGLE_TOKEN**
   - Name: `GOOGLE_TOKEN`
   - Value: Copy entire contents of `token.txt` (base64 encoded token)
   - Click "Add secret"

3. **Update .gitignore**
   ```bash
   echo "credentials.json" >> .gitignore
   echo "token.pickle" >> .gitignore
   echo "token.txt" >> .gitignore
   git add .gitignore
   git commit -m "Add credentials to gitignore"
   ```

4. **Push the workflow**
   ```bash
   git add .github/workflows/update-health-data.yml
   git add fetch-health-connect.py
   git commit -m "Add automated health data sync"
   git push
   ```

5. **Test the workflow**
   - Go to GitHub repository → "Actions" tab
   - Select "Update Health Data" workflow
   - Click "Run workflow" → "Run workflow"
   - Watch it run and verify success

### Part 6: Configure Schedule

The workflow runs automatically at **8 AM UTC** daily. To change this:

Edit `.github/workflows/update-health-data.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # 8 AM UTC
  # Examples:
  # - cron: '0 0 * * *'  # Midnight UTC
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 12 * * *'  # Noon UTC
```

Use [crontab.guru](https://crontab.guru/) to create custom schedules.

## How It Works

1. **Daily (or on schedule):** GitHub Actions triggers
2. **Fetch data:** Script calls Health Connect API
3. **Update JSON:** New data written to `health-data.json`
4. **Commit & push:** Changes automatically committed
5. **Deploy:** GitHub Pages deploys updated site
6. **Blog shows new data:** Visitors see your latest stats

## Troubleshooting

### "Error: credentials.json not found"

- Make sure you downloaded OAuth credentials from Google Cloud Console
- Place `credentials.json` in your blog root directory
- Don't commit it to git!

### "Token expired" or authentication errors

1. Delete `token.pickle`
2. Run `python fetch-health-connect.py` locally
3. Re-authenticate in browser
4. Re-encode and update GitHub secret:
   ```bash
   base64 token.pickle > token.txt
   ```
5. Update `GOOGLE_TOKEN` secret on GitHub

### No data appearing

- Verify Samsung Health is syncing to Health Connect
- Check Health Connect app permissions
- Try running script locally to see detailed errors:
  ```bash
  python fetch-health-connect.py
  ```

### GitHub Actions failing

- Check Actions tab for error logs
- Verify secrets are set correctly:
  - Go to Settings → Secrets → Actions
  - Both `GOOGLE_CREDENTIALS` and `GOOGLE_TOKEN` should exist
- Check token hasn't expired (tokens last ~7 days, but refresh automatically if valid)

### Data is wrong or missing metrics

- Health Connect API doesn't include all Samsung Health metrics (e.g., stress)
- Some metrics require specific data sources
- Check that Samsung Health is actively recording the data you want

## Privacy & Security

### What's shared:
- Daily aggregated stats (sleep score, heart rate, steps)
- 7-day averages
- No detailed minute-by-minute data

### Security best practices:
- ✅ Credentials stored as GitHub Secrets (encrypted)
- ✅ `credentials.json` and `token.pickle` in `.gitignore`
- ✅ OAuth tokens refreshed automatically
- ✅ API access limited to read-only fitness data
- ✅ Only your Google account can access the data

### To stop sharing:
1. Disable GitHub Actions workflow
2. Revoke access in [Google Account Permissions](https://myaccount.google.com/permissions)
3. Delete the Google Cloud Project

## Alternative: Manual Updates

If you prefer not to automate:

```bash
# Just run manually whenever you want to update
python fetch-health-connect.py

# Then commit and push
git add health-data.json
git commit -m "Update health data"
git push
```

## Comparison: CSV vs API

| Feature | CSV Export | Health Connect API |
|---------|-----------|-------------------|
| Setup complexity | Easy | Moderate |
| Updates | Manual | Automatic |
| Data freshness | When you export | Daily (or hourly) |
| Metrics available | All Samsung Health data | Standard fitness metrics |
| Privacy control | Full | Full (you control the app) |
| Maintenance | None | Token refresh (automatic) |

## Resources

- [Health Connect Developer Docs](https://developer.android.com/guide/health-and-fitness/health-connect)
- [Google Fitness API Reference](https://developers.google.com/fit/rest)
- [OAuth 2.0 Setup](https://developers.google.com/identity/protocols/oauth2)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

## Getting Help

If you run into issues:

1. Check the GitHub Actions logs for errors
2. Run the script locally to debug:
   ```bash
   python fetch-health-connect.py
   ```
3. Verify Health Connect app has recent data
4. Check that Samsung Health is syncing to Health Connect

Most issues are related to OAuth token expiration (re-authenticate) or Health Connect not syncing (check app permissions).
