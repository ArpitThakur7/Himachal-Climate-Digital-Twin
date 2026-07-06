# ════════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Terrain & Vulnerability Mapping
# Computes slope and aspect from SRTM DEM, categorizes landslide risk zones.
# Outputs: FIGURE 3 for the NHESS research paper.
# ════════════════════════════════════════════════════════════════════════════════

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

# ── paths ────────────────────────────────────────────────────────────────────
BASE = r"C:\Users\admin\Desktop\rainfall agent"
TERRAIN = os.path.join(BASE, "climate-data", "terrain")
OUT     = os.path.join(BASE, "climate-data", "outputs")
os.makedirs(OUT, exist_ok=True)

ELEV_FILE   = os.path.join(TERRAIN, "elevation_mosaic.npy")
BOUNDS_FILE = os.path.join(TERRAIN, "mosaic_bounds.txt")


# ════════════════════════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ════════════════════════════════════════════════════════════════════════════════
print("═" * 70)
print("  PHASE 2 — TERRAIN & VULNERABILITY MAPPING")
print("  Himachal Climate Digital Twin")
print("═" * 70)

print("\n── Loading Elevation Mosaic ──")
elevation = np.load(ELEV_FILE)
print(f"✓ Shape: {elevation.shape}  |  Size: {elevation.nbytes / 1e9:.2f} GB")

# Parse bounds
bounds = {}
with open(BOUNDS_FILE) as f:
    for line in f:
        if "=" in line:
            key, val = line.strip().split("=")
            try:
                bounds[key] = float(val)
            except ValueError:
                pass
print(f"✓ Bounds: lon [{bounds['min_lon']:.2f}, {bounds['max_lon']:.2f}] "
      f"lat [{bounds['min_lat']:.2f}, {bounds['max_lat']:.2f}]")

# Valid data stats
valid_mask = ~np.isnan(elevation)
print(f"  Valid pixels: {valid_mask.sum():,} / {elevation.size:,} "
      f"({valid_mask.sum()/elevation.size*100:.1f}%)")
print(f"  Elevation range: {np.nanmin(elevation):.0f}m – {np.nanmax(elevation):.0f}m")


# ════════════════════════════════════════════════════════════════════════════════
# 2. COMPUTE SLOPE
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Computing Slope ──")

# SRTM pixel spacing = 1 arc-second ≈ 30m
# For more accurate spacing, use actual lat/lon conversion
# At ~32°N latitude: 1° lat ≈ 111,132m, 1° lon ≈ 111,132 × cos(32°) ≈ 94,232m
nrows, ncols = elevation.shape
lat_range = bounds["max_lat"] - bounds["min_lat"]
lon_range = bounds["max_lon"] - bounds["min_lon"]

# Cell size in meters
cell_size_y = (lat_range / nrows) * 111132.0              # meters per pixel (N-S)
cell_size_x = (lon_range / ncols) * 111132.0 * np.cos(np.radians(32.5))  # meters per pixel (E-W) at mid-lat
print(f"  Cell size: {cell_size_x:.2f}m (E-W) × {cell_size_y:.2f}m (N-S)")

# Gradient computation
# Replace NaN with local mean to avoid edge artifacts, then compute gradient
elev_filled = np.where(np.isnan(elevation), 0, elevation)

dz_dy, dz_dx = np.gradient(elev_filled, cell_size_y, cell_size_x)

# Slope in degrees
slope_pct = np.sqrt(dz_dx**2 + dz_dy**2)
slope_deg = np.degrees(np.arctan(slope_pct))

# Aspect in degrees (0=North, 90=East, 180=South, 270=West)
aspect_deg = np.degrees(np.arctan2(-dz_dx, dz_dy))
aspect_deg = (aspect_deg + 360) % 360  # normalize to 0-360

# Mask out NaN regions
slope_deg = np.where(valid_mask, slope_deg, np.nan)
aspect_deg = np.where(valid_mask, aspect_deg, np.nan)

print(f"✓ Slope range: {np.nanmin(slope_deg):.1f}° – {np.nanmax(slope_deg):.1f}°")
print(f"  Mean slope: {np.nanmean(slope_deg):.1f}°")
print(f"✓ Aspect range: {np.nanmin(aspect_deg):.1f}° – {np.nanmax(aspect_deg):.1f}°")


# ════════════════════════════════════════════════════════════════════════════════
# 3. CATEGORIZE RISK ZONES
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Categorizing Risk Zones ──")

# Risk categories
risk = np.full_like(slope_deg, np.nan)
risk[slope_deg <  15] = 1  # Low Risk
risk[(slope_deg >= 15) & (slope_deg < 30)] = 2  # Moderate Risk
risk[(slope_deg >= 30) & (slope_deg < 45)] = 3  # High Risk
risk[slope_deg >= 45] = 4  # Extreme Risk

# Count pixels per category (valid only)
valid_slopes = slope_deg[valid_mask]
total_valid = len(valid_slopes)

cat_counts = {
    "Low (<15°)":      int((valid_slopes < 15).sum()),
    "Moderate (15-30°)": int(((valid_slopes >= 15) & (valid_slopes < 30)).sum()),
    "High (30-45°)":   int(((valid_slopes >= 30) & (valid_slopes < 45)).sum()),
    "Extreme (>45°)":  int((valid_slopes >= 45).sum()),
}

