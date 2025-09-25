# motor.py â€” TIQQUN PRO (decisor amb pot odds + SPR)
from dataclasses import dataclass
from typing import List, Literal, Optional
from .logic import TechEval

Decision = Literal['FOLD','CALL','RAISE','ALLIN']

@dataclass
class FusionOutput:
    conf_final: float
    decision: Decision
    tech: TechEval
    flow: float
    reasons: List[str]
    sizing: Optional[float] = None    # % del pot suggerit per a RAISE
    spr: Optional[float] = None
    breakeven_eq: Optional[float] = None

DEFAULT_WEIGHTS = {'tech': 0.7, 'flow': 0.3}

# -------------------------
# Funcions dâ€™ajuda
# -------------------------
def breakeven_equity(pot: float, to_call: float) -> float:
    """Equity necessÃ ria per a CALL (sense implied odds)."""
    if to_call <= 0: 
        return 0.0
    return to_call / (pot + to_call)

def suggest_sizing(spr: float, edge: float) -> float:
    """
    Retorna un % de pot per al raise:
    - SPR alt â†’ sizing mÃ©s petit; SPR baix â†’ sizing gran.
    - edge = p_win - BEQ (avantatge sobre el breakeven).
    """
    if spr <= 1.5:        # short SPR: pressionar
        return 100.0
    if spr <= 3.0:
        return 75.0 if edge > 0.06 else 60.0
    if spr <= 6.0:
        return 66.0 if edge > 0.05 else 50.0
    return 50.0 if edge > 0.05 else 33.0

# -------------------------
# Decisor nou (recomanat)
# -------------------------
def decide_action(
    tech: TechEval,
    flow: float,
    pot: float,
    to_call: float,
    spr: float,
    weights=DEFAULT_WEIGHTS
) -> FusionOutput:
    """
    DecisiÃ³ amb pot odds + SPR + fusiÃ³ tech/flow.
    MantÃ© la teva filosofia de 'confianÃ§a', perÃ² no permet CALLs amb equity
    per sota del breakeven.
    """
    # 1) confianÃ§a tÃ¨cnica (mateixa idea que tenies, lleu ajust)
    tech_conf = max(0.0, min(
        1.0,
        0.55*tech.p_win + 0.15*tech.p_improve + 0.20*((tech.ev_hint+1)/2) + 0.10*tech.position_score
    ))
    conf = weights['tech']*tech_conf + weights['flow']*flow

    # 2) pot odds
    beq = breakeven_equity(pot, to_call)
    edge = tech.p_win - beq

    # 3) regles durs + polÃ­tica per SPR
    decision: Decision
    sizing: Optional[float] = None

    # Si no cal pagar res, pots optar per 'RAISE' segons confianÃ§a
    if to_call <= 1e-9:
        if conf >= 0.80 and tech.p_win >= 0.55:
            decision = 'RAISE'
            sizing = suggest_sizing(spr, edge)
        else:
            decision = 'CALL'  # check/back
        return FusionOutput(conf, decision, tech, flow, _reasons(tech_conf, flow, tech, conf, beq, edge, spr), sizing, spr, beq)

    # No fem CALL si p_win < BEQ (sense implied odds considerades aquÃ­)
    if tech.p_win < beq - 0.01:
        decision = 'FOLD'
        return FusionOutput(conf, decision, tech, flow, _reasons(tech_conf, flow, tech, conf, beq, edge, spr), sizing, spr, beq)

    # Quan tenim edge suficient, decidim entre CALL/RAISE/ALLIN segons SPR
    if spr <= 1.5:
        # Short SPR: si p_win >= 0.52 i confianÃ§a alta -> ALLIN, si no RAISE
        if conf >= 0.80 and tech.p_win >= max(0.52, beq + 0.03):
            decision = 'ALLIN'
        else:
            decision = 'RAISE'
            sizing = 100.0
    elif spr <= 3.0:
        if conf >= 0.78 and edge >= 0.05:
            decision = 'RAISE'
            sizing = suggest_sizing(spr, edge)
        else:
            decision = 'CALL'
    elif spr <= 6.0:
        if conf >= 0.82 and edge >= 0.06:
            decision = 'RAISE'
            sizing = suggest_sizing(spr, edge)
        else:
            decision = 'CALL'
    else:  # spr alt
        if conf >= 0.86 and edge >= 0.07:
            decision = 'RAISE'
            sizing = suggest_sizing(spr, edge)
        else:
            decision = 'CALL'

    return FusionOutput(conf, decision, tech, flow, _reasons(tech_conf, flow, tech, conf, beq, edge, spr), sizing, spr, beq)

def _reasons(tech_conf: float, flow: float, tech: TechEval, conf: float, beq: float, edge: float, spr: float) -> List[str]:
    return [
        f"conf={conf:.2f}",
        f"tech_conf={tech_conf:.2f}",
        f"flow={flow:.2f}",
        f"p_win={tech.p_win:.3f}",
        f"BEQ={beq:.3f}",
        f"edge={edge:.3f}",
        f"p_improve={tech.p_improve:.2f}",
        f"ev_hint={tech.ev_hint:.2f}",
        f"position={tech.position_score:.2f}",
        f"SPR={spr:.2f}",
    ]

# -------------------------
# Compatibilitat: versiÃ³ antiga
# -------------------------
def fuse_scores(tech: TechEval, flow: float, weights=DEFAULT_WEIGHTS) -> FusionOutput:
    """
    VersiÃ³ original (compatibilitat). Mantinc la teva lÃ²gica perÃ² sense pot odds/SPR.
    Recomanat migrar a decide_action(...).
    """
    tech_conf = max(0.0, min(1.0, 0.5*tech.p_win + 0.2*tech.p_improve + 0.2*((tech.ev_hint+1)/2) + 0.1*tech.position_score))
    conf = weights['tech']*tech_conf + weights['flow']*flow

    if conf >= 0.90 and tech.ev_hint > 0.5:
        dec: Decision = 'ALLIN'
    elif conf >= 0.75:
        dec = 'RAISE'
    elif conf >= 0.58:
        dec = 'CALL'
    else:
        dec = 'FOLD'

    reasons = [
        f"tech_conf={tech_conf:.2f}",
        f"flow={flow:.2f}",
        f"p_win={tech.p_win:.2f}",
        f"p_improve={tech.p_improve:.2f}",
        f"ev_hint={tech.ev_hint:.2f}",
        f"position={tech.position_score:.2f}",
    ]
    return FusionOutput(conf, dec, tech, flow, reasons)

