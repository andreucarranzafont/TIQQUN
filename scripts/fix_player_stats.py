# scripts/fix_player_stats.py
import json
from pathlib import Path

SRC = Path('data/interim/phh_parsed')
OUT = Path('data/processed/player_stats.json')

files = sorted(SRC.glob('*.jsonl'))
if not files:
    print('No .jsonl files found in', SRC)
    raise SystemExit(1)

stats = {}
for f in files:
    try:
        s = f.read_text(encoding='utf-8', errors='replace').strip()
        obj = json.loads(s)
    except Exception as e:
        print('SKIP', f.name, '(invalid json):', e)
        continue

    players = obj.get('players') or []
    if not isinstance(players, list):
        continue

    # considerem que cada mà compta per a cada jugador present a la llista
    for name in players:
        if name not in stats:
            stats[name] = {'hands': 0, 'vpip': 0, 'pfr': 0, 'threebet': 0}
        stats[name]['hands'] += 1

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
print('WROTE', OUT, 'players:', list(stats.keys()))
