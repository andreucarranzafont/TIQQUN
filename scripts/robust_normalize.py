# scripts/robust_normalize.py
import json, re, ast
from pathlib import Path

SRC = Path('data/interim/phh_parsed')
files = sorted([f for f in SRC.glob('*.jsonl') if not f.name.endswith('.fixed2.jsonl')])
if not files:
    print('No .jsonl files found in', SRC)
    raise SystemExit(0)

def try_literal(s):
    try:
        return ast.literal_eval(s)
    except Exception:
        return None

for f in files:
    try:
        s = f.read_text(encoding='utf-8', errors='replace').strip()
        obj = json.loads(s)
    except Exception as e:
        print('SKIP', f.name, '(invalid json):', e)
        continue

    changed = False
    events = obj.get('events', [])
    if isinstance(events, list) and events:
        # combinem totes les events en una sola string per fer cerca tolerant
        all_text = " ".join(events)
        # players
        m = re.search(r"players\s*=\s*(\[[^\]]*\])", all_text)
        if m and 'players' not in obj:
            val = try_literal(m.group(1))
            if isinstance(val, list):
                obj['players'] = val
                changed = True
        # actions
        m = re.search(r"actions\s*=\s*(\[[^\]]*\])", all_text)
        if m and 'actions' not in obj:
            val = try_literal(m.group(1))
            if isinstance(val, list):
                obj['actions'] = val
                changed = True
        # finishing_stacks
        m = re.search(r"finishing_stacks\s*=\s*(\[[^\]]*\])", all_text)
        if m and 'finishing_stacks' not in obj:
            val = try_literal(m.group(1))
            if isinstance(val, list):
                obj['finishing_stacks'] = val
                changed = True
        # hand number
        m = re.search(r"hand\s*=\s*(\d+)", all_text)
        if m and 'hand' not in obj:
            try:
                obj['hand'] = int(m.group(1))
                changed = True
            except Exception:
                pass

    out = f.with_name(f.stem + '.fixed2.jsonl')
    out.write_text(json.dumps(obj, ensure_ascii=False) + '\n', encoding='utf-8')
    print('WROTE', out.name, 'changed=', changed)

print('Done. Processed', len(files), 'files.')
