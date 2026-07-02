"""
satellite_risk.py
=================
Integrates MOSDAC satellite data into the main HP Rainfall Alert pipeline.

Adds satellite-derived signals to the existing Open-Meteo ground data:
  • GSMaP rain rate       → enhances rainfall alert accuracy
  • Soil moisture          → landslide precondition detector
  • Cross-validation flag  → warns when satellite vs ground mismatch > 50%

Called by the main monitor or FastAPI /risk endpoint.

Usage:
  from satellite.satellite_risk import SatelliteRiskEnhancer
  enhancer = SatelliteRiskEnhancer()
  enhanced = enhancer.enhance(ground_snapshot)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .mosdac_fetcher import (
    fetch_gsmap_for_district,
    fetch_soil_moisture,
    compute_risk_score,
    cross_validate,
    DISTRICTS,
    ALERT_RANK,
    ALERT_EMOJI,
)

log = logging.getLogger("satellite_risk")


# Landslide susceptibility multipliers per district
# Based on HPSDMA geological hazard maps
LANDSLIDE_SUSCEPTIBILITY = {
    "Mandi":  1.3,   # high — Uhl/Beas river gorges, steep slopes
    "Kullu":  1.2,   # high — Beas valley, debris fans
    "Chamba": 1.1,   # moderate-high — Ravi river basin
}


class SatelliteRiskEnhancer:
    """
    Wraps the MOSDAC fetcher and merges satellite signals
    with existing ground-truth data from Open-Meteo.
    """

    def __init__(self):
        self.last_run: Optional[datetime] = None
        self.cache: dict = {}

    def enhance(self, ground_snapshot: dict) -> dict:
        """
        Take the existing live_snapshot.json structure and add satellite layer.
        Returns an enriched snapshot with composite risk scores.
        """
        enhanced = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "Open-Meteo + MOSDAC-GSMaP + MOSDAC-SCATSAT",
            "districts": [],
        }

        for name, info in DISTRICTS.items():
            # --- Ground data from existing snapshot ---
            ground = self._find_district(ground_snapshot, name)

            # --- Satellite signals ---
            rain  = fetch_gsmap_for_district(name, info)
            soil  = fetch_soil_moisture(name, info)
            xval  = cross_validate(name, rain.get("mm_h") or 0)
            risk  = compute_risk_score(rain, soil)

            # --- Landslide risk enhancement ---
            susceptibility = LANDSLIDE_SUSCEPTIBILITY.get(name, 1.0)
            enhanced_score = min(risk["score"] * susceptibility, 100)
            landslide_prob = self._compute_landslide_probability(
                rain, soil, susceptibility
            )

            # --- Merge ground + satellite alerts ---
            ground_level = ground.get("alert_level", "NORMAL") if ground else "NORMAL"
            sat_level    = risk["level"]
            merged_level = self._merge_levels(ground_level, sat_level)

            # --- Build district record ---
            district_record = {
                "name":    name,
                "lat":     info["lat"],
                "lon":     info["lon"],

                # Ground (Open-Meteo)
                "ground": {
                    "mm_today":    ground.get("mm_today") if ground else None,
                    "alert_level": ground_level,
                    "forecast":    ground.get("forecast", []) if ground else [],
                },

                # Satellite (MOSDAC)
                "satellite": {
                    "gsmap_mm_h":      rain.get("mm_h"),
                    "gsmap_daily_est": rain.get("daily_est"),
                    "soil_moisture":   soil.get("sm_m3"),
                    "soil_sat_pct":    soil.get("saturation_pct"),
                    "rain_alert":      rain.get("alert"),
                    "soil_alert":      soil.get("alert"),
                    "source":          rain.get("source"),
                },

                # Cross-validation
                "xval": xval,

                # Composite risk
                "risk": {
                    "score":            round(enhanced_score, 1),
                    "level":            merged_level,
                    "landslide_prob_pct": landslide_prob,
                    "landslide_risk":   landslide_prob > 30,
                    "sms":              self._build_enhanced_sms(
                                            name, merged_level, rain, soil,
                                            landslide_prob, xval
                                        ),
                },
            }
            enhanced["districts"].append(district_record)

        # --- HP-wide summary ---
        enhanced["summary"] = self._build_summary(enhanced["districts"])
        self.last_run = datetime.now(timezone.utc)
        return enhanced

    # ── helpers ────────────────────────────────────────────────────────────────

    def _find_district(self, snapshot: dict, name: str) -> Optional[dict]:
        for d in snapshot.get("districts", []):
            if d.get("name", "").lower() == name.lower():
                return d
        return None

    def _merge_levels(self, ground: str, satellite: str) -> str:
        """Take the higher of the two alert levels (conservative)."""
        gr = ALERT_RANK.get(ground, 0)
        sr = ALERT_RANK.get(satellite, 0)
        return ground if gr >= sr else satellite

    def _compute_landslide_probability(
        self, rain: dict, soil: dict, susceptibility: float
    ) -> float:
        """
        Simple logistic-style landslide probability estimate (0-100%).
        Based on: rain intensity + soil saturation + terrain susceptibility.
        Not a physics model — a risk index for operational alerting.
        """
        mm_h = rain.get("mm_h") or 0
        sm_pct = soil.get("saturation_pct") or 0

        # Normalize each factor 0-1
        rain_factor = min(mm_h / 15.0, 1.0)       # 15mm/h = max
        soil_factor = min(sm_pct / 100.0, 1.0)

        # Interaction term: rain on saturated soil is non-linear
        interaction = rain_factor * soil_factor * 0.5

        raw = (rain_factor * 0.4 + soil_factor * 0.3 + interaction * 0.3)
        prob = raw * susceptibility * 100
        return round(min(prob, 100), 1)

    def _build_enhanced_sms(
        self, name: str, level: str, rain: dict, soil: dict,
        landslide_prob: float, xval: dict
    ) -> str:
        mm_h   = rain.get("mm_h") or 0
        sm_pct = soil.get("saturation_pct") or 0
        emoji  = ALERT_EMOJI.get(level, "⚪")

        base = f"{emoji} {level} — {name}: "
        detail = f"Satellite rain {mm_h:.1f}mm/hr, soil {sm_pct:.0f}% saturated."

        if landslide_prob > 50:
            action = f" Landslide prob {landslide_prob:.0f}%. EVACUATE slopes NOW."
        elif landslide_prob > 25:
            action = f" Landslide prob {landslide_prob:.0f}%. Alert slope communities."
        elif level in ("WARNING", "DANGER"):
            action = " Alert block officers and panchayat heads."
        else:
            action = ""

        xval_note = ""
        if xval.get("flag"):
            xval_note = f" [Satellite-ground mismatch: verify locally]"

        return base + detail + action + xval_note

    def _build_summary(self, districts: list) -> dict:
        levels = [d["risk"]["level"] for d in districts]
        max_rank = max((ALERT_RANK.get(l, 0) for l in levels), default=0)
        overall = ["NORMAL", "WATCH", "WARNING", "DANGER"][max_rank]

        danger_districts = [
            d["name"] for d in districts
            if d["risk"]["level"] in ("WARNING", "DANGER")
        ]
        landslide_districts = [
            d["name"] for d in districts
            if d["risk"]["landslide_risk"]
        ]

        return {
            "overall_level":         overall,
            "overall_emoji":         ALERT_EMOJI.get(overall, "⚪"),
            "danger_districts":      danger_districts,
            "landslide_risk_districts": landslide_districts,
            "send_sms":              overall != "NORMAL",
        }
