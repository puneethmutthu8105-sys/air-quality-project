from flask import Flask, jsonify, render_template
import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = "ab77cda49320082c9e0741e68f57fc9f13319c01ad8cdaf1030c33922a42f88f"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/stations")
def get_stations():
    url = "https://api.openaq.org/v3/locations"
    headers = {"X-API-Key": API_KEY}
    params = {"coordinates": "12.9716,77.5946", "radius": 25000, "limit": 20}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    active_stations = []

    for station in data["results"]:
        last_seen_str = station["datetimeLast"]["utc"] if station["datetimeLast"] else None
        if last_seen_str:
            last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
            if last_seen > cutoff:
                active_stations.append({
                    "id": station["id"],
                    "name": station["name"],
                    "lat": station["coordinates"]["latitude"],
                    "lon": station["coordinates"]["longitude"],
                    "last_seen": last_seen_str
                })

    return jsonify(active_stations)


@app.route("/api/station/<int:location_id>")
def get_station_readings(location_id):
    headers = {"X-API-Key": API_KEY}

    try:
        location_url = f"https://api.openaq.org/v3/locations/{location_id}"
        location_response = requests.get(location_url, headers=headers, timeout=10)
        location_data = location_response.json()

        sensor_names = {}
        for sensor in location_data["results"][0]["sensors"]:
            sensor_names[sensor["id"]] = sensor["parameter"]["displayName"]

        latest_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
        latest_response = requests.get(latest_url, headers=headers, timeout=10)
        latest_data = latest_response.json()

        readings = []
        for reading in latest_data["results"]:
            sensor_id = reading["sensorsId"]
            readings.append({
                "pollutant": sensor_names.get(sensor_id, "Unknown"),
                "value": reading["value"],
                "datetime": reading["datetime"]["utc"]
            })

        return jsonify(readings)

    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not reach the air quality service."}), 503

    except (KeyError, IndexError):
        return jsonify({"error": "Unexpected data format from air quality service."}), 502


if __name__ == "__main__":
    app.run(debug=True)