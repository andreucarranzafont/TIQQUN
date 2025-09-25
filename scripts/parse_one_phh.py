import gzip, json, sys
from pathlib import Path

# si passes ruta com a argument, la fa servir; altrament agafa el primer fitxer de data/raw/phh_test
arg = sys.argv[1] if len(sys.argv) > 1 else None
if arg:
    src = Path(arg)
else:
    src_folder = Path('data/raw/phh_test')
    files = list(src_folder.glob('*.phh')) + list(src_folder.glob('*.phh.gz'))
    if not files:
        raise SystemExit('No phh files in data/raw/phh_test')
    src = files[0]

OUT = Path('data/interim/phh_parsed')
OUT.mkdir(parents=True, exist_ok=True)

def parse_file(path: Path):
    if path.suffix == '.gz':
        f = gzip.open(path, 'rt', encoding='utf-8', errors='ignore')
    else:
        f = open(path, 'r', encoding='utf-8', errors='ignore')
    hand = {'events': []}
    for line in f:
        line = line.strip()
        if not line:
            continue
        # detecta separador de mà (alguns PHH usen "# Game" o "HAND")
        if line.startswith('# Game') or line.startswith('HAND'):
            if hand['events']:
                yield hand
            hand = {'events': []}
        hand['events'].append(line)
    if hand['events']:
        yield hand
    f.close()

out_path = OUT / (src.stem + '.jsonl')
with open(out_path, 'w', encoding='utf-8') as out:
    for hand in parse_file(src):
        out.write(json.dumps(hand, ensure_ascii=False) + '\\n')

print('→ parsed:', src.name, '->', out_path)
