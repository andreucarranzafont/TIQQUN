import json, sys
from pathlib import Path

p = Path('data/interim/phh_parsed')
files = sorted(p.glob('*.jsonl'))
if not files:
    print('No .jsonl files found in', p)
    sys.exit(1)

ok = True
for f in files:
    print('Checking', f.name)
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
            except Exception as e:
                print(f'ERROR in {f.name} line {i}:', e)
                print('SNIPPET:', line[:400])
                ok = False
                break

if ok:
    print('Done. All JSONL files look valid.')
else:
    print('Validation finished with errors.')
