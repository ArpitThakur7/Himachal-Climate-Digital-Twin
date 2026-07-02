# ============================================
# PROJECT SCOPE — DO NOT CHANGE
# Districts : Mandi, Kullu, Chamba
# Period    : Current infrastructure
# Source    : OpenStreetMap via OSMnx
# File      : download_infrastructure.py
# Resumes   : skips already downloaded files
# ============================================

import osmnx as ox
import geopandas as gpd
import json
import os
import time

OUT = r"C:\Users\admin\Desktop\rainfall agent\climate-data\infrastructure"
os.makedirs(OUT, exist_ok=True)

PROGRESS_FILE = f"{OUT}\\progress.json"

DISTRICTS = {
    "Mandi":  (31.5, 76.7, 32.1, 77.4),
    "Kullu":  (31.7, 77.0, 32.5, 77.8),
    "Chamba": (32.4, 75.5, 33.2, 77.0)
}

TAGS_LIST = [
    ("hospitals", {"amenity": "hospital"}),
    ("schools",   {"amenity": "school"}),
    ("bridges",   {"man_made": "bridge"}),
    ("police",    {"amenity": "police"}),
    ("helipads",  {"aeroway": "helipad"}),
]

# ── progress tracker ─────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def is_done(progress, district, item):
    return progress.get(district, {}).get(item, False)

def mark_done(progress, district, item, count=0):
    if district not in progress:
        progress[district] = {}
    progress[district][item] = True
    progress[district][f"{item}_count"] = count
    save_progress(progress)

# ── download with retry ──────────────────────
def download_with_retry(fn, retries=5, wait=30):
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            msg = str(e).lower()
            retryable = any(x in msg for x in [
                "refused", "max retries", "time out", "timeout",
                "connectionerror", "connection", "remote end",
                "closed", "reset", "internal server error", "502",
                "503", "unavailable", "too many"
            ])
            if retryable:
                print(f"  Server issue. Attempt {attempt}/{retries}. Waiting {wait}s... ({e})")
                time.sleep(wait)
            else:
                print(f"  Non-retryable error: {e}")
                return None
    print(f"  Failed after {retries} attempts. Will resume next run.")
    return None

# ── roads ────────────────────────────────────
def download_roads(name, south, west, north, east, progress):
    if is_done(progress, name, "roads"):
        count = progress[name].get("roads_count", 0)
        print(f"  Roads: already downloaded ({count} segments) — skipping")
        return count

    print(f"\nDownloading roads for {name}...")
    out_file = f"{OUT}\\{name.lower()}_roads.gpkg"

    # Use simpler network type for large/mountainous areas to avoid Overpass timeouts
    net_type = "drive" if name in ("Kullu", "Chamba") else "all"

    def fn():
        bbox = (west, south, east, north)
        G   = ox.graph_from_bbox(bbox=bbox, network_type=net_type, simplify=True)
        gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)
        gdf.to_file(out_file, driver="GPKG")
        return len(gdf)

    count = download_with_retry(fn)
    if count is not None:
        mark_done(progress, name, "roads", count)
        print(f"  Roads saved: {count} segments")
    return count or 0

# ── POI ──────────────────────────────────────
def download_poi(name, south, west, north, east, progress):
    print(f"Downloading facilities for {name}...")
    bbox     = (west, south, east, north)
    all_pois = {}

    for label, tags in TAGS_LIST:
        key = f"poi_{label}"
        if is_done(progress, name, key):
            count = progress[name].get(f"{key}_count", 0)
            print(f"  {label}: already downloaded ({count}) — skipping")
            all_pois[label] = count
            continue

        out_file = f"{OUT}\\{name.lower()}_{label}.gpkg"

        def fn(t=tags, o=out_file):
            gdf = ox.features_from_bbox(bbox=bbox, tags=t)
            # Remove duplicate indices before saving
            if not gdf.empty and not gdf.index.is_unique:
                gdf = gdf[~gdf.index.duplicated(keep="first")]
            if not gdf.empty:
                gdf.to_file(o, driver="GPKG")
            return len(gdf)

        count = download_with_retry(fn)
        if count is not None:
            mark_done(progress, name, key, count)
            print(f"  {label}: {count} features saved")
            all_pois[label] = count
        else:
            all_pois[label] = 0

    return all_pois

# ── summary ──────────────────────────────────
def print_summary(progress):
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for name in DISTRICTS:
        d = progress.get(name, {})
        print(f"\n{name}:")
        print(f"  Roads      : {d.get('roads_count', 0)}")
        for label, _ in TAGS_LIST:
            key = f"poi_{label}_count"
            print(f"  {label:12s} : {d.get(key, 0)}")

# ── main ─────────────────────────────────────
def download_all():
    print("=" * 50)
    print("Infrastructure Download — Mandi Kullu Chamba")
    print("Resumable — skips completed downloads")
    print("=" * 50)

    progress = load_progress()

    for name, (south, west, north, east) in DISTRICTS.items():
        print(f"\n{'='*20} {name} {'='*20}")
        download_roads(name, south, west, north, east, progress)
        download_poi(name, south, west, north, east, progress)

    print_summary(progress)
    print("\nDone. Run again anytime to resume incomplete downloads.")

if __name__ == "__main__":
    download_all()
