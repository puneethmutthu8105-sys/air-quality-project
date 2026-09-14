from flask import Flask, jsonify, render_template
import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("OPENAQ_API_KEY")


@app.route("/")
def home():
    return render_template("index.html")


CITIES = {
    "Amaravati": (16.5062, 80.6480),
    "Itanagar": (27.0844, 93.6053),
    "Guwahati": (26.1445, 91.7362),
    "Patna": (25.5941, 85.1376),
    "Raipur": (21.2514, 81.6296),
    "Panaji": (15.4909, 73.8278),
    "Gandhinagar": (23.2156, 72.6369),
    "Chandigarh": (30.7333, 76.7794),
    "Shimla": (31.1048, 77.1734),
    "Ranchi": (23.3441, 85.3096),
    "Bengaluru": (12.9716, 77.5946),
    "Thiruvananthapuram": (8.5241, 76.9366),
    "Bhopal": (23.2599, 77.4126),
    "Mumbai": (19.0760, 72.8777),
    "Imphal": (24.8170, 93.9368),
    "Shillong": (25.5788, 91.8933),
    "Aizawl": (23.7271, 92.7176),
    "Kohima": (25.6751, 94.1086),
    "Bhubaneswar": (20.2961, 85.8245),
    "Jaipur": (26.9124, 75.7873),
    "Gangtok": (27.3389, 88.6065),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Agartala": (23.8315, 91.2868),
    "Lucknow": (26.8467, 80.9462),
    "Dehradun": (30.3165, 78.0322),
    "Kolkata": (22.5726, 88.3639),
    "New Delhi": (28.6139, 77.2090),
}


@app.route("/api/stations")
def get_stations():
    headers = {"X-API-Key": API_KEY}
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    active_stations = []
    seen_ids = set()

    for city_name, (lat, lon) in CITIES.items():
        url = "https://api.openaq.org/v3/locations"
        params = {"coordinates": f"{lat},{lon}", "radius": 25000, "limit": 20}

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        for station in data.get("results", []):
            if station["id"] in seen_ids:
                continue
            seen_ids.add(station["id"])

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