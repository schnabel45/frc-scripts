#!/usr/bin/env python3
"""
FRC Fuel Scores Script (2026 Season)

Connects to the FRC Events API and pulls match results for a given event,
filtering for matches where either alliance scored between 500 and 550 fuel
(inclusive).

Usage:
    python frc_fuel_scores.py --event TXHOU
    python frc_fuel_scores.py --event TXHOU --username USER --token TOKEN
"""

from __future__ import annotations

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_URL = "https://frc-api.firstinspires.org/v3.0"
YEAR = 2026

LEVELS = ["qual"]

FUEL_MIN = 360
FUEL_MAX = 375


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pull FRC match fuel scores from the FRC Events API for 2026."
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


def fetch_matches(session: requests.Session, event: str, level: str) -> list:
    """Fetch match details for one tournament level."""
    url = f"{BASE_URL}/{YEAR}/matches/{event}"
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
    if response.status_code == 400:
        # Bad request - likely an invalid tournament level for this event
        # Skip this level gracefully
        return []
    response.raise_for_status()
    data = response.json()
    return data.get("Matches", [])


def fetch_match_scores(session: requests.Session, event: str, level: str) -> list:
    """Fetch detailed match scores from the scores API endpoint."""
    url = f"{BASE_URL}/{YEAR}/scores/{event}/{level}"
    response = session.get(url)
    if response.status_code == 401:
        print(
            "ERROR: Unauthorized. Provide valid --username and --token "
            "(or set FRC_API_USERNAME / FRC_API_TOKEN environment variables).",
            file=sys.stderr,
        )
        sys.exit(1)
    if response.status_code == 404:
        return []
    if response.status_code == 400:
        return []
    response.raise_for_status()
    data = response.json()
    return data.get("MatchScores", [])


def get_fuel_score(score_data: dict) -> int | None:
    """Extract fuel score from score data using hubScore.totalCount."""
    if not score_data:
        return None
    # The fuel score is in the hubScore.totalCount field
    hub_score = score_data.get("hubScore", {})
    if hub_score and "totalCount" in hub_score:
        value = hub_score["totalCount"]
        if isinstance(value, (int, float)):
            return int(value)
    return None


def filter_matches_by_fuel(match_scores: list) -> tuple[list, int, int]:
    """Filter matches where either alliance has fuel between FUEL_MIN and FUEL_MAX.
    
    Returns: (filtered_matches, total_red_fuel, total_blue_fuel)
    """
    filtered = []
    total_red_fuel = 0
    total_blue_fuel = 0
    
    if not match_scores:
        return filtered, total_red_fuel, total_blue_fuel
    
    for score in match_scores:
        match_number = score.get("matchNumber", "?")
        
        # Get alliance list and extract red and blue
        alliances = score.get("alliances", [])
        red_score_data = {}
        blue_score_data = {}
        
        for alliance in alliances:
            if alliance.get("alliance") == "Red":
                red_score_data = alliance
            elif alliance.get("alliance") == "Blue":
                blue_score_data = alliance
        
        red_fuel = get_fuel_score(red_score_data)
        blue_fuel = get_fuel_score(blue_score_data)
        
        # Add to totals
        if red_fuel is not None:
            total_red_fuel += red_fuel
        if blue_fuel is not None:
            total_blue_fuel += blue_fuel
        
        # Check if either alliance has fuel in the target range
        red_in_range = red_fuel is not None and FUEL_MIN <= red_fuel <= FUEL_MAX
        blue_in_range = blue_fuel is not None and FUEL_MIN <= blue_fuel <= FUEL_MAX
        
        if red_in_range or blue_in_range:
            filtered.append({
                "matchNumber": match_number,
                "redFuel": red_fuel,
                "blueFuel": blue_fuel,
                "redInRange": red_in_range,
                "blueInRange": blue_in_range,
            })
    
    return filtered, total_red_fuel, total_blue_fuel


def display_matches(matches: list, level_label: str) -> None:
    if not matches:
        print(f"  No matches found for {level_label}.\n")
        return

    col_w = [8, 15, 15]
    header = (
        f"{'Match':<{col_w[0]}} "
        f"{'Red Fuel':>{col_w[1]}} "
        f"{'Blue Fuel':>{col_w[2]}}"
    )
    separator = "-" * len(header)

    print(f"\n  {level_label} Matches (Fuel {FUEL_MIN}-{FUEL_MAX})")
    print(f"  {separator}")
    print(f"  {header}")
    print(f"  {separator}")

    for match in matches:
        match_number = str(match["matchNumber"])
        red_fuel = match["redFuel"] if match["redFuel"] is not None else "N/A"
        blue_fuel = match["blueFuel"] if match["blueFuel"] is not None else "N/A"
        
        # Mark which alliance was in range
        red_marker = " *" if match["redInRange"] else ""
        blue_marker = " *" if match["blueInRange"] else ""

        row = (
            f"{match_number:<{col_w[0]}} "
            f"{str(red_fuel) + red_marker:>{col_w[1]}} "
            f"{str(blue_fuel) + blue_marker:>{col_w[2]}}"
        )
        print(f"  {row}")

    print(f"  {separator}")
    print(f"  (* indicates fuel score in {FUEL_MIN}-{FUEL_MAX} range)\n")


def main():
    args = parse_args()
    session = get_session(args.username, args.token)

    print(f"\nFRC {YEAR} Event: {args.event.upper()}")
    print(f"Fuel Scores: {FUEL_MIN}-{FUEL_MAX}")
    print("=" * 60)

    # Fetch match scores from the scores API
    match_scores = fetch_match_scores(session, args.event.upper(), "qual")
    
    filtered_matches, total_red_fuel, total_blue_fuel = filter_matches_by_fuel(match_scores)
    
    display_matches(filtered_matches, "Qualification")

    print(f"Total matches with fuel {FUEL_MIN}-{FUEL_MAX}: {len(filtered_matches)}")
    print(f"Total red alliance fuel: {total_red_fuel}")
    print(f"Total blue alliance fuel: {total_blue_fuel}\n")


if __name__ == "__main__":
    main()
