import geopandas as gpd

river_file = r"C:\Users\admin\Desktop\rivers\HydroRIVERS_v10_as_shp\HydroRIVERS_v10_as.shp"

rivers = gpd.read_file(river_file)

print("Rows:", len(rivers))
print("\nColumns:")
print(rivers.columns)

print("\nFirst 5 Rows:")
print(rivers.head())

import geopandas as gpd

river_file = r"C:\Users\admin\Desktop\rivers\HydroRIVERS_v10_as_shp\HydroRIVERS_v10_as.shp"

rivers = gpd.read_file(river_file)

# Himachal Pradesh bounding box
hp_rivers = rivers.cx[
    75.5:79.5,
    30.0:33.8
]

print("Total Himachal River Segments:", len(hp_rivers))

output_file = r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed\hp_rivers.geojson"

hp_rivers.to_file(output_file, driver="GeoJSON")

print("Saved:", output_file)


import geopandas as gpd

hp = gpd.read_file(
    r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed\hp_rivers.geojson"
)

print(hp.total_bounds)