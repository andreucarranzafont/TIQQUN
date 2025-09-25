
# scripts/build_player_stats.py
import json
from pathlib import Path
from collections import defaultdict

SRC = Path("data/interim/phh_parsed")
DST = Path("data/processed")
DST.mkdir(parents=True, exist_ok=True)

stats = defaultdict(lambda: {'hands': 0, 'vpip': 0, 'pfr': 0, 'threebet': 0})

for f in SRC.glob("*.jsonl"):
    with open(f, 'r', encoding='utf-8') as r:
        for line in r:
            obj = json.loads(line)
            pid = obj.get('hero', 'unknown')
            s = stats[pid]
            s['hands'] += 1

with open(DST / 'player_stats.json', 'w', encoding='utf-8') as w:
    json.dump(stats, w, ensure_ascii=False, indent=2)
print("→ player_stats.json")
