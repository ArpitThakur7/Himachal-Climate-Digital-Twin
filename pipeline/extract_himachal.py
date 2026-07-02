import xarray as xr
import pandas as pd
import os
from tqdm import tqdm

# ==============================
# FOLDERS
# ==============================

INPUT_FOLDER = r"C:\Users\admin\Desktop\rainfall agent\climate-data\rainfall"

OUTPUT_FOLDER = r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==============================
# HIMACHAL BOUNDING BOX
# ==============================

LAT_MIN = 30.0
LAT_MAX = 33.5

LON_MIN = 75.5
LON_MAX = 79.5

# ==============================
# PROCESS FILES
# ==============================

all_data = []

files = sorted([
    f for f in os.listdir(INPUT_FOLDER)
    if f.endswith(".nc")
])

print(f"\nFound {len(files)} files\n")

for file in tqdm(files):

    path = os.path.join(INPUT_FOLDER, file)

    ds = xr.open_dataset(path)

    # Extract Himachal directly from xarray
    hp = ds.sel(
        LATITUDE=slice(LAT_MIN, LAT_MAX),
        LONGITUDE=slice(LON_MIN, LON_MAX)
    )

    # Convert to dataframe
    df = hp["RAINFALL"].to_dataframe().reset_index()

    # Remove missing values
    df = df.dropna()

    all_data.append(df)

# ==============================
# MERGE ALL YEARS
# ==============================

final_df = pd.concat(
    all_data,
    ignore_index=True
)

print("\nFinal Shape:")
print(final_df.shape)

print("\nDate Range:")
print(final_df["TIME"].min())
print(final_df["TIME"].max())

# ==============================
# SAVE PARQUET
# ==============================

output_file = os.path.join(
    OUTPUT_FOLDER,
    "himachal_rainfall.parquet"
)

final_df.to_parquet(
    output_file,
    index=False
)

print(f"\nSaved:")
print(output_file)