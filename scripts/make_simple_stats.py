# make_simple_stats.py
import json
from pathlib import Path

src = Path('data/processed/player_stats.json')
if not src.exists():
    print('ERROR: no trobat data/processed/player_stats.json')
    raise SystemExit(1)

data = json.loads(src.read_text(encoding='utf-8'))
simple = {}

# Si l'estructura és dict, extraiem els camps clau per a cada jugador
if isinstance(data, dict):
    for k, v in data.items():
        if isinstance(v, dict):
            simple[k] = {
                'hands': v.get('hands', 0),
                'vpip': v.get('vpip', 0),
                'pfr': v.get('pfr', 0),
                'threebet': v.get('threebet', 0)
            }
        else:
            simple[k] = v
else:
    simple = {'summary': data}

out = Path('data/processed/player_stats_simple.json')
out.write_text(json.dumps(simple, ensure_ascii=False, indent=2), encoding='utf-8')
print('WROTE', out)
