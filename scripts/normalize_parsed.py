# scripts/normalize_parsed.py
"""
Normalitza els .jsonl parsejats (data/interim/phh_parsed).
Per cada <name>.jsonl crea <name>.fixed.jsonl amb camps top-level
players, actions, finishing_stacks, hand si s'han trobat dins
de les strings d'events.
"""
import json, re, ast
from pathlib import Path

SRC = Path('data/interim/phh_parsed')
files = sorted([f for f in SRC.glob('*.jsonl') if not f.name.endswith('.fixed.jsonl')])
if not files:
    print('No .jsonl files found in', SRC)
    raise SystemExit(0)

def try_literal(s):
    try:
        return ast.literal_eval(s)
    except Exception:
        return None

def extract_fields(obj):
    changed = False
    # assegura que events és una llista de strings
    events = obj.get('events', [])
    if not isinstance(events, list):
        return False
    for ev in events:
        evs = ev.strip()
        # players = [...]
        m = re.match(r"\s*players\s*=\s*(\[.*\])\s*$", evs)
        if m and 'players' not in obj:
            val = try_literal(m.group(1))
            if isinstance(val, list):
                obj['players'] = val
                changed = True
        # actions = [...]
        m = re.match(r"\s*actions\s*=\s*(\[.*\])\s*$", evs)
        if m and 'actions' not in obj:
            val = try_literal(m.group(1))
            if isinstance(val, list):
                obj['actions'] = val
                changed = True
        # finishing_stacks = [...]
        m = re.match(r"\s*finishing_stacks\s*=\s*(\[.*\])\s*$", evs)
        if m and 'finishing_stacks' not in obj:
            val = try_literal(m.group(1))
            if isinstance(val, list):
                obj['finishing_stacks'] = val
                changed = True
        # hand = N
        m = re.match(r"\s*hand\s*=\s*(\d+)\s*$", evs)
        if m and 'hand' not in obj:
            try:
                obj['hand'] = int(m.group(1))
                changed = True
            except Exception:
                pass
    return changed

count = 0
for f in files:
    try:
        txt = f.read_text(encoding='utf-8', errors='replace').strip()
        obj = json.loads(txt)
    except Exception as e:
        print(f"SKIP {f.name} (invalid json):", e)
        continue

    changed = extract_fields(obj)
    out = f.with_name(f.stem + '.fixed.jsonl')
    out.write_text(json.dumps(obj, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"WROTE {out.name} (changed={changed})")
    count += 1

print('Done. Processed', count, 'files.')
