import pandas as pd

df = pd.read_parquet(
    r'C:\Users\admin\Desktop\rainfall agent\climate-data\processed\himachal_rainfall.parquet'
)

districts = {
    "Mandi":  {"lat": (31.5, 32.1), "lon": (76.7, 77.4)},
    "Kullu":  {"lat": (31.7, 32.5), "lon": (77.0, 77.8)},
    "Chamba": {"lat": (32.4, 33.2), "lon": (75.5, 77.0)}
}

def assign_district(row):
    for name, bounds in districts.items():
        if (bounds["lat"][0] <= row["LATITUDE"] <= bounds["lat"][1] and
            bounds["lon"][0] <= row["LONGITUDE"] <= bounds["lon"][1]):
            return name
    return None

print("Assigning districts...")
df["DISTRICT"] = df.apply(assign_district, axis=1)
df = df[df["DISTRICT"].notna()].copy()
print(f"Rows after filtering: {len(df):,}")
print(f"Districts found: {df['DISTRICT'].unique()}")

def classify(mm):
    if mm >= 204.5: return "Extremely Heavy"
    if mm >= 115.6: return "Very Heavy"
    if mm >=  64.5: return "Heavy"
    if mm >=  35.5: return "Rather Heavy"
    if mm >=  15.6: return "Moderate"
    return "Normal"

df["CATEGORY"] = df["RAINFALL"].apply(classify)
df["YEAR"]     = pd.to_datetime(df["TIME"]).dt.year
df["MONTH"]    = pd.to_datetime(df["TIME"]).dt.month

daily = (
    df.groupby(["TIME", "DISTRICT"])["RAINFALL"]
    .mean()
    .reset_index()
    .rename(columns={"RAINFALL": "AVG_RAINFALL_MM"})
)
daily["YEAR"]     = pd.to_datetime(daily["TIME"]).dt.year
daily["MONTH"]    = pd.to_datetime(daily["TIME"]).dt.month
daily["CATEGORY"] = daily["AVG_RAINFALL_MM"].apply(classify)

print("\nDaily district averages (first 10 rows):")
print(daily.head(10))

extreme = daily[daily["AVG_RAINFALL_MM"] >= 64.5]
yearly_extreme = (
    extreme.groupby(["YEAR", "DISTRICT"])
    .size()
    .reset_index(name="EXTREME_DAYS")
)
print("\nExtreme rain days per year per district:")
print(yearly_extreme.to_string())

peak = (
    daily.groupby("DISTRICT")["AVG_RAINFALL_MM"]
    .max()
    .reset_index()
    .rename(columns={"AVG_RAINFALL_MM": "PEAK_DAILY_MM"})
)
print("\nPeak single-day rainfall per district:")
print(peak)

monsoon = daily[daily["MONTH"].between(6, 9)]
monsoon_stats = (
    monsoon.groupby(["YEAR", "DISTRICT"])["AVG_RAINFALL_MM"]
    .agg(["sum", "max", "mean"])
    .reset_index()
    .rename(columns={
        "sum":  "MONSOON_TOTAL_MM",
        "max":  "PEAK_DAY_MM",
        "mean": "AVG_DAILY_MM"
    })
)
print("\nMonsoon stats per year per district:")
print(monsoon_stats.to_string())

out = r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed\mandi_kullu_chamba.parquet"
daily.to_parquet(out, index=False)
print(f"\nSaved to: {out}")
print(f"Shape: {daily.shape}")

daily.to_csv(
    r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed\mandi_kullu_chamba.csv",
    index=False
)
print("CSV also saved.")
