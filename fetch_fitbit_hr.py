#!/usr/bin/env python3
import os, sys, argparse, requests, csv
from datetime import datetime, timezone

# Python 3.8 compatibility for timezones
try:
    from zoneinfo import ZoneInfo          # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # pip install --user backports.zoneinfo

def load_env(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
API_BASE = os.environ.get("FITBIT_API_BASE", "https://api.fitbit.com")

def get_token(cli_token=None):
    token = cli_token or os.environ.get("ACCESS_TOKEN")
    if not token:
        print("ERROR: ACCESS_TOKEN not found. Pass --token or set ACCESS_TOKEN in .env", file=sys.stderr)
        sys.exit(1)
    return token.strip()

def headers(token):
    return {"Authorization": f"Bearer {token}"}

def assert_token(token):
    url = f"{API_BASE}/1/user/-/profile.json"
    r = requests.get(url, headers=headers(token), timeout=20)
    if r.status_code == 401:
        raise SystemExit(f"401 Unauthorized on /profile. Token invalid/expired.\nServer says: {r.text}")
    if r.status_code >= 400:
        raise SystemExit(f"{r.status_code} error on /profile.\nServer says: {r.text}")

def fetch_hr(token, date_str, level="1sec"):
    url = f"{API_BASE}/1/user/-/activities/heart/date/{date_str}/1d/{level}.json"
    r = requests.get(url, headers=headers(token), timeout=30)
    if r.status_code == 401:
        raise SystemExit(f"401 Unauthorized on {url}\nServer says: {r.text}\nGet a fresh token.")
    if r.status_code == 403 and level == "1sec":
        # No 1sec intraday access — fall back to 1min
        url_min = f"{API_BASE}/1/user/-/activities/heart/date/{date_str}/1d/1min.json"
        r2 = requests.get(url_min, headers=headers(token), timeout=30)
        if r2.status_code >= 400:
            raise SystemExit(f"{r2.status_code} error on {url_min}\nServer says: {r2.text}")
        return r2.json(), "1min"
    if r.status_code >= 400:
        raise SystemExit(f"{r.status_code} error on {url}\nServer says: {r.text}")
    return r.json(), "1sec"

def parse_args():
    ap = argparse.ArgumentParser(description="Fetch Fitbit intraday heart rate and save CSV.")
    ap.add_argument("--date", required=True, help="Date in YYYY-MM-DD (the experiment day).")
    ap.add_argument("--tz", default=None, help="IANA timezone (e.g., Asia/Tokyo). Defaults to system tz.")
    ap.add_argument("--out", default=None, help="Output CSV (default: hr_<date>.csv).")
    ap.add_argument("--token", default=None, help="Access token override (else use ACCESS_TOKEN from .env).")
    return ap.parse_args()

def main():
    args = parse_args()
    token = get_token(args.token)
    out_path = args.out or f"hr_{args.date}.csv"
    tz = ZoneInfo(args.tz) if args.tz else datetime.now().astimezone().tzinfo

    # Verify token
    assert_token(token)

    # Fetch HR data
    data, level = fetch_hr(token, args.date, "1sec")
    intraday = data.get("activities-heart-intraday", {}).get("dataset", [])

    # Build rows
    rows = []
    for d in intraday:
        t = d["time"]  # "HH:MM:SS" or "HH:MM"
        if len(t) == 5:
            t += ":00"
        dt_utc = datetime.fromisoformat(args.date + "T" + t).replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone(tz)
        rows.append({
            "timestamp_local": dt_local.isoformat(),
            "timestamp_utc": dt_utc.isoformat(),
            "bpm": d["value"],
            "source": level,
        })

    # Save CSV
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp_local","timestamp_utc","bpm","source"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path} (resolution: {level})")

if __name__ == "__main__":
    main()
