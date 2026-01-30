# main.py
import argparse
import json
from datetime import datetime
from scraper import apis, web_scraper
from db import init_db, upsert_observation, list_unflagged, flag_and_save_summary
from summarize_gpt import summarize_history_for_location
import os

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=["openaq", "airnow", "scrape"], default="openaq")
    p.add_argument("--location", help="OpenAQ location name OR human-friendly name for records")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--start", help="YYYY-MM-DD")
    p.add_argument("--end", help="YYYY-MM-DD")
    p.add_argument("--parameter", default="pm25", help="pm25, pm10, no2, o3, etc.")
    return p.parse_args()

def run_fetch(args):
    if args.source == "openaq":
        records = apis.fetch_openaq_history(location=args.location, lat=args.lat, lon=args.lon, start=args.start, end=args.end, parameter=args.parameter, limit=1000)
    elif args.source == "airnow":
        if args.lat is None or args.lon is None:
            raise SystemExit("airnow requires --lat and --lon")
        records = apis.fetch_airnow_history(args.lat, args.lon, args.start, args.end)
    elif args.source == "scrape":
        # example: args.location used as URL and selectors could be configured; here we expect JSON config
        cfg = json.loads(args.location)
        records = web_scraper.scrape_station_page_history(cfg["url"], cfg["item_selector"], cfg["date_selector"], cfg["value_selector"], parameter=args.parameter)
    else:
        records = []

    for r in records:
        upsert_observation(r)
    print(f"Fetched and upserted {len(records)} records from {args.source}")

def run_summarize(limit_per_location: int = 200):
    # naive grouping by location: fetch unflagged rows, group, summarize with GPT
    rows = list_unflagged(limit=500)
    groups = {}
    for r in rows:
        loc = r["location"] or r["source"]
        groups.setdefault(loc, []).append(r)
    for loc, obs in groups.items():
        # sort by date
        obs_sorted = sorted(obs, key=lambda x: x.get("date_utc") or "")
        res = summarize_history_for_location(obs_sorted, loc, parameter=obs_sorted[0].get("parameter"))
        # mark these obs as flagged and save summary on them
        ids = [o["id"] for o in obs_sorted]
        flag_and_save_summary(ids, json.dumps(res))
        print(f"Location {loc[:60]} -> score {res.get('score'):.2f} exceedances {len(res.get('exceedances', []))}")

def main():
    init_db()
    args = parse_args()
    if args.start is None or args.end is None:
        today = datetime.utcnow().date()
        args.end = args.end or str(today)
        args.start = args.start or str(today)
    run_fetch(args)
    run_summarize()

if __name__ == "__main__":
    main()