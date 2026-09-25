import time
import requests
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Predefined monitoring zones
ZONES = {
    "downtown": {"name": "Downtown Core", "lat": 40.7128, "lon": -74.0060},
    "midtown": {"name": "Midtown Hub", "lat": 40.7549, "lon": -73.9840},
    "uptown": {"name": "Uptown North", "lat": 40.7831, "lon": -73.9712}
}

def fetch_live_weather(lat, lon):
    """Fetches real-time weather from Open-Meteo (Free, No API Key required)."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url, timeout=3).json()
        if "current_weather" in res:
            cw = res["current_weather"]
            temp = cw.get("temperature", "--")
            wind = cw.get("windspeed", "--")
            return f"Current Temp: {temp}°C | Wind Speed: {wind} km/h"
    except Exception as e:
        print(f"Weather API Error: {e}")
    return "Weather telemetry unavailable"

def fetch_live_311(lat, lon):
    """Fetches live 311 complaints near lat/lon from NYC Open Data (Free public API)."""
    try:
        # Search within approximately ~0.02 degrees (~2km radius)
        lat_min, lat_max = lat - 0.02, lat + 0.02
        lon_min, lon_max = lon - 0.02, lon + 0.02
        
        url = (
            f"https://data.cityofnewyork.us/resource/erm2-nwe9.json?"
            f"$where=latitude between {lat_min} and {lat_max} "
            f"and longitude between {lon_min} and {lon_max}"
            f"&$order=created_date DESC&$limit=5"
        )
        res = requests.get(url, timeout=4).json()
        
        events = []
        for item in res:
            complaint = item.get("complaint_type", "General Incident")
            descriptor = item.get("descriptor", "Reported activity")
            item_lat = float(item.get("latitude", lat))
            item_lon = float(item.get("longitude", lon))
            
            events.append({
                "source": "311",
                "text": f"{complaint}: {descriptor}",
                "lat": item_lat,
                "lon": item_lon,
                "timestamp": item.get("created_date", "")
            })
        return events
    except Exception as e:
        print(f"311 API Error: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/probe', methods=['GET'])
def dynamic_probe():
    """Live endpoint triggered when cursor/click moves to any new lat/lon."""
    try:
        lat = float(request.args.get('lat', 40.7128))
        lon = float(request.args.get('lon', -74.0060))
    except ValueError:
        return jsonify({"error": "Invalid coordinates"}), 400

    # Fetch live weather for the exact target coordinates
    weather_summary = fetch_live_weather(lat, lon)
    
    # Fetch live 311 events around the target coordinates
    incidents = fetch_live_311(lat, lon)

    # Dynamic status evaluation
    status = "Green"
    score = 98
    if len(incidents) >= 4:
        status = "Red"
        score = 62
    elif len(incidents) >= 2:
        status = "Amber"
        score = 81

    return jsonify({
        "lat": lat,
        "lon": lon,
        "status": status,
        "score": score,
        "weather": weather_summary,
        "incidents_count": len(incidents),
        "incidents": incidents
    })

@app.route('/api/pulse')
def pulse():
    """Aggregate zone telemetry for dashboard initialization."""
    zone_data = {}
    all_events = []

    for z_id, info in ZONES.items():
        weather_text = fetch_live_weather(info["lat"], info["lon"])
        incidents = fetch_live_311(info["lat"], info["lon"])
        
        all_events.append({
            "source": "weather",
            "text": f"{info['name']} - {weather_text}",
            "lat": info["lat"],
            "lon": info["lon"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        all_events.extend(incidents)

        status = "Green"
        score = 95
        if len(incidents) >= 4:
            status = "Red"
            score = 65
        elif len(incidents) >= 2:
            status = "Amber"
            score = 82

        zone_data[z_id] = {
            "name": info["name"],
            "lat": info["lat"],
            "lon": info["lon"],
            "status": status,
            "score": score,
            "summary": f"{weather_text}. {len(incidents)} active local reports."
        }

    return jsonify({
        "zones": zone_data,
        "recent_events": all_events
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)