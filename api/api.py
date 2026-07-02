# ============================================
# PROJECT SCOPE — DO NOT CHANGE
# Districts : Mandi, Kullu, Chamba
# Period    : Live + 2005 to 2025
# File      : api.py
# Run with  : uvicorn api:app --reload
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import os
from datetime import datetime

# import your live weather function
import sys
sys.path.append(r"C:\Users\admin\Desktop\rainfall agent")
from imd_live import process_district, DISTRICTS

app = FastAPI(
    title="Himachal Rainfall Early Warning API",
    description="Mandi, Kullu, Chamba — Live + Historical",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

OUT = r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed"

# ── load historical data once at startup ────
df = pd.read_parquet(f"{OUT}\\mandi_kullu_chamba.parquet")
df["TIME"] = pd.to_datetime(df["TIME"])
df["YEAR"]  = df["TIME"].dt.year
df["MONTH"] = df["TIME"].dt.month

# ════════════════════════════════════════════
# ENDPOINT 1 — health check
# ════════════════════════════════════════════
@app.get("/")
def root():
    return {
        "status":    "online",
        "project":   "Himachal Rainfall Early Warning System",
        "districts": ["Mandi", "Kullu", "Chamba"],
        "period":    "2005-2025 + live",
        "time":      datetime.now().isoformat()
    }

# ════════════════════════════════════════════
# ENDPOINT 2 — live risk per district
# GET /risk
# GET /risk?district=Mandi
# ════════════════════════════════════════════
@app.get("/risk")
def get_risk(district: str = None):
    results = []
    targets = (
        {district: DISTRICTS[district]}
        if district and district in DISTRICTS
        else DISTRICTS
    )
    for name, coords in targets.items():
        result = process_district(name, coords)
        results.append({
            "district":    name,
            "lat":         coords["lat"],
            "lon":         coords["lon"],
            "rain_mm":     result["rain_mm"],
            "category":    result["category"],
            "alert_level": result["alert_level"],
            "sms":         result["sms"],
            "forecast_5d": result["tomorrow"]["forecast"]
                           if result["tomorrow"] else
                           result["openweather"]["forecast"]
                           if result["openweather"] else [],
            "timestamp":   result["timestamp"]
        })
    return {"districts": results}

# ════════════════════════════════════════════
# ENDPOINT 3 — active alerts only
# GET /alerts
# ════════════════════════════════════════════
@app.get("/alerts")
def get_alerts():
    results = []
    for name, coords in DISTRICTS.items():
        result = process_district(name, coords)
        if result["alert_level"] != "NORMAL":
            results.append({
                "district":    name,
                "alert_level": result["alert_level"],
                "rain_mm":     result["rain_mm"],
                "category":    result["category"],
                "sms":         result["sms"],
                "timestamp":   result["timestamp"]
            })
    return {
        "active_alerts": len(results),
        "alerts": results,
        "timestamp": datetime.now().isoformat()
    }

# ════════════════════════════════════════════
# ENDPOINT 4 — historical trend
# GET /history?district=Mandi&year=2023
# GET /history?district=Kullu
# ════════════════════════════════════════════
@app.get("/history")
def get_history(district: str = "Mandi", year: int = None):
    sub = df[df["AVG_RAINFALL_MM"].notna()]
    if district:
        sub = sub[sub["DISTRICT"] == district]
    if year:
        sub = sub[sub["YEAR"] == year]

    # monsoon stats per year
    monsoon = sub[sub["MONTH"].between(6, 9)]
    yearly = (
        monsoon.groupby("YEAR")
        .agg(
            monsoon_total_mm=("AVG_RAINFALL_MM", "sum"),
            peak_day_mm=("AVG_RAINFALL_MM", "max"),
            avg_daily_mm=("AVG_RAINFALL_MM", "mean"),
            heavy_days=("AVG_RAINFALL_MM", lambda x: (x >= 64.5).sum())
        )
        .reset_index()
        .round(2)
    )

    return {
        "district": district,
        "year_filter": year,
        "records": len(yearly),
        "data": yearly.to_dict(orient="records")
    }

# ════════════════════════════════════════════
# ENDPOINT 5 — worst events
# GET /events?district=Mandi&top=5
# ════════════════════════════════════════════
@app.get("/events")
def get_events(district: str = None, top: int = 10):
    sub = df.copy()
    if district:
        sub = sub[sub["DISTRICT"] == district]

    worst = (
        sub[sub["AVG_RAINFALL_MM"] >= 35.5]
        .sort_values("AVG_RAINFALL_MM", ascending=False)
        .head(top)[["TIME","DISTRICT","AVG_RAINFALL_MM","CATEGORY"]]
        .copy()
    )
    worst["TIME"] = worst["TIME"].astype(str)
    worst = worst.round(2)

    return {
        "district":   district or "All",
        "top":        top,
        "events":     worst.to_dict(orient="records")
    }

# ════════════════════════════════════════════
# ENDPOINT 6 — monthly climatology
# GET /climatology?district=Mandi
# ════════════════════════════════════════════
@app.get("/climatology")
def get_climatology(district: str = "Mandi"):
    sub = df[
        (df["DISTRICT"] == district) &
        (df["MONTH"].between(6, 9))
    ]
    monthly = (
        sub.groupby("MONTH")
        .agg(
            avg_daily_mm=("AVG_RAINFALL_MM", "mean"),
            max_day_mm=("AVG_RAINFALL_MM", "max"),
            total_days=("AVG_RAINFALL_MM", "count")
        )
        .reset_index()
        .round(2)
    )
    month_names = {6:"June", 7:"July", 8:"August", 9:"September"}
    monthly["month_name"] = monthly["MONTH"].map(month_names)

    return {
        "district": district,
        "period":   "2005-2025",
        "data":     monthly.to_dict(orient="records")
    }
