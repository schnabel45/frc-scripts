#!/usr/bin/env python3
"""
FRC Match Times Script

Connects to the FRC Events API and pulls match schedule/results for a given
event, displaying scheduled start time, actual start time, actual end time,
and the duration between actual start and end for every played match.

Usage:
    python frc_match_times.py --year 2024 --event TXHOU
    python frc_match_times.py --year 2024 --event TXHOU --username USER --token TOKEN
"""

import argparse
import os
import sys
from datetime import datetime, timezone

import requests

BASE_URL = "https://frc-api.firstinspires.org/v3.0"

LEVELS = ["qual", "playoff"]
LEVEL_LABELS = {
    "qual": "Qualification",
    "playoff": "Playoff",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pull FRC match times from the FRC Events API."
    )
    parser.add_argument(
        "--year",
        required=True,
        type=int,
        help="Season year (e.g. 2024)",
    )
    parser.add_argument(
        "--event",
        required=True,
        type=str,
        help="Event code (e.g. TXHOU)",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("FRC_API_USERNAME", ""),
        help="FRC API username (or set FRC_API_USERNAME env var)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("FRC_API_TOKEN", ""),
        help="FRC API authorization token (or set FRC_API_TOKEN env var)",
    )
    return parser.parse_args()


def get_session(username: str, token: str) -> requests.Session:
    session = requests.Session()
    if username and token:
        session.auth = (username, token)
    session.headers.update({"Accept": "application/json"})
    return session


def fetch_matches(session: requests.Session, year: int, event: str, level: str) -> list:
    """Fetch match results for one tournament level."""
    url = f"{BASE_URL}/{year}/matches/{event}"
    params = {"tournamentLevel": level}
    response = session.get(url, params=params)
    if response.status_code == 401:
        print(
            "ERROR: Unauthorized. Provide valid --username and --token "
            "(or set FRC_API_USERNAME / FRC_API_TOKEN environment variables).",
            file=sys.stderr,
        )
        sys.exit(1)
    if response.status_code == 404:
        # Event or level not found – return empty list gracefully
        return []
    response.raise_for_status()
    data = response.json()
    return data.get("Matches", [])


def parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string returned by the FRC API."""
    if not value:
        return None
    # The API returns strings like "2024-03-08T09:00:00" (no timezone marker)
    # or "2024-03-08T09:00:00Z". Normalize both forms.
    value = value.rstrip("Z")
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def format_dt(dt: datetime | None) -> str:
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "N/A"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs:02d}s"


def display_matches(matches: list, level_label: str) -> None:
    if not matches:
        print(f"  No matches found for {level_label}.\n")
        return

    col_w = [6, 26, 26, 26, 14]
    header = (
        f"{'Match':<{col_w[0]}} "
        f"{'Scheduled Start':<{col_w[1]}} "
        f"{'Actual Start':<{col_w[2]}} "
        f"{'Actual End':<{col_w[3]}} "
        f"{'Duration':>{col_w[4]}}"
    )
    separator = "-" * len(header)

    print(f"\n  {level_label} Matches")
    print(f"  {separator}")
    print(f"  {header}")
    print(f"  {separator}")

    for match in matches:
        match_number = match.get("matchNumber", "?")
        scheduled_start = parse_dt(match.get("startTime"))
        actual_start = parse_dt(match.get("actualStartTime"))
        actual_end = parse_dt(match.get("postResultTime"))

        duration: float | None = None
        if actual_start and actual_end:
            delta = actual_end - actual_start
            duration = delta.total_seconds()

        row = (
            f"{str(match_number):<{col_w[0]}} "
            f"{format_dt(scheduled_start):<{col_w[1]}} "
            f"{format_dt(actual_start):<{col_w[2]}} "
            f"{format_dt(actual_end):<{col_w[3]}} "
            f"{format_duration(duration):>{col_w[4]}}"
        )
        print(f"  {row}")

    print(f"  {separator}\n")


def main():
    args = parse_args()
    session = get_session(args.username, args.token)

    print(f"\nFRC {args.year} Event: {args.event.upper()}")
    print("=" * 60)

    for level in LEVELS:
        matches = fetch_matches(session, args.year, args.event.upper(), level)
        display_matches(matches, LEVEL_LABELS[level])


if __name__ == "__main__":
    main()
