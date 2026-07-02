# ============================================
# PROJECT SCOPE — DO NOT CHANGE
# Districts : Mandi, Kullu, Chamba
# Source    : NASA SRTM 30m elevation
# File      : download_srtm.py
# ============================================

import requests
import os
import gzip
import shutil

OUT = r"C:\Users\admin\Desktop\rainfall agent\climate-data\terrain"
os.makedirs(OUT, exist_ok=True)

TILES = [
    "N31E076", "N31E077", "N31E078",
    "N32E075", "N32E076", "N32E077", "N32E078",
    "N33E075", "N33E076", "N33E077",
]

BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"

def download_tile(tile):
    lat_band = tile[:3]
    url = f"{BASE_URL}/{lat_band}/{tile}.hgt.gz"
    gz_file = f"{OUT}\\{tile}.hgt.gz"
    hgt_file = f"{OUT}\\{tile}.hgt"

    if os.path.exists(hgt_file):
        print(f"  {tile}: already downloaded")
        return True

    try:
        r = requests.get(url, timeout=30, stream=True)
        if r.status_code == 200:
            with open(gz_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            with gzip.open(gz_file, "rb") as f_in:
                with open(hgt_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            os.remove(gz_file)
            print(f"  {tile}: downloaded and extracted")
            return True
        else:
            print(f"  {tile}: failed status {r.status_code}")
            return False
    except Exception as e:
        print(f"  {tile}: error {e}")
        return False

def download_all():
    print("Downloading SRTM elevation tiles for Mandi Kullu Chamba...")
    success = 0
    for tile in TILES:
        if download_tile(tile):
            success += 1
    print(f"\nDone. {success}/{len(TILES)} tiles downloaded.")
    print(f"Saved to: {OUT}")

if __name__ == "__main__":
    download_all()