"""
test_satellite.py
=================
Quick smoke test for the MOSDAC satellite layer.
Run from your rainfall_agent/ directory:
  python test_satellite.py

Does NOT require MOSDAC credentials — uses Open-Meteo proxy fallback.
"""

import sys
import json
from pathlib import Path

# Allow running from rainfall_agent/ root
sys.path.insert(0, str(Path(__file__).parent))

from satellite.mosdac_fetcher import (
    run_satellite_layer,
    fetch_gsmap_for_district,
    fetch_soil_moisture,
    compute_risk_score,
    cross_validate,
    DISTRICTS,
)


def test_individual_fetchers():
    print("\n=== Testing individual fetchers ===\n")
    for name, info in DISTRICTS.items():
        print(f"District: {name}")

        rain = fetch_gsmap_for_district(name, info)
        print(f"  Rain    : {rain['mm_h']} mm/hr  alert={rain['alert']}  source={rain['source']}")

        soil = fetch_soil_moisture(name, info)
        print(f"  Soil    : {soil['sm_m3']} m³/m³  sat={soil['saturation_pct']}%  alert={soil['alert']}")

        xval = cross_validate(name, rain['mm_h'] or 0)
        print(f"  XVal    : {xval}")

        risk = compute_risk_score(rain, soil)
        print(f"  Risk    : score={risk['score']}  level={risk['level']}  landslide={risk['landslide_risk']}")
        print(f"  SMS     : {risk['sms']}")
        print()


def test_full_layer():
    print("\n=== Testing full satellite layer ===\n")
    snapshot = run_satellite_layer(save=True)
    print("\nSnapshot summary:")
    print(json.dumps(snapshot["summary"], indent=2))


if __name__ == "__main__":
    test_individual_fetchers()
    test_full_layer()
    print("\n✅ Satellite layer test complete.")
    print("   Check satellite_snapshot.json for full output.")
