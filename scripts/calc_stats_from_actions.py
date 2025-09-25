# scripts/calc_stats_from_actions.py
import json
from pathlib import Path

SRC = Path('data/interim/phh_parsed')
OUT = Path('data/processed/player_stats.json')

files = sorted(SRC.glob('*.jsonl'))
if not files:
    print('No .jsonl files found in', SRC)
    raise SystemExit(1)

# accumuladors
acc = {}   # name -> {'hands': int, 'vpip': int, 'pfr': int, 'threebet': int}

def ensure(name):
    if name not in acc:
        acc[name] = {'hands': 0, 'vpip': 0, 'pfr': 0, 'threebet': 0}

for f in files:
    try:
        s = f.read_text(encoding='utf-8', errors='replace').strip()
        obj = json.loads(s)
    except Exception as e:
        print('SKIP', f.name, '(invalid json):', e)
        continue

    players = obj.get('players') or []
    actions = obj.get('actions') or []
    if not isinstance(players, list):
        continue

    # preparar per mà
    for p in players:
        ensure(p)
        acc[p]['hands'] += 1

    # definir map p1->player_name
    seat_to_name = {}
    for i, name in enumerate(players):
        seat_to_name[f'p{i+1}'] = name

    # recollir accions preflop: fins al primer 'd db' (flop) o fins a primer 'd ' que tingui db
    preflop = []
    for a in actions:
        # normalitzar
        if isinstance(a, str) and a.strip().startswith('d db'):
            break
        preflop.append(a)

    # per detectar raises seqüencialment
    raise_count = 0

    # per mà: flags temporals per jugador
    vpip_flag = {name: False for name in players}
    pfr_flag  = {name: False for name in players}
    threebet_flag = {name: False for name in players}

    for act in preflop:
        if not isinstance(act, str):
            continue
        parts = act.strip().split()
        if not parts:
            continue
        # només processem accions de jugador que normalment comencen per 'pN'
        if parts[0].startswith('p'):
            token = parts[0]        # ex: 'p4'
            verb = parts[1] if len(parts) > 1 else ''
            name = seat_to_name.get(token)
            if not name:
                continue

            verb_low = verb.lower()

            # fold
            if verb_low == 'f' or verb_low == 'fold':
                continue

            # ignorar posts de blinds si apareixen explícitament
            if verb_low in ('sb','bb','post','postsb','postbb'):
                continue

            # heurística VPIP: qualsevol acció voluntària que no sigui fold/check/blind
            # (call, raise, bet, cc, etc.)
            if not vpip_flag[name]:
                if ('c' in verb_low) or ('b' in verb_low) or ('r' in verb_low) or verb_low.isdigit():
                    # in many notations call contains 'c' (cc), raise contains 'r' or 'br'
                    vpip_flag[name] = True

            # detectar raises per PFR / threebet: considerem raise si hi ha 'r' al verb
            is_raise = False
            if 'r' in verb_low or verb_low.startswith('b') or verb_low.startswith('raise') or 'raise' in verb_low:
                is_raise = True

            if is_raise:
                raise_count += 1
                # qui fa raise compta com PFR
                if not pfr_flag[name]:
                    pfr_flag[name] = True
                # si raise_count == 2 => això és un 3-bet (open=1, re-raise=2 -> 3-bet)
                if raise_count == 2:
                    threebet_flag[name] = True

            # en alguns casos verbs com 'cbr' (call then bet/raise) tenen 'r' i ja seran comptats com raise

    # sumaritzar flags a acumuladors
    for name in players:
        if vpip_flag.get(name):
            acc[name]['vpip'] += 1
        if pfr_flag.get(name):
            acc[name]['pfr'] += 1
        if threebet_flag.get(name):
            acc[name]['threebet'] += 1

# convertir a percentatges (enter, redondejat)
out = {}
for name, d in acc.items():
    hands = d['hands'] or 1
    out[name] = {
        'hands': d['hands'],
        'vpip': int(round(d['vpip'] / hands * 100)) ,
        'pfr':  int(round(d['pfr']  / hands * 100)) ,
        'threebet': int(round(d['threebet'] / hands * 100))
    }

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print('WROTE', OUT, 'players:', list(out.keys()))
