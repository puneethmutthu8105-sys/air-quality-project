import requests
from datetime import datetime, timedelta, timezone

API_KEY = "be931df175249909a14e0e16bef6d48226f524e2648d1c4a45448e545428092d"

url = "https://api.openaq.org/v3/locations"
headers = {"X-API-Key": API_KEY}
params = {"coordinates": "12.9716,77.5946", "radius": 25000, "limit": 20}

response = requests.get(url, headers=headers, params=params)
data = response.json()

cutoff = datetime.now(timezone.utc) - timedelta(days=7)

for station in data["results"]:
    last_seen_str = station["datetimeLast"]["utc"] if station["datetimeLast"] else None
    if last_seen_str:
        last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
        if last_seen > cutoff:
            print(station["name"], "→ last reading:", last_seen_str)