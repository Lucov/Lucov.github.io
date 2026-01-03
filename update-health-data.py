#!/usr/bin/env python3
"""
Samsung Health Data Updater

This script processes Samsung Health CSV exports and updates the health-data.json file.

Usage:
    python update-health-data.py --sleep sleep_data.csv --heart heart_rate.csv --steps steps.csv

To export data from Samsung Health:
    1. Open Samsung Health app
    2. Go to Menu (☰) > Settings
    3. Tap "Download my data"
    4. Select data types (Sleep, Heart Rate, Steps, Stress)
    5. Choose date range
    6. Download and extract the ZIP file
"""

import json
import csv
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import statistics


class HealthDataProcessor:
    def __init__(self):
        self.data = {
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
            "dataSource": "Samsung Health CSV",
            "dailyStats": {
                "date": datetime.now().strftime("%Y-%m-%d"),
            },
            "weeklyTrends": {}
        }
        self.diagnostics = {
            'fetchTime': datetime.utcnow().isoformat() + "Z",
            'dataProcessed': {},
            'errors': []
        }

    def process_sleep_data(self, filepath: str):
        """Process Samsung Health sleep CSV export"""
        if not Path(filepath).exists():
            error_msg = f"Sleep data file not found: {filepath}"
            print(f"Warning: {error_msg}")
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['sleep'] = False
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                sleep_records = list(reader)

            if not sleep_records:
                error_msg = "No sleep data found in CSV file"
                print(f"Warning: {error_msg}")
                self.diagnostics['errors'].append(error_msg)
                self.diagnostics['dataProcessed']['sleep'] = False
                return

            # Get most recent sleep record
            latest = sleep_records[-1]

            # Parse sleep data (adjust field names based on actual Samsung Health CSV)
            # These are common field names - you may need to adjust based on your export
            self.data["dailyStats"]["sleep"] = {
                "duration": self._parse_duration(latest.get("Sleep time", "0")),
                "score": int(latest.get("Sleep score", 87)),
                "deepSleep": self._parse_duration(latest.get("Deep sleep", "0")),
                "remSleep": self._parse_duration(latest.get("REM sleep", "0")),
                "lightSleep": self._parse_duration(latest.get("Light sleep", "0")),
                "bedTime": self._parse_time(latest.get("Bedtime", "23:30")),
                "wakeTime": self._parse_time(latest.get("Wake time", "07:00"))
            }

            # Extract energy score if available (may be in same CSV or separate)
            energy_score = latest.get("Energy score") or latest.get("Energy") or latest.get("energy_score")
            if energy_score:
                try:
                    score = int(energy_score)
                    level = "High Energy" if score >= 80 else "Good" if score >= 70 else "Moderate" if score >= 60 else "Low"
                    self.data["dailyStats"]["energy"] = {
                        "score": score,
                        "level": level
                    }
                except (ValueError, TypeError):
                    pass

            # Calculate weekly average
            recent_records = sleep_records[-7:] if len(sleep_records) >= 7 else sleep_records
            sleep_scores = [int(r.get("Sleep score", 87)) for r in recent_records if r.get("Sleep score")]
            energy_scores = []
            for r in recent_records:
                e_score = r.get("Energy score") or r.get("Energy") or r.get("energy_score")
                if e_score:
                    try:
                        energy_scores.append(int(e_score))
                    except (ValueError, TypeError):
                        pass
            durations = [self._parse_duration(r.get("Sleep time", "0")) for r in recent_records]

            if sleep_scores:
                self.data["weeklyTrends"]["averageSleepScore"] = round(statistics.mean(sleep_scores))
            if energy_scores:
                self.data["weeklyTrends"]["averageEnergyScore"] = round(statistics.mean(energy_scores))
            if durations:
                self.data["weeklyTrends"]["averageSleepDuration"] = round(statistics.mean(durations), 1)

            self.diagnostics['dataProcessed']['sleep'] = True
            print(f"✓ Processed sleep data: {len(sleep_records)} records")

        except Exception as e:
            error_msg = f"Error processing sleep data: {e}"
            print(error_msg)
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['sleep'] = False

    def process_heart_rate_data(self, filepath: str):
        """Process Samsung Health heart rate CSV export"""
        if not Path(filepath).exists():
            error_msg = f"Heart rate data file not found: {filepath}"
            print(f"Warning: {error_msg}")
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['heartRate'] = False
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                hr_records = list(reader)

            if not hr_records:
                error_msg = "No heart rate data found in CSV file"
                print(f"Warning: {error_msg}")
                self.diagnostics['errors'].append(error_msg)
                self.diagnostics['dataProcessed']['heartRate'] = False
                return

            # Get today's records
            today = datetime.now().strftime("%Y-%m-%d")
            today_records = [r for r in hr_records if today in r.get("Date", "")]

            if today_records:
                hr_values = [int(r.get("Heart rate", 70)) for r in today_records if r.get("Heart rate")]

                if hr_values:
                    self.data["dailyStats"]["heartRate"] = {
                        "resting": min(hr_values),
                        "average": round(statistics.mean(hr_values)),
                        "max": max(hr_values),
                        "min": min(hr_values)
                    }

                    # Weekly resting HR average
                    recent_records = hr_records[-100:] if len(hr_records) >= 100 else hr_records
                    recent_hr = [int(r.get("Heart rate", 70)) for r in recent_records if r.get("Heart rate")]
                    if recent_hr:
                        # Approximate resting HR as lowest 10th percentile
                        sorted_hr = sorted(recent_hr)
                        resting_hrs = sorted_hr[:len(sorted_hr)//10] if len(sorted_hr) > 10 else sorted_hr
                        self.data["weeklyTrends"]["averageRestingHR"] = round(statistics.mean(resting_hrs))

            self.diagnostics['dataProcessed']['heartRate'] = True
            print(f"✓ Processed heart rate data: {len(hr_records)} records")

        except Exception as e:
            error_msg = f"Error processing heart rate data: {e}"
            print(error_msg)
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['heartRate'] = False

    def process_activity_data(self, filepath: str):
        """Process Samsung Health steps/activity CSV export"""
        if not Path(filepath).exists():
            error_msg = f"Activity data file not found: {filepath}"
            print(f"Warning: {error_msg}")
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['activity'] = False
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                activity_records = list(reader)

            if not activity_records:
                error_msg = "No activity data found in CSV file"
                print(f"Warning: {error_msg}")
                self.diagnostics['errors'].append(error_msg)
                self.diagnostics['dataProcessed']['activity'] = False
                return

            latest = activity_records[-1]

            self.data["dailyStats"]["activity"] = {
                "steps": int(latest.get("Step count", 8000)),
                "calories": int(latest.get("Calories", 2000)),
                "activeMinutes": int(latest.get("Active time", 30))
            }

            # Weekly average steps
            recent_records = activity_records[-7:] if len(activity_records) >= 7 else activity_records
            steps = [int(r.get("Step count", 0)) for r in recent_records if r.get("Step count")]
            if steps:
                self.data["weeklyTrends"]["averageSteps"] = round(statistics.mean(steps))

            self.diagnostics['dataProcessed']['activity'] = True
            print(f"✓ Processed activity data: {len(activity_records)} records")

        except Exception as e:
            error_msg = f"Error processing activity data: {e}"
            print(error_msg)
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['activity'] = False

    def process_stress_data(self, filepath: str):
        """Process Samsung Health stress CSV export"""
        if not Path(filepath).exists():
            error_msg = f"Stress data file not found: {filepath}"
            print(f"Warning: {error_msg}")
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['stress'] = False
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stress_records = list(reader)

            if not stress_records:
                error_msg = "No stress data found in CSV file"
                print(f"Warning: {error_msg}")
                self.diagnostics['errors'].append(error_msg)
                self.diagnostics['dataProcessed']['stress'] = False
                return

            today = datetime.now().strftime("%Y-%m-%d")
            today_records = [r for r in stress_records if today in r.get("Date", "")]

            if today_records:
                stress_values = [int(r.get("Stress", 35)) for r in today_records if r.get("Stress")]
                if stress_values:
                    avg_stress = round(statistics.mean(stress_values))
                    level = "Low" if avg_stress < 40 else "Medium" if avg_stress < 70 else "High"

                    self.data["dailyStats"]["stress"] = {
                        "average": avg_stress,
                        "level": level
                    }

            self.diagnostics['dataProcessed']['stress'] = True
            print(f"✓ Processed stress data: {len(stress_records)} records")

        except Exception as e:
            error_msg = f"Error processing stress data: {e}"
            print(error_msg)
            self.diagnostics['errors'].append(error_msg)
            self.diagnostics['dataProcessed']['stress'] = False

    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to hours (e.g., '7h 30m' -> 7.5)"""
        try:
            hours = 0
            minutes = 0

            if 'h' in duration_str:
                parts = duration_str.split('h')
                hours = int(parts[0].strip())
                if len(parts) > 1 and 'm' in parts[1]:
                    minutes = int(parts[1].replace('m', '').strip())
            elif 'm' in duration_str:
                minutes = int(duration_str.replace('m', '').strip())
            elif ':' in duration_str:
                # Handle HH:MM format
                h, m = duration_str.split(':')
                hours = int(h)
                minutes = int(m)
            else:
                # Assume it's in minutes
                minutes = int(float(duration_str))

            return round(hours + minutes / 60, 1)
        except:
            return 7.5  # Default

    def _parse_time(self, time_str: str) -> str:
        """Parse and format time string"""
        try:
            # Try to parse various time formats
            for fmt in ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p']:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    return dt.strftime('%H:%M')
                except:
                    continue
            return time_str
        except:
            return time_str

    def save_json(self, output_path: str = "health-data.json"):
        """Save processed data to JSON file"""
        # Validate that we have at least some data
        has_data = any([
            'sleep' in self.data['dailyStats'],
            'heartRate' in self.data['dailyStats'],
            'activity' in self.data['dailyStats'],
            'energy' in self.data['dailyStats']
        ])

        if not has_data:
            error_msg = "No health data was successfully processed. File will not be updated."
            print(f"\n✗ {error_msg}")
            self.diagnostics['errors'].append(error_msg)
            self.save_diagnostics(success=False)
            return False

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            print(f"\n✓ Health data saved to {output_path}")
            print(f"  Last updated: {self.data['lastUpdated']}")
            self.save_diagnostics(success=True)
            return True
        except Exception as e:
            error_msg = f"Error saving JSON: {e}"
            print(error_msg)
            self.diagnostics['errors'].append(error_msg)
            self.save_diagnostics(success=False)
            return False

    def save_diagnostics(self, success: bool):
        """Save diagnostic information"""
        self.diagnostics['success'] = success
        try:
            with open('health-data-diagnostics.json', 'w', encoding='utf-8') as f:
                json.dump(self.diagnostics, f, indent=2)
            print(f"📊 Diagnostics saved to health-data-diagnostics.json")
        except Exception as e:
            print(f"Warning: Could not save diagnostics: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Update health-data.json from Samsung Health CSV exports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Update with all data types
    python update-health-data.py --sleep sleep.csv --heart heart.csv --steps steps.csv --stress stress.csv

    # Update only sleep data
    python update-health-data.py --sleep sleep.csv

    # Specify output file
    python update-health-data.py --sleep sleep.csv --output custom-data.json

How to export from Samsung Health:
    1. Open Samsung Health app
    2. Menu (☰) > Settings > Download my data
    3. Select data types and date range
    4. Download and extract ZIP
    5. Find CSV files in extracted folder
        """
    )

    parser.add_argument('--sleep', help='Path to sleep data CSV file')
    parser.add_argument('--heart', help='Path to heart rate data CSV file')
    parser.add_argument('--steps', help='Path to steps/activity data CSV file')
    parser.add_argument('--stress', help='Path to stress data CSV file')
    parser.add_argument('--output', default='health-data.json', help='Output JSON file path')

    args = parser.parse_args()

    if not any([args.sleep, args.heart, args.steps, args.stress]):
        parser.print_help()
        print("\nError: Please provide at least one data file")
        return

    print("Samsung Health Data Updater")
    print("=" * 50)

    processor = HealthDataProcessor()

    if args.sleep:
        processor.process_sleep_data(args.sleep)

    if args.heart:
        processor.process_heart_rate_data(args.heart)

    if args.steps:
        processor.process_activity_data(args.steps)

    if args.stress:
        processor.process_stress_data(args.stress)

    if processor.save_json(args.output):
        print("\n✓ Done! Refresh your blog to see updated health stats.")
    else:
        print("\n✗ Failed to update health data. Check errors above.")


if __name__ == "__main__":
    main()
