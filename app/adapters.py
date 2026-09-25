import httpx, random, uuid
from datetime import datetime, timezone
from app.config import ZONES

async def fetch_weather_event():
    """Fetches real current weather from Open-Meteo (zero-key)."""
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&current_weather=true"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=5.0)
            data = res.json().get("current_weather", {})
            code = data.get("weathercode", 0)
            
            cond = "Rain / Storm" if code in [51, 61, 80, 95] else "Clear / Normal"
            severity = 4 if code in [51, 61, 80, 95] else 1
            
            return {
                "id": str(uuid.uuid4()),
                "source": "weather",
                "type": cond,
                "severity": severity,
                "lat": 40.7128,
                "lon": -74.0060,
                "zone_id": "zone_downtown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "text": f"Current condition: {cond}, Temp: {data.get('temperature', 20)}°C"
            }
    except Exception:
        return None  # Fail gracefully without breaking ingestion pipeline

def generate_mock_incidents():
    """Simulates 311 and transit stream pulses."""
    incidents = []
    types_311 = [("pothole", 2), ("noise_complaint", 1), ("water_leak", 3), ("traffic_signal", 4)]
    
    for z_id, z_data in ZONES.items():
        if random.random() > 0.4:
            t_name, sev = random.choice(types_311)
            incidents.append({
                "id": str(uuid.uuid4()),
                "source": "311",
                "type": t_name,
                "severity": sev,
                "lat": z_data["lat"] + random.uniform(-0.005, 0.005),
                "lon": z_data["lon"] + random.uniform(-0.005, 0.005),
                "zone_id": z_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "text": f"Reported {t_name.replace('_', ' ')} in {z_data['name']}"
            })
    return incidents