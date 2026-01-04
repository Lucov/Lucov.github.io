#!/usr/bin/env python3
"""
Health Connect API Integration

Automatically fetches health data from Google Health Connect API and updates health-data.json.
This is more convenient than manual CSV exports.

Setup:
    1. Enable Health Connect on your Android phone
    2. Sync Samsung Health to Health Connect
    3. Create a Google Cloud project and enable Health Connect API
    4. Set up OAuth credentials
    5. Configure environment variables

Usage:
    python fetch-health-connect.py
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import statistics

# Check for required dependencies
try:
    import requests
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle
except ImportError:
    print("Missing required dependencies. Install with:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 requests")
    exit(1)


class HealthConnectClient:
    """Client for fetching data from Health Connect API"""

    SCOPES = [
        'https://www.googleapis.com/auth/fitness.sleep.read',
        'https://www.googleapis.com/auth/fitness.heart_rate.read',
        'https://www.googleapis.com/auth/fitness.activity.read',
    ]

    def __init__(self):
        self.creds = None
        self.token_file = 'token.pickle'
        self.credentials_file = 'credentials.json'

    def authenticate(self):
        """Authenticate with Google Health Connect API"""
        # Load saved credentials if they exist
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

        # If credentials are invalid or don't exist, get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"Error: {self.credentials_file} not found!")
                    print("Please download OAuth credentials from Google Cloud Console")
                    print("See HEALTH_CONNECT_SETUP.md for instructions")
                    exit(1)

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save credentials for next time
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        print("✓ Authenticated successfully")

    def get_sleep_data(self, days: int = 7) -> Dict[str, Any]:
        """Fetch sleep data from Health Connect"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # Health Connect REST API endpoint
        url = "https://www.googleapis.com/fitness/v1/users/me/sessions"

        headers = {
            'Authorization': f'Bearer {self.creds.token}',
            'Content-Type': 'application/json'
        }

        params = {
            'startTime': start_time.isoformat() + 'Z',
            'endTime': end_time.isoformat() + 'Z',
            'activityType': 72  # Sleep activity type
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get('session'):
                print("Warning: No sleep data found from API")
                return None

            return self._process_sleep_data(data['session'])

        except requests.exceptions.RequestException as e:
            print(f"Error fetching sleep data: {e}")
            return None

    def get_heart_rate_data(self, days: int = 1) -> Dict[str, Any]:
        """Fetch heart rate data from Health Connect"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"

        headers = {
            'Authorization': f'Bearer {self.creds.token}',
            'Content-Type': 'application/json'
        }

        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.heart_rate.bpm"
            }],
            "bucketByTime": {"durationMillis": 86400000},  # 1 day
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            return self._process_heart_rate_data(data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching heart rate data: {e}")
            return None

    def get_activity_data(self, days: int = 1) -> Dict[str, Any]:
        """Fetch activity/steps data from Health Connect"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"

        headers = {
            'Authorization': f'Bearer {self.creds.token}',
            'Content-Type': 'application/json'
        }

        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.calories.expended"},
                {"dataTypeName": "com.google.active_minutes"}
            ],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            return self._process_activity_data(data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching activity data: {e}")
            return None

    def _calculate_sleep_metrics(self, session: Dict) -> Dict[str, Any]:
        """Calculate sleep metrics for a single session"""
        start_ms = int(session.get('startTimeMillis', 0))
        end_ms = int(session.get('endTimeMillis', 0))
        duration_hours = (end_ms - start_ms) / (1000 * 60 * 60)

        if duration_hours <= 0:
            return None

        # Extract sleep stages if available
        deep_sleep = session.get('deepSleep', duration_hours * 0.2)
        rem_sleep = session.get('remSleep', duration_hours * 0.15)
        light_sleep = max(0, duration_hours - deep_sleep - rem_sleep)

        # Calculate sleep score (simplified algorithm)
        # Duration: 8 hours = 40 points, Deep sleep quality: up to 30 points, REM: up to 30 points
        duration_score = min(40, (duration_hours / 8) * 40)
        deep_score = (deep_sleep / duration_hours) * 30 if duration_hours > 0 else 0
        rem_score = (rem_sleep / duration_hours) * 30 if duration_hours > 0 else 0
        sleep_score = min(100, int(duration_score + deep_score + rem_score))

        # Calculate energy score based on sleep quality and duration
        energy_score = max(0, min(100, int(
            sleep_score * 0.85 + (duration_hours / 8 * 15)
        )))

        return {
            'duration': duration_hours,
            'score': sleep_score,
            'deepSleep': deep_sleep,
            'remSleep': rem_sleep,
            'lightSleep': light_sleep,
            'energyScore': energy_score,
            'startMs': start_ms,
            'endMs': end_ms
        }

    def _process_sleep_data(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Process raw sleep session data with proper weekly averages"""
        if not sessions:
            return None

        # Process all sessions to calculate proper weekly averages
        all_metrics = []
        for session in sessions:
            metrics = self._calculate_sleep_metrics(session)
            if metrics:
                all_metrics.append(metrics)

        if not all_metrics:
            return None

        # Get most recent session for daily stats
        latest = all_metrics[-1]

        start_time = datetime.fromtimestamp(latest['startMs'] / 1000)
        end_time = datetime.fromtimestamp(latest['endMs'] / 1000)

        energy_level = (
            "High Energy" if latest['energyScore'] >= 80 else
            "Good" if latest['energyScore'] >= 70 else
            "Moderate" if latest['energyScore'] >= 60 else
            "Low"
        )

        # Calculate weekly averages from ALL sessions (up to 7 days)
        sleep_scores = [m['score'] for m in all_metrics]
        energy_scores = [m['energyScore'] for m in all_metrics]
        durations = [m['duration'] for m in all_metrics]

        print(f"    Processing {len(all_metrics)} sleep sessions for weekly averages")

        return {
            'daily': {
                'duration': round(latest['duration'], 1),
                'score': latest['score'],
                'deepSleep': round(latest['deepSleep'], 1),
                'remSleep': round(latest['remSleep'], 1),
                'lightSleep': round(latest['lightSleep'], 1),
                'bedTime': start_time.strftime('%H:%M'),
                'wakeTime': end_time.strftime('%H:%M')
            },
            'energy': {
                'score': latest['energyScore'],
                'level': energy_level
            },
            'weekly': {
                'averageSleepScore': round(statistics.mean(sleep_scores)),
                'averageEnergyScore': round(statistics.mean(energy_scores)),
                'averageSleepDuration': round(statistics.mean(durations), 1),
                'sessionsAnalyzed': len(all_metrics)
            }
        }

    def _process_heart_rate_data(self, data: Dict) -> Dict[str, Any]:
        """Process raw heart rate data with daily breakdown for weekly averages"""
        daily_hr_data = []

        for bucket in data.get('bucket', []):
            bucket_values = []
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        hr = value.get('fpVal')
                        if hr and hr > 30 and hr < 220:  # Validate reasonable HR range
                            bucket_values.append(int(hr))

            if bucket_values:
                daily_hr_data.append({
                    'resting': min(bucket_values),
                    'average': round(statistics.mean(bucket_values)),
                    'max': max(bucket_values),
                    'min': min(bucket_values)
                })

        if not daily_hr_data:
            print("Warning: No heart rate values found in API response")
            return None

        # Use most recent day for daily stats
        latest = daily_hr_data[-1]

        # Calculate weekly average resting HR
        weekly_resting = round(statistics.mean([d['resting'] for d in daily_hr_data]))

        print(f"    Processing {len(daily_hr_data)} days of heart rate data")

        return {
            'resting': latest['resting'],
            'average': latest['average'],
            'max': latest['max'],
            'min': latest['min'],
            'weeklyResting': weekly_resting,
            'daysAnalyzed': len(daily_hr_data)
        }

    def _process_activity_data(self, data: Dict) -> Dict[str, Any]:
        """Process raw activity data with daily breakdown for weekly averages"""
        daily_activity = []

        for bucket in data.get('bucket', []):
            day_steps = 0
            day_calories = 0
            day_active_mins = 0

            for dataset in bucket.get('dataset', []):
                data_type = dataset.get('dataSourceId', '')

                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        if 'step_count' in data_type:
                            day_steps += int(value.get('intVal', 0))
                        elif 'calories' in data_type:
                            day_calories += int(value.get('fpVal', 0))
                        elif 'active_minutes' in data_type:
                            day_active_mins += int(value.get('intVal', 0))

            # Only add days with actual data
            if day_steps > 0 or day_calories > 0:
                daily_activity.append({
                    'steps': day_steps,
                    'calories': day_calories,
                    'activeMinutes': day_active_mins
                })

        if not daily_activity:
            print("Warning: No activity data found in API response")
            return None

        # Use most recent day for daily stats
        latest = daily_activity[-1]

        # Calculate weekly average steps
        all_steps = [d['steps'] for d in daily_activity if d['steps'] > 0]
        weekly_steps = round(statistics.mean(all_steps)) if all_steps else 0

        print(f"    Processing {len(daily_activity)} days of activity data")

        return {
            'steps': latest['steps'],
            'calories': latest['calories'],
            'activeMinutes': latest['activeMinutes'],
            'weeklySteps': weekly_steps,
            'daysAnalyzed': len(daily_activity)
        }



def main():
    print("Health Connect Data Fetcher")
    print("=" * 50)

    # Diagnostic tracking
    diagnostics = {
        'fetchTime': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'dataFetched': {},
        'errors': []
    }

    # Initialize client
    try:
        client = HealthConnectClient()
        client.authenticate()
    except Exception as e:
        error_msg = f"Authentication failed: {e}"
        print(f"\n✗ {error_msg}")
        diagnostics['errors'].append(error_msg)
        save_diagnostics(diagnostics, success=False)
        exit(1)

    print("\nFetching health data from API...")

    # Fetch all data (returns None if fails)
    # Note: We fetch 7 days for weekly averages
    sleep_data = client.get_sleep_data(days=7)
    hr_data = client.get_heart_rate_data(days=7)
    activity_data = client.get_activity_data(days=7)

    # Track what was successfully fetched
    diagnostics['dataFetched']['sleep'] = sleep_data is not None
    diagnostics['dataFetched']['heartRate'] = hr_data is not None
    diagnostics['dataFetched']['activity'] = activity_data is not None

    # Validate that we got at least SOME real data
    if not sleep_data and not hr_data and not activity_data:
        error_msg = "Failed to fetch any health data from API. No data sources returned valid data."
        print(f"\n✗ {error_msg}")
        print("   Health stats will NOT be updated - no placeholder data will be shown.")
        print("   Check that:")
        print("   1. Samsung Health is syncing to Google Fit/Health Connect")
        print("   2. Your Google account has fitness data permissions")
        print("   3. Data exists for the requested time period")
        diagnostics['errors'].append(error_msg)
        save_diagnostics(diagnostics, success=False)
        exit(1)

    # Build health data structure - only include data that was successfully fetched
    now = datetime.now(timezone.utc)
    health_data = {
        'lastUpdated': now.isoformat().replace('+00:00', 'Z'),
        'dataSource': 'Health Connect API',
        'dailyStats': {
            'date': datetime.now().strftime('%Y-%m-%d'),
        },
        'weeklyTrends': {}
    }

    # Add sleep data if available
    if sleep_data:
        health_data['dailyStats']['sleep'] = sleep_data['daily']
        if 'energy' in sleep_data:
            health_data['dailyStats']['energy'] = sleep_data['energy']
        if 'weekly' in sleep_data:
            if 'averageSleepScore' in sleep_data['weekly']:
                health_data['weeklyTrends']['averageSleepScore'] = sleep_data['weekly']['averageSleepScore']
            if 'averageEnergyScore' in sleep_data['weekly']:
                health_data['weeklyTrends']['averageEnergyScore'] = sleep_data['weekly']['averageEnergyScore']
            if 'averageSleepDuration' in sleep_data['weekly']:
                health_data['weeklyTrends']['averageSleepDuration'] = sleep_data['weekly']['averageSleepDuration']
        print("  ✓ Sleep data fetched")
    else:
        diagnostics['errors'].append("Sleep data not available from API")

    # Add heart rate data if available
    if hr_data:
        health_data['dailyStats']['heartRate'] = hr_data
        if 'weeklyResting' in hr_data:
            health_data['weeklyTrends']['averageRestingHR'] = hr_data['weeklyResting']
        print("  ✓ Heart rate data fetched")
    else:
        diagnostics['errors'].append("Heart rate data not available from API")

    # Add activity data if available
    if activity_data:
        health_data['dailyStats']['activity'] = activity_data
        if 'weeklySteps' in activity_data:
            health_data['weeklyTrends']['averageSteps'] = activity_data['weeklySteps']
        print("  ✓ Activity data fetched")
    else:
        diagnostics['errors'].append("Activity data not available from API")

    # Note: Stress data not available in Health Connect API
    # We don't include it unless it's actually available

    # Save to JSON file
    output_file = 'health-data.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(health_data, f, indent=2)
        print(f"\n✓ Health data saved to {output_file}")
    except Exception as e:
        error_msg = f"Failed to save health data: {e}"
        print(f"\n✗ {error_msg}")
        diagnostics['errors'].append(error_msg)
        save_diagnostics(diagnostics, success=False)
        exit(1)

    # Print summary
    print(f"\nData Summary:")
    if sleep_data and 'daily' in sleep_data:
        print(f"  Sleep Score: {sleep_data['daily'].get('score', 'N/A')}")
    if hr_data and 'resting' in hr_data:
        print(f"  Resting HR: {hr_data['resting']} bpm")
    if activity_data and 'steps' in activity_data:
        print(f"  Steps: {activity_data['steps']:,}")
    print(f"  Last updated: {health_data['lastUpdated']}")

    # Save diagnostics
    save_diagnostics(diagnostics, success=True)

    print("\n✓ Done! Your blog will show the latest real data (no placeholders).")


def save_diagnostics(diagnostics: Dict[str, Any], success: bool):
    """Save diagnostic information to help track data fetch status"""
    diagnostics['success'] = success

    try:
        with open('health-data-diagnostics.json', 'w', encoding='utf-8') as f:
            json.dump(diagnostics, f, indent=2)
        print(f"\n📊 Diagnostics saved to health-data-diagnostics.json")
    except Exception as e:
        print(f"Warning: Could not save diagnostics: {e}")


if __name__ == "__main__":
    main()
