# inspect_jsonl.py
from pathlib import Path
from json import JSONDecoder
p = Path('data/interim/phh_parsed')
files = sorted(p.glob('*.clean.jsonl'))
if not files:
    files = sorted(p.glob('*.jsonl'))
if not files:
    print('No .jsonl files found in', p)
    raise SystemExit(0)

dec = JSONDecoder()
for f in files:
    print('FILE =>', f)
    s = f.read_text(encoding='utf-8', errors='replace')
    print('LENGTH:', len(s))
    print('FIRST 800 repr:')
    print(repr(s[:800]))
    try:
        obj, idx = dec.raw_decode(s)
        print('raw_decode OK, idx:', idx)
        rem = s[idx:idx+400]
        print('REMAINING repr (next 400 chars):')
        print(repr(rem))
    except Exception as e:
        print('raw_decode FAILED:', e)
    print('-'*60)
