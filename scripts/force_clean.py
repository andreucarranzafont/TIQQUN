# force_clean.py
import json
from json import JSONDecoder
from pathlib import Path
p = Path('data/interim/phh_parsed/0.jsonl')
s = p.read_text(encoding='utf-8', errors='replace')
dec = JSONDecoder()
try:
    obj, idx = dec.raw_decode(s)
except Exception as e:
    print('ERROR: no s\'ha pogut extreure JSON amb raw_decode:', e)
    raise SystemExit(1)
out = json.dumps(obj, ensure_ascii=False)
p.write_text(out + '\n', encoding='utf-8')
print('WROTE cleaned 0.jsonl (length)', len(out)+1)
