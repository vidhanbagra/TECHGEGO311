from app.config import ZONES

def calculate_zone_pulse(events):
    """Computes pulse intensity and hedges correlation language."""
    zone_status = {}
    
    for z_id, z_info in ZONES.items():
        z_events = [e for e in events if e["zone_id"] == z_id]
        score = min(100, sum(e["severity"] * 12 for e in z_events))
        
        sources = set(e["source"] for e in z_events)
        types = [e["type"] for e in z_events]
        
        # Epistemic hedging summaries
        if "weather" in sources and "water_leak" in types:
            summary = f"Elevated water complaints coincide with active weather alerts in {z_info['name']}. Possible link; no confirmed causation."
        elif "traffic_signal" in types:
            summary = f"Infrastructure issues (traffic signals) detected in {z_info['name']}. Traffic delays likely elevated."
        elif score > 50:
            summary = f"Multiple non-critical incidents reported in {z_info['name']}. Pulse intensity is elevated."
        else:
            summary = f"{z_info['name']} is currently operating under normal baseline conditions."
            
        zone_status[z_id] = {
            "name": z_info["name"],
            "score": score,
            "status": "Red" if score > 65 else "Amber" if score > 30 else "Green",
            "lat": z_info["lat"],
            "lon": z_info["lon"],
            "summary": summary
        }
    return zone_status