#!/usr/bin/env python3
"""
FRC Match Scores CSV Export Script (2026 Season)

Connects to the FRC Events API and pulls all completed qualification match
scores for a given event, exporting full score details to a CSV file.

Usage:
    python frc_export_scores.py --event TXHOU
    python frc_export_scores.py --event TXHOU --output scores.csv
    python frc_export_scores.py --event TXHOU --username USER --token TOKEN
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_URL = "https://frc-api.firstinspires.org/v3.0"
YEAR = 2026


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export FRC qualification match scores to CSV for 2026."
    )
    parser.add_argument(
        "--event",
        required=True,
        type=str,
        help="Event code (e.g. TXHOU)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: <event>_scores.csv)",
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


def fetch_match_scores(session: requests.Session, event: str) -> list:
    """Fetch all qualification match scores from the scores API endpoint."""
    url = f"{BASE_URL}/{YEAR}/scores/{event}/qual"
    response = session.get(url)
    if response.status_code == 401:
        print(
            "ERROR: Unauthorized. Provide valid --username and --token "
            "(or set FRC_API_USERNAME / FRC_API_TOKEN environment variables).",
            file=sys.stderr,
        )
        sys.exit(1)
    if response.status_code == 404:
        print(f"ERROR: Event '{event}' not found.", file=sys.stderr)
        sys.exit(1)
    if response.status_code == 400:
        print("ERROR: Bad request to scores API.", file=sys.stderr)
        sys.exit(1)
    response.raise_for_status()
    data = response.json()
    return data.get("MatchScores", [])


def flatten_alliance(alliance_data: dict, prefix: str) -> dict:
    """Flatten all alliance score fields into a prefixed dict for CSV output."""
    row = {
        f"{prefix}_totalPoints": alliance_data.get("totalPoints"),
        f"{prefix}_foulPoints": alliance_data.get("foulPoints"),
        f"{prefix}_adjustPoints": alliance_data.get("adjustPoints"),
        f"{prefix}_totalAutoPoints": alliance_data.get("totalAutoPoints"),
        f"{prefix}_totalTeleopPoints": alliance_data.get("totalTeleopPoints"),
        f"{prefix}_endGameTowerPoints": alliance_data.get("endGameTowerPoints"),
        f"{prefix}_totalTowerPoints": alliance_data.get("totalTowerPoints"),
        f"{prefix}_autoTowerPoints": alliance_data.get("autoTowerPoints"),
        f"{prefix}_autoTowerRobot1": alliance_data.get("autoTowerRobot1"),
        f"{prefix}_autoTowerRobot2": alliance_data.get("autoTowerRobot2"),
        f"{prefix}_autoTowerRobot3": alliance_data.get("autoTowerRobot3"),
        f"{prefix}_endGameTowerRobot1": alliance_data.get("endGameTowerRobot1"),
        f"{prefix}_endGameTowerRobot2": alliance_data.get("endGameTowerRobot2"),
        f"{prefix}_endGameTowerRobot3": alliance_data.get("endGameTowerRobot3"),
        f"{prefix}_energizedAchieved": alliance_data.get("energizedAchieved"),
        f"{prefix}_superchargedAchieved": alliance_data.get("superchargedAchieved"),
        f"{prefix}_traversalAchieved": alliance_data.get("traversalAchieved"),
        f"{prefix}_minorFoulCount": alliance_data.get("minorFoulCount"),
        f"{prefix}_majorFoulCount": alliance_data.get("majorFoulCount"),
        f"{prefix}_g206Penalty": alliance_data.get("g206Penalty"),
        f"{prefix}_rp": alliance_data.get("rp"),
        f"{prefix}_penalties": alliance_data.get("penalties"),
    }

    # Flatten hubScore fields with hub_ prefix
    hub = alliance_data.get("hubScore", {})
    if hub:
        for key, value in hub.items():
            row[f"{prefix}_hub_{key}"] = value

    return row


def scores_to_rows(match_scores: list) -> list[dict]:
    """Convert match score objects to flat rows, one row per match."""
    rows = []
    for score in match_scores:
        row = {
            "matchNumber": score.get("matchNumber"),
            "matchLevel": score.get("matchLevel", "Qualification"),
        }

        for alliance_data in score.get("alliances", []):
            alliance = alliance_data.get("alliance", "").lower()
            if alliance in ("red", "blue"):
                row.update(flatten_alliance(alliance_data, alliance))

        rows.append(row)

    return rows


def write_csv(rows: list[dict], output_path: str) -> None:
    if not rows:
        print("No data to write.", file=sys.stderr)
        return

    # Collect all unique fieldnames preserving insertion order
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()
    event = args.event.upper()
    output_path = args.output or f"{event}_scores.csv"

    session = get_session(args.username, args.token)

    print(f"\nFRC {YEAR} Event: {event}")
    print(f"Fetching qualification match scores...")

    match_scores = fetch_match_scores(session, event)

    if not match_scores:
        print("No match scores found.")
        sys.exit(0)

    rows = scores_to_rows(match_scores)
    write_csv(rows, output_path)

    print(f"Exported {len(match_scores)} matches ({len(rows)} rows) to: {output_path}\n")


if __name__ == "__main__":
    main()
