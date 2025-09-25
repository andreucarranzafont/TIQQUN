# logic.py — TIQQUN PRO
from typing import NamedTuple, List

# NOVES DEPENDÈNCIES (Paquet PRO)
from modules.equity import estimate_equity
from modules.ranges import PreflopRanges

# Precarrega rangs (JSON a data/refs/preflop_ranges.json)
_RANGES = PreflopRanges()

class TechEval(NamedTuple):
    p_win: float          # Equity real 0..1
    p_improve: float      # Aproximació simple a millora (draws)
    ev_hint: float        # EV normalitzat [-1..1] via pot odds
    position_score: float # Posicional 0..1

# ----------------------- UTILITATS EXISTENTS -----------------------

def estimate_p_improve(hero: List[str], board: List[str]) -> float:
    """
    Aproximació lleugera a la probabilitat de millorar (flush/straight draws).
    Mantinc l'esperit del teu càlcul original, però pots substituir-ho per
    un càlcul exacte si vols en una següent iteració.
    """
    if not hero:
        return 0.0
    has_suit_pair = len(hero) >= 2 and hero[0][-1] == hero[1][-1]
    suit_on_board = sum(1 for c in board if c and hero and c[-1] == hero[0][-1])
    p_flush_draw = 0.18 if (has_suit_pair and suit_on_board >= 2) else 0.06
    p_straight_draw = 0.10
    return min(0.6, p_flush_draw + p_straight_draw)

def pot_odds_ev(pot: float, to_call: float, p_win: float, reward_mult: float = 1.0) -> float:
    """
    Indici d’EV: p_win*reward - (1-p_win)*cost, normalitzat a [-1..1].
    """
    if to_call <= 0:
        return 0.0
    reward = pot * reward_mult
    cost = to_call
    ev = p_win * reward - (1 - p_win) * cost
    scale = max(1.0, pot + to_call)
    return max(-1.0, min(1.0, ev / scale))

def position_score(seat_number: int, total_players: int) -> float:
    """
    Simple: com més a prop del BTN, millor (0..1).
    """
    idx_from_end = (total_players - seat_number)
    return max(0.0, min(1.0, idx_from_end / max(1, total_players-1)))

# ----------------------- NOVETAT CLAU: EQUITY REAL -----------------------

def estimate_p_win(
    hero: List[str],
    board: List[str],
    players: int,
    posicio_rival: str = "CO",
    accio_rival: str = "open",
    trials: int = 20000,
) -> float:
    """
    Equity real de l'Hero contra el rang del rival segons posició/acció,
    via Monte Carlo. Si el rang queda buit (per cartes bloquejades),
    fa sample de rival random (gestionat a estimate_equity).
    """
    villain_combos = _RANGES.combos_for(posicio_rival, accio_rival)
    return estimate_equity(hero, board, villain_combos, trials=trials)

def tech_eval(
    hero: List[str],
    board: List[str],
    players: int,
    pot: float,
    to_call: float,
    seat_num: int,
    posicio_rival: str = "CO",
    accio_rival: str = "open",
    trials: int = 20000,
) -> TechEval:
    """
    Aglutina mètriques tècniques. Manté la teva interfície antiga però
    ara permet passar posició/acció del rival per ajustar el rang.
    """
    pwin = estimate_p_win(hero, board, players, posicio_rival, accio_rival, trials=trials)
    pimp = estimate_p_improve(hero, board)
    evh  = pot_odds_ev(pot, to_call, pwin, reward_mult=1.0)
    pos  = position_score(seat_num, players)
    return TechEval(pwin, pimp, evh, pos)
