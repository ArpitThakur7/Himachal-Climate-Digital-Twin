# ============================================
# PROJECT SCOPE — DO NOT CHANGE
# Districts : Mandi, Kullu, Chamba
# File      : view_research_map.py
# Research-grade infrastructure intelligence map
# ============================================

import geopandas as gpd
import folium
from folium.plugins import MiniMap, MeasureControl, Fullscreen, MarkerCluster

DATA = r"C:\Users\admin\Desktop\rainfall agent\climate-data\infrastructure"
OUT  = DATA

DISTRICTS = {
    "mandi":  {"color": "#D85A30", "center": [31.71, 76.93]},
    "kullu":  {"color": "#378ADD", "center": [31.96, 77.11]},
    "chamba": {"color": "#1D9E75", "center": [32.55, 76.13]},
}

FACILITY_STYLE = {
    "hospitals": {"icon": "plus-square",      "color": "red",       "size": 1},
    "bridges":   {"icon": "road",             "color": "black",     "size": 1},
    "schools":   {"icon": "graduation-cap",   "color": "blue",      "size": 1},
    "police":    {"icon": "shield-alt",       "color": "darkgreen", "size": 1},
    "helipads":  {"icon": "helicopter",       "color": "purple",    "size": 1},
}

m = folium.Map(
    location=[31.9, 76.9],
    zoom_start=9,
    tiles=None,
    control_scale=True
)

folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attr="CartoDB Positron",
    name="Light basemap",
    overlay=False
).add_to(m)

folium.TileLayer(
    tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attr="OpenTopoMap",
    name="Terrain basemap",
    overlay=False
).add_to(m)

folium.TileLayer(
    tiles="OpenStreetMap",
    name="Street basemap",
    overlay=False
).add_to(m)

print("Building research map...")

# ── road network — styled as transport corridors ──
for d, cfg in DISTRICTS.items():
    try:
        roads = gpd.read_file(f"{DATA}\\{d}_roads.gpkg")
        roads = roads.to_crs(epsg=4326)

        fg = folium.FeatureGroup(
            name=f"{d.title()} — road network ({len(roads)} segments)",
            show=True
        )
        folium.GeoJson(
            roads,
            style_function=lambda x, c=cfg["color"]: {
                "color": c,
                "weight": 1.2,
                "opacity": 0.55
            }
        ).add_to(fg)
        fg.add_to(m)
        print(f"  {d}: {len(roads)} road segments added")
    except Exception as e:
        print(f"  {d} roads error: {e}")

# ── critical facilities — clustered markers ──
for d, cfg in DISTRICTS.items():
    for label, style in FACILITY_STYLE.items():
        try:
            gdf = gpd.read_file(f"{DATA}\\{d}_{label}.gpkg")
            gdf = gdf.to_crs(epsg=4326)
            if len(gdf) == 0:
                continue

            cluster = MarkerCluster(
                name=f"{d.title()} — {label} ({len(gdf)})"
            )

            for _, row in gdf.iterrows():
                geom = row.geometry
                lat, lon = (
                    (geom.y, geom.x) if geom.geom_type == "Point"
                    else (geom.centroid.y, geom.centroid.x)
                )
                name = row.get("name", label.title())
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(
                        f"<b>{name}</b><br>"
                        f"District: {d.title()}<br>"
                        f"Type: {label.title()}",
                        max_width=200
                    ),
                    tooltip=f"{label.title()} — {d.title()}",
                    icon=folium.Icon(
                        color=style["color"],
                        icon=style["icon"],
                        prefix="fa"
                    )
                ).add_to(cluster)

            cluster.add_to(m)
            print(f"  {d} {label}: {len(gdf)} markers added")
        except Exception as e:
            print(f"  {d} {label} error: {e}")

# ── district boundary markers ──
for d, cfg in DISTRICTS.items():
    folium.Marker(
        cfg["center"],
        icon=folium.DivIcon(html=f"""
            <div style="font-size:14px;font-weight:bold;
                        color:{cfg['color']};
                        text-shadow:1px 1px 2px white,
                        -1px -1px 2px white,1px -1px 2px white,
                        -1px 1px 2px white;">
                {d.upper()}
            </div>
        """)
    ).add_to(m)

# ── controls ──
folium.LayerControl(collapsed=False).add_to(m)
MiniMap(toggle_display=True, position="bottomleft").add_to(m)
MeasureControl(primary_length_unit="kilometers").add_to(m)
Fullscreen(position="topleft").add_to(m)

# ── legend ──
legend_html = """
<div style="position: fixed; bottom: 30px; right: 30px; z-index: 9999;
            background: white; padding: 14px 18px; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 13px;
            font-family: sans-serif; line-height: 1.8;">
  <b style="font-size:14px;">Infrastructure Legend</b><br>
  <span style="color:#D85A30;">━━</span> Mandi roads<br>
  <span style="color:#378ADD;">━━</span> Kullu roads<br>
  <span style="color:#1D9E75;">━━</span> Chamba roads<br>
  <i class="fa fa-plus-square" style="color:red;"></i> Hospitals<br>
  <i class="fa fa-road" style="color:black;"></i> Bridges<br>
  <i class="fa fa-graduation-cap" style="color:blue;"></i> Schools<br>
  <i class="fa fa-shield-alt" style="color:darkgreen;"></i> Police<br>
  <i class="fa fa-helicopter" style="color:purple;"></i> Helipads<br>
  <hr style="margin:6px 0;">
  <span style="font-size:11px;color:#666;">
    Himachal Climate Digital Twin<br>
    Infrastructure Intelligence Layer
  </span>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ── title ──
title_html = """
<div style="position: fixed; top: 10px; left: 60px; z-index: 9999;
            background: white; padding: 10px 20px; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-family: sans-serif;">
  <span style="font-size:16px;font-weight:bold;color:#222;">
    Mandi, Kullu, Chamba — Infrastructure Intelligence Map
  </span><br>
  <span style="font-size:12px;color:#666;">
    Roads, hospitals, bridges, schools, police, helipads — OpenStreetMap
  </span>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

out_file = f"{OUT}\\infrastructure_research_map.html"
m.save(out_file)
print(f"\nSaved: {out_file}")
print("Open in browser to view.")