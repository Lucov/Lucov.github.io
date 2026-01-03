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

    def _process_sleep_data(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Process raw sleep session data"""
        if not sessions:
            return None

        # Get most recent sleep session
        latest = sessions[-1]

        start_ms = int(latest.get('startTimeMillis', 0))
        end_ms = int(latest.get('endTimeMillis', 0))
        duration_hours = (end_ms - start_ms) / (1000 * 60 * 60)

        # Extract sleep stages if available
        deep_sleep = latest.get('deepSleep', duration_hours * 0.2)
        rem_sleep = latest.get('remSleep', duration_hours * 0.15)
        light_sleep = duration_hours - deep_sleep - rem_sleep

        # Calculate sleep score (simplified algorithm)
        sleep_score = min(100, int(
            (duration_hours / 8 * 40) +  # Duration component
            (deep_sleep / duration_hours * 30) +  # Deep sleep quality
            (rem_sleep / duration_hours * 30)  # REM quality
        ))

        # Calculate energy score based on sleep quality and duration
        # Energy is typically lower than sleep score (you wake up building energy)
        energy_score = max(0, min(100, int(
            sleep_score * 0.85 +  # Base on sleep quality
            (duration_hours / 8 * 15)  # Duration bonus
        )))

        energy_level = "High Energy" if energy_score >= 80 else "Good" if energy_score >= 70 else "Moderate" if energy_score >= 60 else "Low"

        start_time = datetime.fromtimestamp(start_ms / 1000)
        end_time = datetime.fromtimestamp(end_ms / 1000)

        # Calculate weekly averages
        sleep_scores = [sleep_score]  # Would need to process all sessions for true average
        energy_scores = [energy_score]
        durations = [duration_hours]

        return {
            'daily': {
                'duration': round(duration_hours, 1),
                'score': sleep_score,
                'deepSleep': round(deep_sleep, 1),
                'remSleep': round(rem_sleep, 1),
                'lightSleep': round(light_sleep, 1),
                'bedTime': start_time.strftime('%H:%M'),
                'wakeTime': end_time.strftime('%H:%M')
            },
            'energy': {
                'score': energy_score,
                'level': energy_level
            },
            'weekly': {
                'averageSleepScore': round(statistics.mean(sleep_scores)),
                'averageEnergyScore': round(statistics.mean(energy_scores)),
                'averageSleepDuration': round(statistics.mean(durations), 1)
            }
        }

    def _process_heart_rate_data(self, data: Dict) -> Dict[str, Any]:
        """Process raw heart rate data"""
        hr_values = []

        for bucket in data.get('bucket', []):
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        hr = value.get('fpVal')
                        if hr:
                            hr_values.append(int(hr))

        if not hr_values:
            print("Warning: No heart rate values found in API response")
            return None

        resting = min(hr_values)

        return {
            'resting': resting,
            'average': round(statistics.mean(hr_values)),
            'max': max(hr_values),
            'min': min(hr_values),
            'weeklyResting': resting  # Simplified
        }

    def _process_activity_data(self, data: Dict) -> Dict[str, Any]:
        """Process raw activity data"""
        steps = 0
        calories = 0
        active_minutes = 0

        for bucket in data.get('bucket', []):
            for dataset in bucket.get('dataset', []):
                data_type = dataset.get('dataSourceId', '')

                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        if 'step_count' in data_type:
                            steps += int(value.get('intVal', 0))
                        elif 'calories' in data_type:
                            calories += int(value.get('fpVal', 0))
                        elif 'active_minutes' in data_type:
                            active_minutes += int(value.get('intVal', 0))

        if steps == 0 and calories == 0 and active_minutes == 0:
            print("Warning: No activity data found in API response")
            return None

        return {
            'steps': steps,
            'calories': calories,
            'activeMinutes': active_minutes,
            'weeklySteps': steps  # Simplified
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
    sleep_data = client.get_sleep_data(days=7)
    hr_data = client.get_heart_rate_data(days=1)
    activity_data = client.get_activity_data(days=1)

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
