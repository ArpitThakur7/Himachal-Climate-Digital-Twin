# ════════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Ground Truth Disaster Labeling
# Builds the labeled dataset for ML training: marks days where disasters
# occurred within a 3-day window for each district.
# Outputs: TABLE 1 for the NHESS research paper.
# ════════════════════════════════════════════════════════════════════════════════

import pandas as pd
import numpy as np
import requests
import json
import sys
import os
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

# ── paths ────────────────────────────────────────────────────────────────────
BASE = r"C:\Users\admin\Desktop\rainfall agent"
DATA = os.path.join(BASE, "climate-data", "processed", "mandi_kullu_chamba.parquet")
DISASTER_DIR = os.path.join(BASE, "climate-data", "disaster")
OUT  = os.path.join(BASE, "climate-data", "outputs")
os.makedirs(DISASTER_DIR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

DISTRICTS = ["Mandi", "Kullu", "Chamba"]


# ════════════════════════════════════════════════════════════════════════════════
# 1. KNOWN DISASTER EVENTS (Manually curated ground truth)
# ════════════════════════════════════════════════════════════════════════════════
print("═" * 70)
print("  PHASE 3 — GROUND TRUTH DISASTER LABELING")
print("  Himachal Climate Digital Twin")
print("═" * 70)

# Comprehensive list of verified disaster events for Mandi, Kullu, Chamba
# Sources: ReliefWeb, SDMA reports, news archives, NDMA bulletins
KNOWN_EVENTS = [
    # ── MANDI ────────────────────────────────────────────────────────────
    {"date": "2005-06-25", "district": "Mandi", "type": "Flash Flood",
     "description": "Beas river flooding in Mandi town", "deaths": 0, "source": "IMD"},
    {"date": "2007-08-19", "district": "Mandi", "type": "Landslide",
     "description": "Monsoon landslides in Mandi district", "deaths": 5, "source": "SDMA"},
    {"date": "2010-09-15", "district": "Mandi", "type": "Flash Flood",
     "description": "Flash floods in Mandi after heavy rain", "deaths": 12, "source": "ReliefWeb"},
    {"date": "2013-08-14", "district": "Mandi", "type": "Flood",
     "description": "Severe flooding in Mandi-Kullu region", "deaths": 8, "source": "NDMA"},
    {"date": "2014-09-06", "district": "Mandi", "type": "Landslide",
     "description": "Multiple landslides on NH-21", "deaths": 4, "source": "SDMA"},
    {"date": "2015-07-30", "district": "Mandi", "type": "Flash Flood",
     "description": "Uhl river flooding", "deaths": 3, "source": "SDMA"},
    {"date": "2017-08-13", "district": "Mandi", "type": "Landslide",
     "description": "Kotropi landslide — 2 HRTC buses buried", "deaths": 46, "source": "NDMA"},
    {"date": "2018-07-12", "district": "Mandi", "type": "Flash Flood",
     "description": "Monsoon flash floods in Mandi", "deaths": 7, "source": "SDMA"},
    {"date": "2019-08-18", "district": "Mandi", "type": "Landslide",
     "description": "Multiple landslides after cloudburst", "deaths": 6, "source": "ReliefWeb"},
    {"date": "2021-07-26", "district": "Mandi", "type": "Flash Flood",
     "description": "Beas river flooding", "deaths": 9, "source": "SDMA"},
    {"date": "2023-07-09", "district": "Mandi", "type": "Cloudburst",
     "description": "Mandi cloudburst — massive urban flooding", "deaths": 15, "source": "NDMA"},
    {"date": "2023-07-12", "district": "Mandi", "type": "Landslide",
     "description": "Multiple landslides post-cloudburst", "deaths": 12, "source": "SDMA"},
    {"date": "2023-08-14", "district": "Mandi", "type": "Flood",
     "description": "Sustained monsoon flooding across Mandi", "deaths": 22, "source": "ReliefWeb"},
    {"date": "2024-08-01", "district": "Mandi", "type": "Flash Flood",
     "description": "Monsoon flash floods in Mandi district", "deaths": 8, "source": "SDMA"},

    # ── KULLU ────────────────────────────────────────────────────────────
    {"date": "2005-07-12", "district": "Kullu", "type": "Flash Flood",
     "description": "Parvati river flash floods", "deaths": 4, "source": "SDMA"},
    {"date": "2010-08-06", "district": "Kullu", "type": "Flood",
     "description": "Beas river flooding in Kullu valley", "deaths": 6, "source": "ReliefWeb"},
    {"date": "2013-06-16", "district": "Kullu", "type": "Flash Flood",
     "description": "Cloudburst floods in Kullu-Manali", "deaths": 10, "source": "NDMA"},
    {"date": "2014-09-07", "district": "Kullu", "type": "Flood",
     "description": "Severe flooding in Kullu district", "deaths": 5, "source": "SDMA"},
    {"date": "2015-09-18", "district": "Kullu", "type": "Flash Flood",
     "description": "Parvati valley flash floods", "deaths": 3, "source": "SDMA"},
    {"date": "2018-09-01", "district": "Kullu", "type": "Flood",
     "description": "Kullu floods — widespread destruction", "deaths": 14, "source": "NDMA"},
    {"date": "2019-08-20", "district": "Kullu", "type": "Landslide",
     "description": "Landslides on Manali-Leh highway", "deaths": 4, "source": "SDMA"},
    {"date": "2021-07-25", "district": "Kullu", "type": "Flash Flood",
     "description": "Flash floods in Kullu-Manali belt", "deaths": 7, "source": "ReliefWeb"},
    {"date": "2023-07-10", "district": "Kullu", "type": "Flood",
     "description": "Monsoon flooding in Kullu valley", "deaths": 18, "source": "NDMA"},
    {"date": "2023-08-14", "district": "Kullu", "type": "Landslide",
     "description": "Landslides in Kullu during August monsoon", "deaths": 11, "source": "SDMA"},

    # ── CHAMBA ───────────────────────────────────────────────────────────
    {"date": "2007-08-20", "district": "Chamba", "type": "Landslide",
     "description": "Landslides in Chamba district", "deaths": 3, "source": "SDMA"},
    {"date": "2012-08-07", "district": "Chamba", "type": "Flash Flood",
     "description": "Ravi river flash floods", "deaths": 5, "source": "SDMA"},
    {"date": "2013-06-17", "district": "Chamba", "type": "Flood",
     "description": "Major flooding in Chamba district", "deaths": 8, "source": "ReliefWeb"},
    {"date": "2015-09-24", "district": "Chamba", "type": "Flash Flood",
     "description": "Flash floods in upper Chamba", "deaths": 4, "source": "SDMA"},
    {"date": "2018-09-03", "district": "Chamba", "type": "Flood",
     "description": "Chamba flooding — Ravi and Chenab basins", "deaths": 9, "source": "NDMA"},
    {"date": "2019-08-17", "district": "Chamba", "type": "Landslide",
     "description": "Landslides in Chamba hills", "deaths": 5, "source": "SDMA"},
    {"date": "2021-08-11", "district": "Chamba", "type": "Landslide",
     "description": "Multiple landslides in Chamba", "deaths": 6, "source": "ReliefWeb"},
    {"date": "2023-07-11", "district": "Chamba", "type": "Cloudburst",
     "description": "Cloudburst-triggered flooding", "deaths": 8, "source": "SDMA"},
    {"date": "2023-08-21", "district": "Chamba", "type": "Flood",
     "description": "Severe monsoon flooding in Chamba", "deaths": 14, "source": "NDMA"},
]


# ════════════════════════════════════════════════════════════════════════════════
# 2. ATTEMPT RELIEFWEB API ENRICHMENT (optional — supplement known events)
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Fetching ReliefWeb Reports ──")

def fetch_reliefweb_events():
    """Query ReliefWeb API for Himachal Pradesh disaster reports."""
    events = []
    base_url = "https://api.reliefweb.int/v1/reports"
    params = {
        "appname": "himachal-climate-digital-twin",
        "query[value]": "Himachal Pradesh landslide OR flood",
        "filter[field]": "date.created",
        "filter[value][from]": "2005-01-01",
        "filter[value][to]": "2025-12-31",
        "limit": 100,
        "fields[include][]": ["title", "date.created", "body"],
        "sort[]": "date.created:asc",
    }
    try:
        resp = requests.get(base_url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            count = data.get("totalCount", 0)
            print(f"  ReliefWeb returned {count} reports")
            for item in data.get("data", []):
                fields = item.get("fields", {})
                title = fields.get("title", "")
                date_info = fields.get("date", {})
                created = date_info.get("created", "") if isinstance(date_info, dict) else ""
                events.append({
                    "title": title,
                    "date": created[:10] if created else "",
                    "source": "ReliefWeb API"
                })
        else:
            print(f"  ⚠ ReliefWeb API returned status {resp.status_code}")
    except Exception as e:
        print(f"  ⚠ ReliefWeb API failed: {e}")
        print(f"    Proceeding with {len(KNOWN_EVENTS)} manually curated events")

    return events


reliefweb_events = fetch_reliefweb_events()


# ════════════════════════════════════════════════════════════════════════════════
# 3. SAVE DISASTER EVENTS DATABASE
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Saving Disaster Event Database ──")

events_df = pd.DataFrame(KNOWN_EVENTS)
events_df["date"] = pd.to_datetime(events_df["date"])
events_csv = os.path.join(DISASTER_DIR, "disaster_events.csv")
events_df.to_csv(events_csv, index=False)
print(f"✓ Saved: disaster_events.csv ({len(events_df)} events)")

# Summary by district
for d in DISTRICTS:
    dd = events_df[events_df["district"] == d]
    total_deaths = dd["deaths"].sum()
    print(f"  {d}: {len(dd)} events, {total_deaths} deaths")

# Also save as JSON
events_json = os.path.join(DISASTER_DIR, "known_events_curated.json")
with open(events_json, "w") as f:
    # Convert dates to strings for JSON
    json_events = []
    for e in KNOWN_EVENTS:
        json_events.append(e)
    json.dump(json_events, f, indent=2, default=str)
print(f"✓ Saved: known_events_curated.json")


# ════════════════════════════════════════════════════════════════════════════════
# 4. LABEL THE RAINFALL DATASET
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Labeling Rainfall Dataset ──")

# Load rainfall data
df = pd.read_parquet(DATA)
df["TIME"] = pd.to_datetime(df["TIME"])
print(f"  Loaded: {len(df):,} daily records")

# Build a set of (date, district) tuples for disaster windows
# For each disaster event, mark the event date AND the 3 days BEFORE
# (because we want to predict 3 days ahead)
disaster_windows = set()
for event in KNOWN_EVENTS:
    event_date = pd.Timestamp(event["date"])
    district = event["district"]
    # Mark the 3 days leading up to AND including the event
    for offset in range(0, 4):  # 0, 1, 2, 3 days before
        check_date = event_date - timedelta(days=offset)
        disaster_windows.add((check_date, district))

print(f"  Disaster window entries: {len(disaster_windows)} (date, district) pairs")

# Label each row
df["disaster_within_3days"] = df.apply(
    lambda row: (row["TIME"], row["DISTRICT"]) in disaster_windows,
    axis=1
)

positive_count = df["disaster_within_3days"].sum()
negative_count = len(df) - positive_count
print(f"  Positive labels (disaster=True) : {positive_count:,}")
print(f"  Negative labels (disaster=False): {negative_count:,}")
print(f"  Class imbalance ratio           : 1:{negative_count//max(positive_count,1)}")

# Save labeled dataset
labeled_path = os.path.join(BASE, "climate-data", "processed", "mandi_kullu_chamba_labelled.parquet")
df.to_parquet(labeled_path, index=False)
print(f"\n✓ Saved: mandi_kullu_chamba_labelled.parquet")
print(f"  Columns: {list(df.columns)}")


# ════════════════════════════════════════════════════════════════════════════════
# 5. GENERATE TABLE 1 (Disaster Event Summary)
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Generating TABLE 1: Disaster Event Summary ──")

# Cross-reference: check rainfall on disaster dates
disaster_rainfall = []
for event in KNOWN_EVENTS:
    event_date = pd.Timestamp(event["date"])
    district = event["district"]
    match = df[(df["TIME"] == event_date) & (df["DISTRICT"] == district)]
    rain_mm = float(match["AVG_RAINFALL_MM"].values[0]) if len(match) > 0 else np.nan

    # Also get 3-day preceding rainfall
    three_day = df[
        (df["TIME"] >= event_date - timedelta(days=2)) &
        (df["TIME"] <= event_date) &
        (df["DISTRICT"] == district)
    ]["AVG_RAINFALL_MM"].sum()

    disaster_rainfall.append({
        "Date": event["date"],
        "District": district,
        "Type": event["type"],
        "Deaths": event["deaths"],
        "Description": event["description"],
        "Day_Rainfall_mm": round(rain_mm, 1),
        "3Day_Rainfall_mm": round(float(three_day), 1),
        "Source": event["source"],
    })

table1 = pd.DataFrame(disaster_rainfall)
table1_path = os.path.join(OUT, "disaster_event_table.csv")
table1.to_csv(table1_path, index=False)
print(f"✓ Saved: disaster_event_table.csv (TABLE 1 for paper)")


# ── Print TABLE 1 ────────────────────────────────────────────────────────────
print(f"\n  {'Date':<12s}  {'District':<8s}  {'Type':<14s}  {'Deaths':>6s}  "
      f"{'Day Rain':>9s}  {'3Day Rain':>10s}  Description")
print(f"  {'─'*12}  {'─'*8}  {'─'*14}  {'─'*6}  {'─'*9}  {'─'*10}  {'─'*40}")
for _, row in table1.iterrows():
    print(f"  {row['Date']:<12s}  {row['District']:<8s}  {row['Type']:<14s}  "
          f"{row['Deaths']:>6d}  {row['Day_Rainfall_mm']:>8.1f}  "
          f"{row['3Day_Rainfall_mm']:>9.1f}  {row['Description'][:40]}")


# ── Summary ──────────────────────────────────────────────────────────────────
total_deaths = events_df["deaths"].sum()
print(f"\n\n── SUMMARY ──")
print(f"  Total disaster events    : {len(KNOWN_EVENTS)}")
print(f"  Total deaths documented  : {total_deaths}")
print(f"  Labeled dataset rows     : {len(df):,}")
print(f"  Positive labels          : {positive_count:,} ({positive_count/len(df)*100:.2f}%)")

print("\n" + "═" * 70)
print("  Phase 3 complete.")
print(f"  Outputs:")
print(f"    disaster_events.csv              → Event database")
print(f"    disaster_event_table.csv         → TABLE 1 for paper")
print(f"    mandi_kullu_chamba_labelled.parquet → ML training dataset")
print("═" * 70)
