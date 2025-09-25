# scripts/extract_players.py
import json, re, ast
from pathlib import Path

p = Path('data/interim/phh_parsed/0.jsonl')
s = json.loads(p.read_text(encoding='utf-8', errors='replace'))
players = None
for ev in s.get('events', []):
    m = re.match(r"\s*players\s*=\s*(\[.*\])", ev)
    if m:
        players = ast.literal_eval(m.group(1))
        break

print('players found:', players)
