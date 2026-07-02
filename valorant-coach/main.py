"""
CLI orchestrator. Run this before touching the dashboard.

Usage:
    python main.py --riot-id "Name#TAG" --region na
    python main.py --riot-id "Name#TAG" --region na --matches 5
    python main.py --riot-id "Name#TAG" --region na --dump-raw   # debug: print raw match JSON
"""
import argparse
import json
import sys

from riot_api.resolver import MatchResolver
from riot_api.client import RiotAPIError
from data.parser import parse_match
from data.storage import init_db, save_match, get_rounds_for_puuid
from analysis.coach import get_coaching_feedback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--riot-id", required=True, help="e.g. 'Sova Main#NA1'")
    ap.add_argument("--region", required=True, choices=["na", "eu", "ap", "kr", "latam", "br"])
    ap.add_argument("--matches", type=int, default=1, help="how many recent matches to pull")
    ap.add_argument("--dump-raw", action="store_true", help="print raw match JSON and exit (debug)")
    args = ap.parse_args()

    init_db()
    resolver = MatchResolver()

    try:
        print(f"Resolving {args.riot_id}...")
        puuid = resolver.get_puuid(args.riot_id, args.region)
        print(f"  puuid: {puuid}")

        print(f"Fetching {args.matches} recent match ID(s)...")
        match_ids = resolver.get_recent_match_ids(puuid, args.region, count=args.matches)
        if not match_ids:
            print("No matches found for this player/region.")
            sys.exit(1)

        for match_id in match_ids:
            print(f"\nFetching match {match_id}...")
            raw = resolver.get_match_details(match_id, args.region)

            if args.dump_raw:
                print(json.dumps(raw, indent=2)[:5000])  # first 5k chars — enough to check field names
                continue

            summary = parse_match(raw, puuid)
            print(f"  {summary.map_name} — {'WIN' if summary.match_won else 'LOSS'} "
                  f"{summary.final_score_won}-{summary.final_score_lost} as {summary.agent}")
            save_match(summary)

        if args.dump_raw:
            return

        print("\nGenerating coaching feedback from all stored rounds...")
        rounds = get_rounds_for_puuid(puuid)
        feedback = get_coaching_feedback(rounds)
        print("\n--- Coaching feedback ---")
        print(feedback)

    except RiotAPIError as e:
        print(f"\nRiot API error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
