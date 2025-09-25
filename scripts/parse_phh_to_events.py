
# scripts/parse_phh_to_events.py
import gzip, json, re
from pathlib import Path

SRC = Path("data/raw/phh")
DST = Path("data/interim/phh_parsed")
DST.mkdir(parents=True, exist_ok=True)

HAND_SEP = re.compile(r"^# Game \d+", re.M)

for f in list(SRC.glob("*.phh")) + list(SRC.glob("*.phh.gz")):
    data = gzip.open(f, 'rt', encoding='utf-8') if f.suffix == '.gz' else open(f, 'r', encoding='utf-8')
    text = data.read()
    data.close()

    hands = HAND_SEP.split(text)
    out_path = DST / (f.stem.replace('.phh','') + ".jsonl")
    with open(out_path, 'w', encoding='utf-8') as w:
        for h in hands:
            if not h.strip():
                continue
            obj = {"raw": h}
            w.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print("→", out_path.name)
