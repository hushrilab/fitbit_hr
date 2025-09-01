# Fitbit Sense 2 → CSV (Post-Experiment Workflow)

This starter kit shows how to get **timestamped heart-rate data** from a Fitbit Sense 2 **after** your experiment and save it as a CSV aligned with your computer logs.

⚠️ Fitbit does **not** stream live HR data to a computer. This workflow is for **post-hoc export**. 
✅ Timestamps returned by the Fitbit Web API are in **UTC**; the script also converts them to your chosen local timezone.

---

## ✨ Features
- Exports **1-second intraday heart rate** (for Personal apps on your own account)  
- Falls back to **1-minute** resolution if 1-second not available  
- Outputs both **UTC** and **local timezone** timestamps  
- Simple command-line usage  
- Compatible with Ubuntu 20.04 (Python 3.8 via `backports.zoneinfo`)  

## 🚀 Setup (to do only once at the beginning)

### 1. Register a Fitbit Personal App
1. Go to [Fitbit Developer Portal](https://dev.fitbit.com/apps). 
2. Create a new app:
   - **Application Type:** Personal 
   - **Redirect URL:** `http://127.0.0.1:8080/callback` 
   - Other fields can be `http://localhost`. 
3. Save the app and note your **Client ID**.

---

### 2. Get an Access Token
1. Build an authorization URL (replace `YOUR_CLIENT_ID`):
```
https://www.fitbit.com/oauth2/authorize?response_type=token&client_id=YOUR_CLIENT_ID&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2Fcallback&scope=heartrate%20activity%20profile&expires_in=31536000
```

2. Open it in your browser, log in, and you’ll be redirected to:
```
http://127.0.0.1:8080/callback?utm_source=chatgpt.com#access_token=AAA.BBB.CCC&user_id=...&scope=
```

3. Copy **only** the token (`AAA.BBB.CCC`) — stop at the first `&`.

4. Test the token:
```bash
curl -H "Authorization: Bearer AAA.BBB.CCC" https://api.fitbit.com/1/user/-/profile.json

```
### Dependencies

For Ubuntu 20.04:
```bash
sudo apt update
sudo apt install -y python3-pip
pip3 install --user requests pandas backports.zoneinfo
```

Modify the following parameters in the script:
```
ACCESS_TOKEN=AAA.BBB.CCC
FITBIT_API_BASE=https://api.fitbit.com
```

## 📦 Usage
Fetch heart-rate data for a given date (after syncing your watch in the Fitbit mobile app):
```
python3 fetch_fitbit_hr.py --date 2025-09-01 --tz Asia/Tokyo --out hr_2025-09-01_tokyo.csv --token YOURTOKEN
```

### Arguments:
- `--date YYY-MM-DD`: Day to fetch (must be synced in the Fitbit app)

- `--tz ZONE` : Local timezone (e.g., Asia/Tokyo, America/Toronto). Defaults to system timezone.

- `--out FILE.csv` : Output filename (default: hr_<date>.csv)

- `--token YOURTOKEN` : Override token (else it uses the one in venv, if using venv)

### Output format
CSV columns:
- `timestamp_local`: Local time
- `timestamp_utc`: UTC time
- `bpm`: heart rate in beats per minute
- `source`: resolution (should be 1 min or 1 sec)

## 🔧 Troubleshooting

- 401 Unauthorized → Token expired/invalid. Get a fresh one.
- 403 on 1sec → Your account only allows 1-minute data. Script will auto-fallback.
- Empty CSV → Sync your watch in the Fitbit app first.
- Wrong times → Use the --tz flag for your local timezone.
