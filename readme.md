# Himachal Climate Digital Twin

### An AI-Powered Climate Intelligence, Forecast Correction, Multi-Hazard Prediction and Cascading Disaster Intelligence Framework for the Western Himalayas

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Region](https://img.shields.io/badge/Region-Himachal%20Pradesh-orange)](https://en.wikipedia.org/wiki/Himachal_Pradesh)
[![Status](https://img.shields.io/badge/Status-Active%20Research-red)](https://github.com)

---

## Overview

Over the past 50 years, rainfall patterns in Himachal Pradesh have undergone a fundamental structural shift. Rain that once arrived as consistent, distributed precipitation across the monsoon season now arrives as violent, concentrated cloudbursts separated by prolonged dry spells. In 2023 alone, this shift caused 428 deaths, destroyed 12,000 km of roads, collapsed 340 bridges, and inflicted economic damage exceeding ₹12,000 crores.

Existing global forecasting platforms — Zoom Earth, ECMWF, GFS, OpenWeather — treat high-altitude zones like Prashar and low-altitude Mandi town with identical spatial resolution. A single forecast grid cell may contain multiple valleys, ridges, and microclimates, producing spatial averages that are useless for village-level disaster response.

This project builds a Himachal Climate Digital Twin — a system that does not merely predict rainfall but predicts consequences: which roads close, which bridges fail, which villages isolate, and how long emergency response will be delayed.

---

## Study Region

| District | Elevation Range  | Primary Rivers | Risk Profile |
|----------|-----------------|----------------|--------------|
| Mandi    | 800m to 4200m   | Beas, Uhl      | Critical     |
| Kullu    | 1100m to 5900m  | Beas, Parvati  | Critical     |
| Chamba   | 900m to 6500m   | Ravi, Chenab   | High         |

Study Period: 2005 to 2025 — 20 years

---

## Key Findings

From 1.83 million daily rainfall records across three districts:

| Metric | Value |
|--------|-------|
| Mandi 2025 monsoon total | 1,488 mm — highest on record |
| Mandi 2023 extreme rain days | 3 days above 64.5mm threshold |
| Mandi all-time peak single day | 105.97 mm |
| Chamba all-time peak single day | 105.20 mm |
| Kullu all-time peak single day | 95.70 mm |
| Extreme events post 2018 | Clustering across all three districts |
| Wet day intensity | Rising year on year |
| Dry spell duration | Increasing consecutive dry days |

---

## System Architecture

```
Data Layer
├── CHIRPS rainfall         1.83M records · 2005-2025
├── NASA SRTM DEM           30m elevation · 10 tiles
├── OpenStreetMap           roads · bridges · hospitals · schools
├── HydroSHEDS              river networks · watersheds
├── ERA5 reanalysis         temperature · humidity · wind · CAPE
├── ESP32 IoT gauge         live ground truth from lab
└── Climate indices         ENSO · CO2 · IOD

Processing Layer
├── filter_districts.py     district extraction + IMD classification
├── trend_analysis.py       20-year statistical analysis — 10 charts
├── download_srtm.py        terrain data pipeline
└── disaster_history.py     event labelling for ML training

Intelligence Layer
├── Forecast bias correction    terrain-adjusted prediction engine
├── XGBoost multi-hazard model  flood · landslide · road closure risk
├── LSTM temporal model         sequence-based rainfall prediction
├── Cascading disaster engine   full consequence chain simulation
└── SHAP explainability         feature attribution for government trust

Agent Layer
├── Monitor agent           hourly live weather anomaly detection
├── Alert agent             graded SMS dispatch
└── Report agent            weekly automated government briefing

Output Layer
├── FastAPI backend         6 live endpoints
├── Live dashboard          Leaflet.js map — colour coded risk
├── SMS alerts              district officials + panchayat heads
├── Weekly brief            Claude API auto-generated PDF
└── Education cards         WhatsApp shareable PNG for communities
```

---

## The Cascade Chain

The primary novel contribution of this project:

```
Extreme Rainfall above 64.5mm per day
        ↓
Slope Failure — slope above 30 degrees + soil saturation
        ↓
Landslide or Debris Flow
        ↓
Road Closure — proximity analysis to failure zone
        ↓
Village Isolation — connectivity graph broken
        ↓
Emergency Response Delay — hospital access time increases
        ↓
Lives Lost and Infrastructure Damage
```

This exact chain killed 46 people at Kotropi, Mandi in 2017.
A 6-hour advance warning would have been sufficient to stop those buses.

---

## Data Sources

| Dataset | Source | Coverage | Format |
|---------|--------|----------|--------|
| Daily rainfall | CHIRPS | 2005-2025 | Parquet |
| Elevation DEM | NASA SRTM | 30m resolution | HGT |
| Roads | OpenStreetMap | Current | GPKG |
| Bridges | OpenStreetMap | Current | GPKG |
| Hospitals | OpenStreetMap | Current | GPKG |
| River network | HydroSHEDS | Beas + Ravi | SHP |
| Live weather | OpenWeather | Real-time | API |
| Hourly forecast | Tomorrow.io | Real-time | API |
| ENSO index | NOAA | 1950 to present | TXT |
| CO2 concentration | NOAA | 1958 to present | TXT |
| IOD index | NOAA | Monthly | TXT |
| Ground truth | ESP32 gauge | Live | IoT |
| Disaster events | ReliefWeb | 2005-2025 | JSON |
| Atmospheric | ERA5 Copernicus | 2005-2025 | NetCDF |

---

## Infrastructure Intelligence

Real counts from OpenStreetMap for all three districts:

| Facility | Mandi | Kullu | Chamba | Total |
|----------|-------|-------|--------|-------|
| Road segments | 12,013 | 2,657 | 4,918 | 19,588 |
| Hospitals | 77 | 21 | 33 | 131 |
| Schools | 74 | 38 | 62 | 174 |
| Bridges | 7 | 7 | 1 | 15 |
| Police stations | 13 | 7 | 8 | 28 |
| Helipads | 3 | 2 | 10 | 15 |

---

## Project Structure

```
rainfall-agent/
├── climate-data/
│   ├── processed/
│   │   ├── mandi_kullu_chamba.parquet
│   │   ├── mandi_kullu_chamba.csv
│   │   └── mandi_kullu_chamba_labelled.parquet
│   ├── terrain/
│   │   ├── N31E076.hgt ... N33E077.hgt  (10 tiles)
│   │   ├── elevation_mosaic.npy
│   │   ├── mosaic_bounds.txt
│   │   ├── terrain_relief_map.png
│   │   ├── terrain_slope_map.png
│   │   └── terrain_3d.html
│   ├── infrastructure/
│   │   ├── mandi_roads.gpkg
│   │   ├── mandi_bridges.gpkg
│   │   ├── mandi_hospitals.gpkg
│   │   ├── mandi_schools.gpkg
│   │   ├── mandi_police.gpkg
│   │   ├── mandi_helipads.gpkg
│   │   ├── kullu_roads.gpkg
│   │   ├── kullu_bridges.gpkg
│   │   ├── kullu_hospitals.gpkg
│   │   ├── kullu_schools.gpkg
│   │   ├── kullu_police.gpkg
│   │   ├── kullu_helipads.gpkg
│   │   ├── chamba_roads.gpkg
│   │   ├── chamba_bridges.gpkg
│   │   ├── chamba_hospitals.gpkg
│   │   ├── chamba_schools.gpkg
│   │   ├── chamba_police.gpkg
│   │   ├── chamba_helipads.gpkg
│   │   ├── infrastructure_research_map.html
│   │   └── progress.json
│   ├── rainfall/
│   │   └── RF25_ind20XX_rfp25.nc  (21 files 2005-2025)
│   ├── disaster/
│   │   ├── reliefweb_reports.json
│   │   └── known_events.json
│   └── satellite/
├── satellite/
│   ├── mosdac_fetcher.py
│   └── satellite_risk.py
├── extract_himachal.py
├── filter_districts.py
├── trend_analysis.py
├── imd_live.py
├── api.py
├── download_srtm.py
├── download_infrastructure.py
├── download_era5.py
├── download_gpm.py
├── disaster_history.py
├── view_terrain_3d.py
├── view_terrain_research.py
└── README.md
```

---

## API Endpoints

Start the API:
```bash
uvicorn api:app --reload
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System health and status |
| `/risk` | GET | Live risk all districts |
| `/risk?district=Mandi` | GET | Live risk one district |
| `/alerts` | GET | Active warnings only |
| `/history?district=Mandi` | GET | 20-year monsoon stats |
| `/events?district=Kullu&top=5` | GET | Worst rainfall events |
| `/climatology?district=Chamba` | GET | Monthly averages |

Interactive API docs: `http://localhost:8000/docs`

---

## Installation

```bash
git clone https://github.com/yourusername/himachal-climate-digital-twin
cd himachal-climate-digital-twin

pip install pandas geopandas rasterio fastapi uvicorn
pip install plotly folium osmnx xgboost scikit-learn
pip install matplotlib seaborn requests torch scipy
```

---

## Running the System

```bash
# 20-year trend analysis — generates 10 charts
python trend_analysis.py

# 3D interactive terrain visualization
python view_terrain_3d.py

# Research grade infrastructure map
python view_research_map.py

# Live weather monitor
python imd_live.py

# Start API server
uvicorn api:app --reload

# Download infrastructure data
python download_infrastructure.py

# Download terrain data
python download_srtm.py

# Build disaster event labels
python disaster_history.py
```

---

## Alert Levels

| Level | Rainfall Threshold | Action Required |
|-------|-------------------|-----------------|
| NORMAL | Below 35.5mm | No action |
| WATCH | 35.5 to 64.4mm | Monitor closely |
| WARNING | 64.5 to 115.5mm | Prepare evacuation |
| EMERGENCY | Above 115.6mm | Immediate action |

---

## Research Questions

| ID | Question | Status |
|----|----------|--------|
| RQ1 | How have rainfall patterns changed 2005 to 2025? | Answered |
| RQ2 | Can terrain explain forecast errors in HP? | In progress |
| RQ3 | Can AI correct forecast bias for Himalayan terrain? | In progress |
| RQ4 | Can multi-source data improve hazard prediction? | In progress |
| RQ5 | Can cascading disaster impacts be predicted? | Not started |
| RQ6 | Can explainable AI increase government trust? | Not started |

---

## Scientific Hypothesis

```
Risk = Hazard × Exposure × Vulnerability

Hazard       = Rainfall intensity + cloudburst frequency
Exposure     = Population + infrastructure + settlements
Vulnerability = Terrain slope + accessibility + disaster history
```

---

## Target Publication

Journal: Natural Hazards and Earth System Sciences (NHESS)
Impact Factor: 4.6
Category: Hydrology and Earth System Sciences

Novel contributions:
1. First terrain-adjusted forecast bias correction for Western Himalayan districts
2. First cascading disaster chain prediction for Mandi-Kullu-Chamba at block level
3. First IoT ground truth integration with satellite rainfall for HP forecast correction
4. District-level explainable AI dashboard for government decision support

---

## Real World Impact

| Scenario | Without This System | With This System |
|----------|---------------------|-----------------|
| Kotropi 2017 | 46 deaths | 6-hour advance cascade warning |
| 2023 monsoon | 428 deaths, ₹12,000cr damage | Graded evacuation alerts |
| Road closures | Discovered after failure | Predicted 6 hours before |
| Village isolation | No warning issued | SMS to panchayat head |
| Government response | Reactive relief | Proactive prevention |

Cost of this system in Phase 1: ₹0
Cost of 2023 inaction: ₹12,000 crores and 428 lives

---

## Presentation

Venue: Ministry of Himachal Pradesh
Location: Himachal Pradesh, India
Year: 2026

---

## Author

Built by an independent researcher based in Himachal Pradesh with one month of manual field forecasting experience using Zoom Earth, personal weather pattern analysis, and a live ESP32 IoT rain gauge — now being automated into a production-grade AI system for the Western Himalayas.

---

## License

MIT License — free to use, modify, and deploy for disaster management and climate research purposes.

---

*"The data exists. The technology is ready. What is needed is the will to act before the next cloudburst."*
