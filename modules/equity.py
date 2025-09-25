
# modules/equity.py
from __future__ import annotations
import random
import itertools
from typing import List, Tuple, Dict, Optional

RANKS = "23456789TJQKA"
SUITS = "cdhs"  # clubs, diamonds, hearts, spades
ALL_CARDS = [r + s for r in RANKS for s in SUITS]

# ---------- Utilitats bàsiques ----------

def card_int(card: str) -> Tuple[int, str]:
    r, s = card[0], card[1]
    return RANKS.index(r), s

def deck_without(excluded: List[str]) -> List[str]:
    excl = set(excluded)
    return [c for c in ALL_CARDS if c not in excl]

# ---------- Avaluador senzill (fallback) ----------
HAND_RANK_ORDER = {
    "high": 0,
    "pair": 1,
    "two_pair": 2,
    "trips": 3,
    "straight": 4,
    "flush": 5,
    "full_house": 6,
    "quads": 7,
    "straight_flush": 8,
}

def best5_from7(cards7: List[str]) -> Tuple[int, List[int]]:
    """Retorna (categoria, tie_breakers) per comparar mans. Categoria creixent = pitjor.
    tie_breakers és una llista de ranks (0..12) ordenats de major a menor per trencar empats.
    """
    ranks = [RANKS.index(c[0]) for c in cards7]
    suits = [c[1] for c in cards7]

    # Comptes
    by_rank: Dict[int, int] = {}
    for rv in ranks:
        by_rank[rv] = by_rank.get(rv, 0) + 1

    # Flush
    flush_suit = None
    for s in SUITS:
        if suits.count(s) >= 5:
            flush_suit = s
            break

    # Llista de cartes ordenades per rank
    uniq_ranks = sorted(set(ranks))

    # Straight helper (considera A com a low també)
    def best_straight(vals: List[int]) -> Optional[int]:
        vset = set(vals)
        for high in range(12, 3, -1):
            need = {high - i for i in range(5)}
            if need.issubset(vset):
                return high
        # wheel A-2-3-4-5
        if {12, 0, 1, 2, 3}.issubset(vset):
            return 3  # 5 alta
        return None

    # Straight flush
    if flush_suit:
        flush_cards = [RANKS.index(c[0]) for c in cards7 if c[1] == flush_suit]
        sf_high = best_straight(sorted(set(flush_cards)))
        if sf_high is not None:
            return (HAND_RANK_ORDER["straight_flush"], [sf_high])

    # Quads, Full, Trips, Pairs
    counts = sorted(((cnt, rv) for rv, cnt in by_rank.items()), reverse=True)
    if counts[0][0] == 4:
        quad = counts[0][1]
        kick = max(rv for rv in uniq_ranks if rv != quad)
        return (HAND_RANK_ORDER["quads"], [quad, kick])

    if counts[0][0] == 3 and any(c == 2 for c, _ in counts[1:]):
        trips = counts[0][1]
        pair = max(rv for cnt, rv in counts if cnt == 2)
        return (HAND_RANK_ORDER["full_house"], [trips, pair])

    if flush_suit:
        top5 = sorted([RANKS.index(c[0]) for c in cards7 if c[1] == flush_suit], reverse=True)[:5]
        return (HAND_RANK_ORDER["flush"], top5)

    st_high = best_straight(uniq_ranks)
    if st_high is not None:
        return (HAND_RANK_ORDER["straight"], [st_high])

    if counts[0][0] == 3:
        trips = counts[0][1]
        kickers = sorted([rv for rv in uniq_ranks if rv != trips], reverse=True)[:2]
        return (HAND_RANK_ORDER["trips"], [trips] + kickers)

    if counts[0][0] == 2 and counts[1][0] == 2:
        hi, lo = sorted([counts[0][1], counts[1][1]], reverse=True)
        kick = max(rv for rv in uniq_ranks if rv not in (hi, lo))
        return (HAND_RANK_ORDER["two_pair"], [hi, lo, kick])

    if counts[0][0] == 2:
        pair = counts[0][1]
        kickers = sorted([rv for rv in uniq_ranks if rv != pair], reverse=True)[:3]
        return (HAND_RANK_ORDER["pair"], [pair] + kickers)

    top5 = sorted(uniq_ranks, reverse=True)[:5]
    return (HAND_RANK_ORDER["high"], top5)

def compare7(a7: List[str], b7: List[str]) -> int:
    ca = best5_from7(a7)
    cb = best5_from7(b7)
    if ca[0] != cb[0]:
        return 1 if ca[0] > cb[0] else -1
    for x, y in itertools.zip_longest(ca[1], cb[1], fillvalue=-1):
        if x != y:
            return 1 if x > y else -1
    return 0

# ---------- Equity Monte Carlo ----------
def estimate_equity(hero_hole: List[str], board: List[str], villain_range: List[List[str]], trials: int = 20000) -> float:
    """Equity de l'heroi contra 1 vilà amb rang de combos."""
    used = set(hero_hole + board)
    combos = [c for c in villain_range if not (set(c) & used)]
    if not combos:
        combos = []
    wins = ties = 0
    for _ in range(trials):
        deck = deck_without(hero_hole + board)
        if combos:
            v = random.choice(combos)
            for x in v:
                deck.remove(x)
        else:
            v = random.sample(deck, 2)
            for x in v:
                deck.remove(x)
        need = 5 - len(board)
        runout = random.sample(deck, need)
        a7 = hero_hole + board + runout
        b7 = v + board + runout
        cmp_ = compare7(a7, b7)
        if cmp_ > 0:
            wins += 1
        elif cmp_ == 0:
            ties += 1
    return (wins + 0.5 * ties) / max(1, trials)

def expand_range(mask: str) -> List[List[str]]:
    """Converteix 'AKs', 'TT', 'A5s-A2s', 'KQo' a llista de combos."""
    def gen_suited(a, b):
        out = []
        for s in SUITS:
            out.append([a + s, b + s])
        return out

    def gen_off(a, b):
        out = []
        for s1 in SUITS:
            for s2 in SUITS:
                if s1 != s2:
                    out.append([a + s1, b + s2])
        return out

    def gen_pair(r):
        out = []
        for i, s1 in enumerate(SUITS):
            for s2 in SUITS[i+1:]:
                out.append([r + s1, r + s2])
        return out

    mask = mask.strip()
    if len(mask) == 2 and mask[0] == mask[1]:
        return gen_pair(mask[0])
    if len(mask) == 3 and mask[2] in "so":
        a, b, typ = mask[0], mask[1], mask[2]
        return gen_suited(a, b) if typ == 's' else gen_off(a, b)
    if '-' in mask:  # e.g. A5s-A2s
        lo, hi = mask.split('-')
        if len(lo) == 3 and lo[2] == 's' and len(hi) == 3 and hi[2] == 's' and lo[0] == hi[0]:
            a = lo[0]
            r_lo = RANKS.index(lo[1])
            r_hi = RANKS.index(hi[1])
            out = []
            for ri in range(min(r_lo, r_hi), max(r_lo, r_hi) + 1):
                out += gen_suited(a, RANKS[ri])
            return out
    return []
