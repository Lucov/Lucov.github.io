#!/usr/bin/env python3
"""
Health Connect Data Discovery Tool

This script explores what data is available from Google Fit / Health Connect APIs
and tries multiple methods to retrieve your Samsung Health data.
"""

import json
import os
from datetime import datetime, timedelta, timezone
import pickle

try:
    import requests
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("Missing dependencies. Run: pip install -r requirements.txt")
    exit(1)


class HealthDataExplorer:
    SCOPES = [
        'https://www.googleapis.com/auth/fitness.sleep.read',
        'https://www.googleapis.com/auth/fitness.heart_rate.read',
        'https://www.googleapis.com/auth/fitness.activity.read',
        'https://www.googleapis.com/auth/fitness.body.read',
        'https://www.googleapis.com/auth/fitness.location.read',
    ]

    def __init__(self):
        self.creds = None
        self.token_file = 'token.pickle'
        self.credentials_file = 'credentials.json'

    def authenticate(self):
        """Authenticate with Google"""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        print("✓ Authenticated\n")

    def list_data_sources(self):
        """List all available data sources"""
        print("=" * 60)
        print("DISCOVERING DATA SOURCES")
        print("=" * 60)

        url = "https://www.googleapis.com/fitness/v1/users/me/dataSources"
        headers = {'Authorization': f'Bearer {self.creds.token}'}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if 'dataSource' in data:
                print(f"\nFound {len(data['dataSource'])} data sources:\n")
                for idx, source in enumerate(data['dataSource'], 1):
                    print(f"{idx}. {source.get('dataStreamId', 'Unknown')}")
                    print(f"   Type: {source.get('dataType', {}).get('name', 'Unknown')}")
                    print(f"   App: {source.get('application', {}).get('name', 'Unknown')}")
                    print()
            else:
                print("No data sources found!")

            return data.get('dataSource', [])

        except Exception as e:
            print(f"Error listing data sources: {e}")
            return []

    def try_sleep_sessions(self):
        """Try to get sleep sessions"""
        print("\n" + "=" * 60)
        print("METHOD 1: Sleep Sessions API")
        print("=" * 60)

        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        url = "https://www.googleapis.com/fitness/v1/users/me/sessions"
        headers = {'Authorization': f'Bearer {self.creds.token}'}
        params = {
            'startTime': start_time.isoformat() + 'Z',
            'endTime': end_time.isoformat() + 'Z',
            'activityType': 72  # Sleep
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            print(f"\nResponse: {json.dumps(data, indent=2)[:500]}...")

            if data.get('session'):
                print(f"\n✓ Found {len(data['session'])} sleep sessions!")
                return data['session']
            else:
                print("\n✗ No sleep sessions found")
                return None

        except Exception as e:
            print(f"\n✗ Error: {e}")
            return None

    def try_aggregate_sleep_data(self):
        """Try aggregate endpoint for sleep"""
        print("\n" + "=" * 60)
        print("METHOD 2: Aggregate Sleep Data")
        print("=" * 60)

        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"
        headers = {'Authorization': f'Bearer {self.creds.token}'}

        # Try multiple data type names
        sleep_data_types = [
            "com.google.sleep.segment",
            "com.google.activity.segment",
            "com.google.sleep",
        ]

        for data_type in sleep_data_types:
            print(f"\nTrying data type: {data_type}")

            body = {
                "aggregateBy": [{"dataTypeName": data_type}],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000)
            }

            try:
                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()

                if data.get('bucket'):
                    has_data = any(
                        bucket.get('dataset', [{}])[0].get('point')
                        for bucket in data.get('bucket', [])
                    )
                    if has_data:
                        print(f"✓ Found data!")
                        print(json.dumps(data, indent=2)[:800])
                        return data
                    else:
                        print(f"✗ No data points")
                else:
                    print(f"✗ No buckets")

            except Exception as e:
                print(f"✗ Error: {e}")

        return None

    def try_dataset_read(self):
        """Try direct dataset read"""
        print("\n" + "=" * 60)
        print("METHOD 3: Direct Dataset Read")
        print("=" * 60)

        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        start_ms = int(start_time.timestamp() * 1000000000)  # nanoseconds
        end_ms = int(end_time.timestamp() * 1000000000)

        data_types_to_try = [
            "com.google.sleep.segment",
            "com.google.heart_rate.bpm",
            "com.google.step_count.delta",
            "com.google.activity.segment",
        ]

        for data_type in data_types_to_try:
            print(f"\nTrying: {data_type}")

            url = f"https://www.googleapis.com/fitness/v1/users/me/dataSources/derived:{data_type}:com.google.android.gms:merge_sleep_segments/datasets/{start_ms}-{end_ms}"
            headers = {'Authorization': f'Bearer {self.creds.token}'}

            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('point'):
                        print(f"✓ Found {len(data['point'])} data points!")
                        print(json.dumps(data, indent=2)[:800])
                        return data
                    else:
                        print(f"✗ No points")
                else:
                    print(f"✗ Status {response.status_code}")

            except Exception as e:
                print(f"✗ Error: {e}")

        return None

    def check_health_connect_sync(self):
        """Check if Health Connect is syncing to Google Fit"""
        print("\n" + "=" * 60)
        print("CHECKING HEALTH CONNECT SYNC")
        print("=" * 60)

        # Look for Samsung Health data source
        sources = self.list_data_sources()

        samsung_sources = [s for s in sources if 'samsung' in str(s).lower()]
        health_connect_sources = [s for s in sources if 'health' in str(s).lower()]

        if samsung_sources:
            print("\n✓ Found Samsung Health data sources:")
            for source in samsung_sources:
                print(f"  - {source.get('dataStreamId')}")
        else:
            print("\n✗ No Samsung Health data sources found")
            print("   This means Samsung Health is NOT syncing to Google Fit")

        if health_connect_sources:
            print("\n✓ Found Health Connect data sources:")
            for source in health_connect_sources:
                print(f"  - {source.get('dataStreamId')}")

    def run_all_tests(self):
        """Run all data discovery tests"""
        print("\n")
        print("=" * 60)
        print("HEALTH CONNECT DATA DISCOVERY")
        print("=" * 60)
        print("\nThis script will try multiple methods to find your health data\n")

        self.authenticate()

        # 1. List data sources
        self.list_data_sources()

        # 2. Check Health Connect sync
        self.check_health_connect_sync()

        # 3. Try getting sleep data different ways
        self.try_sleep_sessions()
        self.try_aggregate_sleep_data()
        self.try_dataset_read()

        print("\n" + "=" * 60)
        print("DISCOVERY COMPLETE")
        print("=" * 60)
        print("\nIf you see data above, we can use it!")
        print("If not, Samsung Health might not be syncing to Google Fit.")
        print("\nNext steps:")
        print("1. Check if Samsung Health → Google Fit sync is enabled")
        print("2. Or use CSV export method for guaranteed results")


if __name__ == "__main__":
    explorer = HealthDataExplorer()
    explorer.run_all_tests()
