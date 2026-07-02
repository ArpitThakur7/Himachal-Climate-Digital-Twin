# ============================================
# PROJECT SCOPE — DO NOT CHANGE
# Districts : Mandi, Kullu, Chamba
# Period    : Live data
# Sources   : OpenWeather + Tomorrow.io
# File      : live/imd_live.py
# ============================================

import os
import requests
import json
from datetime import datetime

# ── API KEYS — loaded from environment ──────
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "your_key_here")
TOMORROW_KEY    = os.getenv("TOMORROW_KEY", "your_key_here")

# ── district coordinates ─────────────────────
DISTRICTS = {
    "Mandi":  {"lat": 31.7048, "lon": 76.9320},
    "Kullu":  {"lat": 31.9579, "lon": 77.1095},
    "Chamba": {"lat": 32.5531, "lon": 76.1258}
}

OUT = r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed"

# ── IMD thresholds ───────────────────────────
def classify(mm):
    if mm >= 204.5: return "Extremely Heavy"
    if mm >= 115.6: return "Very Heavy"
    if mm >=  64.5: return "Heavy"
    if mm >=  35.5: return "Rather Heavy"
    if mm >=  15.6: return "Moderate"
    return "Normal"

def alert_level(mm):
    if mm >= 115.6: return "EMERGENCY"
    if mm >=  64.5: return "WARNING"
    if mm >=  35.5: return "WATCH"
    return "NORMAL"

def generate_sms(district, level, mm, category):
    msgs = {
        "EMERGENCY": (
            f"EMERGENCY: {district} district — "
            f"{mm}mm rain expected ({category}). "
            f"Evacuate low-lying areas immediately. "
            f"Avoid all river crossings."
        ),
        "WARNING": (
            f"WARNING: {district} district — "
            f"{mm}mm rain expected ({category}). "
            f"Avoid rivers and unstable slopes. "
            f"Keep emergency contacts ready."
        ),
        "WATCH": (
            f"WATCH: {district} district — "
            f"{mm}mm rain possible. "
            f"Stay alert and monitor updates."
        ),
        "NORMAL": (
            f"{district} district — "
            f"Normal conditions. {mm}mm expected today."
        )
    }
    return msgs.get(level, "No data available.")

# ════════════════════════════════════════════
# OPENWEATHER — current + 5 day forecast
# ════════════════════════════════════════════
def fetch_openweather(name, lat, lon):
    print(f"\n  [OpenWeather] Fetching {name}...")
    try:
        current_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}"
            f"&appid={OPENWEATHER_KEY}"
            f"&units=metric"
        )
        cur = requests.get(current_url, timeout=10)
        cur.raise_for_status()
        cur_data = cur.json()

        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"lat={lat}&lon={lon}"
            f"&appid={OPENWEATHER_KEY}"
            f"&units=metric"
            f"&cnt=40"
        )
        fct = requests.get(forecast_url, timeout=10)
        fct.raise_for_status()
        fct_data = fct.json()

        rain_1h = cur_data.get("rain", {}).get("1h", 0) or 0
        rain_3h = cur_data.get("rain", {}).get("3h", 0) or 0

        day_totals = {}
        for item in fct_data.get("list", []):
            date = item["dt_txt"].split(" ")[0]
            rain = item.get("rain", {}).get("3h", 0) or 0
            day_totals[date] = day_totals.get(date, 0) + rain

        forecast_days = [
            {"date": d, "mm": round(v, 1)}
            for d, v in sorted(day_totals.items())
        ]

        return {
            "source":      "OpenWeather",
            "district":    name,
            "lat":         lat,
            "lon":         lon,
            "temp_c":      cur_data["main"]["temp"],
            "feels_like":  cur_data["main"]["feels_like"],
            "humidity":    cur_data["main"]["humidity"],
            "description": cur_data["weather"][0]["description"].title(),
            "wind_kmh":    round(cur_data["wind"]["speed"] * 3.6, 1),
            "rain_1h_mm":  round(rain_1h, 1),
            "rain_3h_mm":  round(rain_3h, 1),
            "forecast":    forecast_days,
            "timestamp":   datetime.now().isoformat()
        }

    except requests.exceptions.HTTPError as e:
        if "401" in str(e):
            print(f"  [ERROR] OpenWeather: Invalid API key")
        elif "429" in str(e):
            print(f"  [ERROR] OpenWeather: Rate limit hit")
        else:
            print(f"  [ERROR] OpenWeather: {e}")
        return None
    except Exception as e:
        print(f"  [ERROR] OpenWeather: {e}")
        return None

