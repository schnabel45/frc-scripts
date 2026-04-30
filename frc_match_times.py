#!/usr/bin/env python3
"""
FRC Match Times Script

Pulls all played matches from an FRC event and displays scheduled start time,
actual start time, actual end time, and the duration between actual start and end.
"""

import argparse
import os
import sys
from datetime import datetime, timezone

import requests
from requests.auth import HTTPBasicAuth

FRC_API_BASE = "https://frc-events.firstinspires.org/V2.0"
MATCH_LEVELS = ["Practice", "Qualification", "Playoff"]
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def parse_dt(value: str | None) -> datetime | None:
    """Parse a datetime string returned by the FRC Events API.

    The API returns ISO-8601-style strings such as:
      "2024-03-08T09:01:45"   (no timezone)
      "2024-03-08T09:01:45Z"  (UTC, trailing 'Z')
      "2024-03-08T09:01:45+00:00"  (UTC, numeric offset)
    All are converted to a naive datetime in local/API time by stripping the
    timezone designator before parsing.
    """
    if not value:
        return None
    # Normalize: remove trailing 'Z', then strip any timezone offset (+HH:MM or -HH:MM)
    # keeping only the date/time portion before any offset indicator.
    normalized = value.rstrip("Z")
    if "T" in normalized:
        date_part, time_part = normalized.split("T", 1)
        # Remove offset: find first '+' or '-' after position 0 in the time portion
        for i, ch in enumerate(time_part):
            if ch in ("+", "-") and i > 0:
                time_part = time_part[:i]
                break
        normalized = f"{date_part}T{time_part}"
    for fmt in (DATE_FORMAT, "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"


def fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "N/A"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    return f"{minutes}m {secs:02d}s"


def get_matches(session: requests.Session, year: int, event_code: str, level: str) -> list[dict]:
    """Fetch matches for a given tournament level."""
    url = f"{FRC_API_BASE}/{year}/matches/{event_code}"
    params = {"tournamentLevel": level}
    resp = session.get(url, params=params)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()
    return data.get("Matches", [])


def display_matches(matches: list[dict], level: str) -> None:
    """Print a formatted table of match timing information."""
    played = [m for m in matches if m.get("actualStartTime")]
    if not played:
        print(f"\n  No played matches found for {level} level.\n")
        return

    col_widths = {
        "match": 10,
        "scheduled": 21,
        "actual_start": 21,
        "actual_end": 21,
        "duration": 12,
    }
    header = (
        f"  {'Match':<{col_widths['match']}}"
        f"{'Scheduled Start':<{col_widths['scheduled']}}"
        f"{'Actual Start':<{col_widths['actual_start']}}"
        f"{'Actual End':<{col_widths['actual_end']}}"
        f"{'Duration':<{col_widths['duration']}}"
    )
    sep = "  " + "-" * (sum(col_widths.values()))

    print(f"\n{'='*60}")
    print(f"  {level} Matches")
    print(f"{'='*60}")
    print(header)
    print(sep)

    for match in sorted(played, key=lambda m: m.get("matchNumber", 0)):
        match_num = match.get("matchNumber", "?")
        scheduled = parse_dt(match.get("startTime"))
        actual_start = parse_dt(match.get("actualStartTime"))
        actual_end = parse_dt(match.get("postResultTime"))

        duration = None
        if actual_start and actual_end and actual_end >= actual_start:
            duration = (actual_end - actual_start).total_seconds()

        print(
            f"  {str(match_num):<{col_widths['match']}}"
            f"{fmt_dt(scheduled):<{col_widths['scheduled']}}"
            f"{fmt_dt(actual_start):<{col_widths['actual_start']}}"
            f"{fmt_dt(actual_end):<{col_widths['actual_end']}}"
            f"{fmt_duration(duration):<{col_widths['duration']}}"
        )

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull FRC match times from an event and display scheduling information."
    )
    parser.add_argument("--year", type=int, required=True, help="Season year (e.g. 2024)")
    parser.add_argument("--event", required=True, help="Event code (e.g. WAELL)")
    parser.add_argument(
        "--username",
        default=os.environ.get("FRC_API_USERNAME"),
        help="FRC Events API username (or set FRC_API_USERNAME env var)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("FRC_API_TOKEN"),
        help="FRC Events API token (or set FRC_API_TOKEN env var)",
    )
    args = parser.parse_args()

    if not args.username or not args.token:
        print(
            "Error: FRC API credentials are required.\n"
            "Set FRC_API_USERNAME and FRC_API_TOKEN environment variables, "
            "or pass --username and --token arguments.",
            file=sys.stderr,
        )
        sys.exit(1)

    session = requests.Session()
    session.auth = HTTPBasicAuth(args.username, args.token)
    session.headers.update({"Accept": "application/json"})

    print(f"\nFRC {args.year} Event: {args.event.upper()}")
    print(f"Fetching match data for all levels...")

    total_played = 0
    for level in MATCH_LEVELS:
        try:
            matches = get_matches(session, args.year, args.event.upper(), level)
        except requests.HTTPError as exc:
            print(f"  Warning: could not fetch {level} matches: {exc}", file=sys.stderr)
            continue

        played = [m for m in matches if m.get("actualStartTime")]
        total_played += len(played)
        display_matches(matches, level)

    print(f"Total played matches shown: {total_played}\n")


if __name__ == "__main__":
    main()
