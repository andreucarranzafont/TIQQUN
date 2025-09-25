# repair_jsonl.py
import json
from pathlib import Path
p = Path('data/interim/phh_parsed')
files = sorted(p.glob('*.jsonl'))
if not files:
    print('No .jsonl files found in', p)
    raise SystemExit(1)

def extract_first_json(s: str):
    start = None
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == '\\\\':
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    return s[start:i+1]
    return None

for f in files:
    print('Processing', f.name)
    txt = f.read_text(encoding='utf-8', errors='replace')
    lines = [line for line in txt.splitlines() if line.strip()]
    if len(lines) == 0:
        print('  skipped (empty)')
        continue
    first = lines[0]
    try:
        obj = json.loads(first)
        print('  OK: first line is valid JSON')
        continue
    except Exception:
        extracted = extract_first_json(txt)
        if not extracted:
            print('  ERROR: could not locate a balanced JSON object in', f.name)
            continue
        try:
            obj = json.loads(extracted)
        except Exception as e2:
            print('  ERROR: extracted JSON still invalid:', e2)
            print('  snippet:', extracted[:800])
            continue
        out = f.with_suffix('.jsonl')
        out.write_text(json.dumps(obj, ensure_ascii=False) + '\\n', encoding='utf-8')
        print('  Repaired and rewrote', out.name)
print('Done.')