print(f"  {'Category':<20s}  {'Pixels':>12s}  {'Percent':>8s}")
print(f"  {'─'*20}  {'─'*12}  {'─'*8}")
for cat, cnt in cat_counts.items():
    pct = cnt / total_valid * 100
    print(f"  {cat:<20s}  {cnt:>12,}  {pct:>7.1f}%")


# ════════════════════════════════════════════════════════════════════════════════
# 4. SAVE OUTPUTS
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Saving Outputs ──")

# Save slope and aspect arrays for ML pipeline
slope_path = os.path.join(TERRAIN, "slope_mosaic.npy")
np.save(slope_path, slope_deg)
print(f"✓ Saved: slope_mosaic.npy ({os.path.getsize(slope_path)/1e9:.2f} GB)")

aspect_path = os.path.join(TERRAIN, "aspect_mosaic.npy")
np.save(aspect_path, aspect_deg)
print(f"✓ Saved: aspect_mosaic.npy ({os.path.getsize(aspect_path)/1e9:.2f} GB)")


# ════════════════════════════════════════════════════════════════════════════════
# 5. GENERATE SLOPE RISK MAP (FIGURE 3)
# ════════════════════════════════════════════════════════════════════════════════
print("\n── Generating Slope Risk Map ──")

# District boundaries (approximate bounding boxes for overlay)
district_boxes = {
    "Mandi":  {"lat_min": 31.4, "lat_max": 32.1, "lon_min": 76.6, "lon_max": 77.4},
    "Kullu":  {"lat_min": 31.5, "lat_max": 32.5, "lon_min": 76.9, "lon_max": 77.9},
    "Chamba": {"lat_min": 32.1, "lat_max": 33.2, "lon_min": 75.7, "lon_max": 76.7},
}

# Crop to study region for the map (all three districts combined)
study_lat_min, study_lat_max = 31.0, 33.5
study_lon_min, study_lon_max = 75.5, 78.0

# Convert bounds to pixel indices
def latlon_to_pixel(lat, lon):
    row = int((bounds["max_lat"] - lat) / lat_range * nrows)
    col = int((lon - bounds["min_lon"]) / lon_range * ncols)
    row = max(0, min(nrows - 1, row))
    col = max(0, min(ncols - 1, col))
    return row, col

r1, c1 = latlon_to_pixel(study_lat_max, study_lon_min)
r2, c2 = latlon_to_pixel(study_lat_min, study_lon_max)

# Subsample for plotting (full resolution is too large for a figure)
step = 4  # every 4th pixel ≈ 120m resolution for the plot
slope_crop = slope_deg[r1:r2:step, c1:c2:step]

# Create the figure
fig, ax = plt.subplots(1, 1, figsize=(14, 10))

# Custom colormap: green → yellow → orange → red
colors_list = ["#2d7d46", "#a8d08d", "#ffd966", "#e06666", "#990000"]
cmap = mcolors.LinearSegmentedColormap.from_list("slope_risk", colors_list, N=256)
cmap.set_bad(color="#f0f0f0")  # NaN areas

extent = [study_lon_min, study_lon_max, study_lat_min, study_lat_max]
im = ax.imshow(slope_crop, extent=extent, origin="upper", cmap=cmap,
               vmin=0, vmax=60, aspect="auto")

# Add district boundary boxes
for name, box in district_boxes.items():
    rect = plt.Rectangle(
        (box["lon_min"], box["lat_min"]),
        box["lon_max"] - box["lon_min"],
        box["lat_max"] - box["lat_min"],
        linewidth=2, edgecolor="white", facecolor="none", linestyle="--"
    )
    ax.add_patch(rect)
    ax.text(box["lon_min"] + 0.05, box["lat_max"] - 0.05, name,
            fontsize=12, fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.7))

# Colorbar
cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Slope (degrees)", fontsize=12)
cbar.set_ticks([0, 15, 30, 45, 60])
cbar.set_ticklabels(["0° (Flat)", "15° (Low)", "30° (Moderate)", "45° (High)", "60° (Extreme)"])

# Risk zone legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="#2d7d46", label="Low Risk (<15°)"),
    Patch(facecolor="#a8d08d", label="Moderate (15-30°)"),
    Patch(facecolor="#ffd966", label="High Risk (30-45°)"),
    Patch(facecolor="#e06666", label="Extreme (>45°)"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=10,
          framealpha=0.9, fancybox=True)

ax.set_xlabel("Longitude (°E)", fontsize=12)
ax.set_ylabel("Latitude (°N)", fontsize=12)
ax.set_title("Slope Risk Map — Mandi, Kullu, Chamba\nSRTM 30m DEM | Landslide Vulnerability Classification",
             fontsize=14, fontweight="bold")
ax.grid(alpha=0.3, linestyle="--")

fig.tight_layout()
map_path = os.path.join(OUT, "slope_risk_map.png")
fig.savefig(map_path, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"✓ Saved: slope_risk_map.png ({os.path.getsize(map_path)/1e6:.1f} MB)")


# ── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "═" * 70)
print("  Phase 2 complete.")
print(f"  Outputs:")
print(f"    slope_mosaic.npy  → ML pipeline input")
print(f"    aspect_mosaic.npy → ML pipeline input")
print(f"    slope_risk_map.png → FIGURE 3 for paper")
print("═" * 70)
