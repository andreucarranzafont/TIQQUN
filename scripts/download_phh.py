
# scripts/download_phh.py
import urllib.request
from pathlib import Path

TARGET = Path("data/raw/phh")
TARGET.mkdir(parents=True, exist_ok=True)

# TODO: Afegeix aquí les URLs exactes del dataset (Zenodo/GitHub).
URLS = [
    # "https://example.com/nlhe_part1.phh.gz",
]

for url in URLS:
    fname = TARGET / Path(url).name
    print("↓", fname.name)
    urllib.request.urlretrieve(url, fname)
print("Done.")