# ════════════════════════════════════════════
# TOMORROW.IO — precision alerts + hourly
# ════════════════════════════════════════════
def fetch_tomorrow(name, lat, lon):
    print(f"  [Tomorrow.io] Fetching {name}...")
    try:
        url = (
            f"https://api.tomorrow.io/v4/weather/forecast?"
            f"location={lat},{lon}"
            f"&apikey={TOMORROW_KEY}"
            f"&units=metric"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        daily  = data.get("timelines", {}).get("daily", [])
        today  = daily[0]["values"] if daily else {}

        rain_today = today.get("precipitationAccumulationSum", 0) or 0
        rain_prob  = today.get("precipitationProbabilityAvg", 0) or 0
        wind_gust  = today.get("windGustMax", 0) or 0
        humidity   = today.get("humidityAvg", 0) or 0
        temp_max   = today.get("temperatureMax", 0) or 0
        temp_min   = today.get("temperatureMin", 0) or 0

        forecast_days = []
        for day in daily[:5]:
            forecast_days.append({
                "date":     day["time"][:10],
                "mm":       round(day["values"].get("precipitationAccumulationSum", 0) or 0, 1),
                "prob_pct": round(day["values"].get("precipitationProbabilityAvg", 0) or 0, 0),
                "temp_max": round(day["values"].get("temperatureMax", 0) or 0, 1),
                "temp_min": round(day["values"].get("temperatureMin", 0) or 0, 1),
            })

        hourly = data.get("timelines", {}).get("hourly", [])[:12]
        hourly_rain = []
        for h in hourly:
            hourly_rain.append({
                "time": h["time"][11:16],
                "mm":   round(h["values"].get("precipitationIntensity", 0) or 0, 2)
            })

        return {
            "source":        "Tomorrow.io",
            "district":      name,
            "rain_today_mm": round(rain_today, 1),
            "rain_prob_pct": round(rain_prob, 0),
            "wind_gust_kmh": round(wind_gust * 3.6, 1),
            "humidity_pct":  round(humidity, 0),
            "temp_max_c":    round(temp_max, 1),
            "temp_min_c":    round(temp_min, 1),
            "forecast":      forecast_days,
            "hourly":        hourly_rain,
            "timestamp":     datetime.now().isoformat()
        }

    except requests.exceptions.HTTPError as e:
        if "401" in str(e) or "403" in str(e):
            print(f"  [ERROR] Tomorrow.io: Invalid API key")
        elif "429" in str(e):
            print(f"  [ERROR] Tomorrow.io: Rate limit hit")
        else:
            print(f"  [ERROR] Tomorrow.io: {e}")
        return None
    except Exception as e:
        print(f"  [ERROR] Tomorrow.io: {e}")
        return None

# ════════════════════════════════════════════
# COMBINE + ALERT LOGIC
# ════════════════════════════════════════════
def process_district(name, coords):
    lat, lon = coords["lat"], coords["lon"]
    ow = fetch_openweather(name, lat, lon)
    tm = fetch_tomorrow(name, lat, lon)

    if tm:
        rain_mm = tm["rain_today_mm"]
    elif ow:
        rain_mm = ow["rain_3h_mm"]
    else:
        rain_mm = 0

    category = classify(rain_mm)
    level    = alert_level(rain_mm)
    sms      = generate_sms(name, level, rain_mm, category)

    return {
        "district":    name,
        "rain_mm":     rain_mm,
        "category":    category,
        "alert_level": level,
        "sms":         sms,
        "openweather": ow,
        "tomorrow":    tm,
        "timestamp":   datetime.now().isoformat()
    }

# ════════════════════════════════════════════
# MAIN MONITOR
# ════════════════════════════════════════════
def run_monitor():
    print("=" * 55)
    print("LIVE WEATHER MONITOR")
    print("Districts : Mandi, Kullu, Chamba")
    print("Sources   : OpenWeather + Tomorrow.io")
    print(f"Time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    results = []

    for name, coords in DISTRICTS.items():
        print(f"\n{'='*20} {name} {'='*20}")
        result = process_district(name, coords)
        results.append(result)

        print(f"\n  Rain today   : {result['rain_mm']} mm")
        print(f"  Category     : {result['category']}")
        print(f"  Alert level  : {result['alert_level']}")

        if result["openweather"]:
            ow = result["openweather"]
            print(f"\n  OpenWeather:")
            print(f"    Temp       : {ow['temp_c']}C  feels {ow['feels_like']}C")
            print(f"    Humidity   : {ow['humidity']}%")
            print(f"    Wind       : {ow['wind_kmh']} km/h")
            print(f"    Conditions : {ow['description']}")
            print(f"    5-day forecast:")
            for f in ow["forecast"]:
                print(f"      {f['date']} : {f['mm']:5.1f} mm")

        if result["tomorrow"]:
            tm = result["tomorrow"]
            print(f"\n  Tomorrow.io:")
            print(f"    Rain prob  : {tm['rain_prob_pct']}%")
            print(f"    Wind gust  : {tm['wind_gust_kmh']} km/h")
            print(f"    Temp       : {tm['temp_min_c']}C to {tm['temp_max_c']}C")
            print(f"    5-day forecast:")
            for f in tm["forecast"]:
                print(f"      {f['date']} : {f['mm']:5.1f} mm  ({f['prob_pct']}% chance)")
            print(f"    Next 12 hours:")
            for h in tm["hourly"]:
                print(f"      {h['time']} : {h['mm']} mm/hr")

        print(f"\n  SMS ALERT: {result['sms']}")

    out_file = f"{OUT}\\live_snapshot.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSnapshot saved to live_snapshot.json")

    print("\n" + "=" * 55)
    print("SUMMARY")
    print("=" * 55)
    print(f"  {'District':<12} {'Rain (mm)':<12} {'Category':<18} {'Alert'}")
    print(f"  {'-'*55}")
    for r in results:
        print(f"  {r['district']:<12} {r['rain_mm']:<12} {r['category']:<18} {r['alert_level']}")

if __name__ == "__main__":
    run_monitor()