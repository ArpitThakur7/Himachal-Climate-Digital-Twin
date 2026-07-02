# ============================================
# 3D interactive terrain visualization — v2
# Mandi, Kullu, Chamba — SRTM elevation
# ============================================
import numpy as np
import plotly.graph_objects as go

TERRAIN_DIR = r"C:\Users\admin\Desktop\rainfall agent\climate-data\terrain"

print("Loading elevation mosaic...")
mosaic = np.load(f"{TERRAIN_DIR}\\elevation_mosaic.npy")

bounds = {}
with open(f"{TERRAIN_DIR}\\mosaic_bounds.txt") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=")
            bounds[k] = v

min_lon = float(bounds["min_lon"])
max_lon = float(bounds["max_lon"])
min_lat = float(bounds["min_lat"])
max_lat = float(bounds["max_lat"])

step = 12
mosaic_small = mosaic[::step, ::step]
mosaic_small = np.where(mosaic_small < -100, np.nan, mosaic_small)
mosaic_small = np.nan_to_num(mosaic_small, nan=np.nanmean(mosaic_small))

print(f"Downsampled shape: {mosaic_small.shape}")

lons = np.linspace(min_lon, max_lon, mosaic_small.shape[1])
lats = np.linspace(max_lat, min_lat, mosaic_small.shape[0])

DISTRICTS = {
    "Mandi":  {"lat": (31.5, 32.1), "lon": (76.7, 77.4), "color": "#FF3B30"},
    "Kullu":  {"lat": (31.7, 32.5), "lon": (77.0, 77.8), "color": "#0A84FF"},
    "Chamba": {"lat": (32.4, 33.2), "lon": (75.5, 77.0), "color": "#34C759"}
}

def elevation_at(lat, lon):
    lat_idx = np.argmin(np.abs(lats - lat))
    lon_idx = np.argmin(np.abs(lons - lon))
    return mosaic_small[lat_idx, lon_idx]

print("Building 3D surface...")

fig = go.Figure(data=[
    go.Surface(
        z=mosaic_small,
        x=lons,
        y=lats,
        colorscale=[
            [0.0, "#0d5c63"], [0.15, "#3a8f6b"],
            [0.35, "#9bbb59"], [0.55, "#d4b96a"],
            [0.75, "#a0784f"], [0.9, "#8b7355"],
            [1.0, "#f5f5f5"]
        ],
        colorbar=dict(title="Elevation (m)", thickness=18, x=1.02),
        lighting=dict(
            ambient=0.6, diffuse=0.9,
            specular=0.2, roughness=0.6
        ),
        lightposition=dict(x=-100, y=100, z=8000),
        contours={
            "z": {"show": True, "usecolormap": False,
                  "highlightcolor": "white", "project_z": False,
                  "width": 1}
        }
    )
])

for name, cfg in DISTRICTS.items():
    n_pts = 30
    lat_top  = [cfg["lat"][1]] * n_pts
    lat_bot  = [cfg["lat"][0]] * n_pts
    lon_left  = np.full(n_pts, cfg["lon"][0])
    lon_right = np.full(n_pts, cfg["lon"][1])
    lon_range = np.linspace(cfg["lon"][0], cfg["lon"][1], n_pts)
    lat_range = np.linspace(cfg["lat"][0], cfg["lat"][1], n_pts)

    edges = [
        (lat_top, lon_range),
        (lat_bot, lon_range),
        (lat_range, lon_left),
        (lat_range, lon_right),
    ]

    for lat_e, lon_e in edges:
        z_e = [elevation_at(la, lo) + 80 for la, lo in zip(lat_e, lon_e)]
        fig.add_trace(go.Scatter3d(
            x=lon_e, y=lat_e, z=z_e,
            mode="lines",
            line=dict(color=cfg["color"], width=8),
            showlegend=False,
            hoverinfo="skip"
        ))

    center_lat = (cfg["lat"][0] + cfg["lat"][1]) / 2
    center_lon = (cfg["lon"][0] + cfg["lon"][1]) / 2
    label_z = elevation_at(cfg["lat"][1], center_lon) + 600

    fig.add_trace(go.Scatter3d(
        x=[center_lon], y=[cfg["lat"][1]], z=[label_z],
        mode="markers+text",
        marker=dict(size=6, color=cfg["color"]),
        text=[f"<b>{name.upper()}</b>"],
        textposition="top center",
        textfont=dict(size=16, color=cfg["color"]),
        showlegend=False
    ))

fig.update_layout(
    title=dict(
        text="3D Terrain Intelligence — Mandi, Kullu, Chamba<br>"
             "<sub>Drag to rotate · Scroll to zoom · Hover for elevation</sub>",
        font=dict(size=20),
        x=0.5
    ),
    scene=dict(
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        zaxis_title="Elevation (m)",
        aspectmode="manual",
        aspectratio=dict(x=1.6, y=1.2, z=0.5),
        camera=dict(
            eye=dict(x=-1.4, y=-1.8, z=1.1),
            center=dict(x=0, y=0, z=-0.15)
        ),
        zaxis=dict(range=[0, 8000])
    ),
    width=1200,
    height=850,
    margin=dict(l=0, r=0, t=90, b=0),
    paper_bgcolor="white"
)

out_file = f"{TERRAIN_DIR}\\terrain_3d.html"
fig.write_html(out_file)
print(f"\nSaved: {out_file}")
print("Open in browser — drag to rotate, scroll to zoom")