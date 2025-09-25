
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass(frozen=True)
class Sefirah:
    name: str
    column: str   # 'left', 'right', 'middle', 'hidden'
    base_weight: float  # 0..1

SEFIROT: Dict[str, Sefirah] = {
    "Keter": Sefirah("Keter", "middle", 0.95),
    "Hokhmah": Sefirah("Hokhmah", "right", 0.85),
    "Binah": Sefirah("Binah", "left", 0.85),
    "Hesed": Sefirah("Hesed", "right", 0.75),
    "Gevurah": Sefirah("Gevurah", "left", 0.78),
    "Tiferet": Sefirah("Tiferet", "middle", 0.90),
    "Netzach": Sefirah("Netzach", "right", 0.72),
    "Hod": Sefirah("Hod", "left", 0.70),
    "Yesod": Sefirah("Yesod", "middle", 0.74),
    "Malkhut": Sefirah("Malkhut", "middle", 0.68),
    "Daat": Sefirah("Daat", "hidden", 1.00),
}

SUIT_ELEMENT = {"C": "aigua", "D": "terra", "T": "foc", "P": "aire"}  # C=cor, D=diamant, T=trèvol, P=piques
ELEMENT_COLUMN_BONUS = {"aigua": ("right", +0.03), "terra": ("middle", +0.03), "foc": ("left", +0.03), "aire": ("middle", +0.02)}

CARD_VALUE_BASE = {
    "A": ("Keter", 0.90),
    "K": ("Tiferet", 0.82),
    "Q": ("Tiferet", 0.80),
    "J": ("Tiferet", 0.78),
    "10": ("Hesed", 0.70),
    "9": ("Binah", 0.66),
    "8": ("Binah", 0.64),
    "7": ("Netzach", 0.62),
    "6": ("Gevurah", 0.60),
    "5": ("Gevurah", 0.58),
    "4": ("Hod", 0.56),
    "3": ("Yesod", 0.55),
    "2": ("Yesod", 0.54),
}

def _suit(card: str) -> str:
    return ''.join([ch for ch in card if ch.isalpha()])[-1]

def suit_element_bonus(card: str) -> float:
    suit = _suit(card)
    elem = SUIT_ELEMENT.get(suit, None)
    if not elem:
        return 0.0
    _, bonus = ELEMENT_COLUMN_BONUS[elem]
    return bonus

def sefirah_value(card: str) -> Tuple[str, float]:
    val = card[:-1]
    if val == 'T':  # 10 shorthand
        val = '10'
    sef, base = CARD_VALUE_BASE.get(val, ("Malkhut", 0.50))
    return sef, max(0.0, min(1.0, base + suit_element_bonus(card)))

def flow_score(preflop_cards: List[str], street: str, board: List[str]) -> float:
    # Base: pesos de les teves dues cartes
    weights = []
    for c in preflop_cards:
        _, w = sefirah_value(c)
        weights.append(w)
    base = sum(weights)/max(1, len(weights))

    # Ajust per textura del board
    left = right = middle = 0.0
    for c in board:
        sef, w = sefirah_value(c)
        col = SEFIROT[sef].column
        if col == 'left': left += w
        elif col == 'right': right += w
        elif col == 'middle': middle += w

    denom = max(1, len(board))
    left /= denom; right /= denom; middle /= denom

    opposition_penalty = max(0.0, abs(left - right) - 0.15) * 0.5
    central_bonus = middle * 0.4

    score = base + central_bonus - opposition_penalty
    if street == 'river':
        score += 0.05  # Da'at revela

    return max(0.0, min(1.0, score))
