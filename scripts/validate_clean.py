# validate_clean.py
import glob, json, sys
files = glob.glob('data/interim/phh_parsed/*.clean.jsonl')
if not files:
    print('No clean files to validate.')
    sys.exit(0)
ok = True
for f in files:
    print('Validating', f)
    with open(f, 'r', encoding='utf-8') as fh:
        for i,line in enumerate(fh,1):
            line=line.strip()
            if not line: continue
            try:
                json.loads(line)
            except Exception as e:
                print('ERROR', f, 'line', i, e)
                ok = False
                break
print('CLEAN validation OK' if ok else 'CLEAN validation FAILED')
