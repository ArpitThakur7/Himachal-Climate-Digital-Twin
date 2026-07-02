# ============================================
# PROJECT SCOPE — DO NOT CHANGE
# Districts : Mandi, Kullu, Chamba
# Source    : NASA GPM IMERG via OpenDAP
# File      : download_gpm.py
# ============================================

import requests
import os
from datetime import datetime, timedelta

OUT = r"C:\Users\admin\Desktop\rainfall agent\climate-data\satellite"
os.makedirs(OUT, exist_ok=True)

# NASA Earthdata credentials — register free at earthdata.nasa.gov
USERNAME = "your_earthdata_username"
PASSWORD = "your_earthdata_password"

def download_gpm_day(date):
    year  = date.strftime("%Y")
    month = date.strftime("%m")
    day   = date.strftime("%d")
    doy   = date.strftime("%j")

    filename = (
        f"3B-DAY.MS.MRG.3IMERG.{year}{month}{day}"
        f"-S000000-E235959.V07.nc4"
    )
    url = (
        f"https://gpm1.gesdisc.eosdis.nasa.gov/data/"
        f"GPM_L3/GPM_3IMERGDF.07/{year}/{month}/{filename}"
    )
    out_file = f"{OUT}\\gpm_{year}{month}{day}.nc4"

    if os.path.exists(out_file):
        return True

    try:
        r = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=30,
            stream=True
        )
        if r.status_code == 200:
            with open(out_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  Downloaded: {year}-{month}-{day}")
            return True
        else:
            print(f"  Failed {year}-{month}-{day}: {r.status_code}")
            return False
    except Exception as e:
        print(f"  Error {year}-{month}-{day}: {e}")
        return False

def download_monsoon_seasons():
    print("Downloading GPM monsoon season data 2020-2025...")
    start = datetime(2020, 6, 1)
    end   = datetime(2025, 9, 30)
    current = start
    count = 0

    while current <= end:
        if current.month in [6, 7, 8, 9]:
            if download_gpm_day(current):
                count += 1
        current += timedelta(days=1)

    print(f"\nDone. Downloaded {count} daily files.")

if __name__ == "__main__":
    download_monsoon_seasons()