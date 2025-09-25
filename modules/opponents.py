
# modules/opponents.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class OpponentStats:
    hands: int = 0
    vpip: int = 0
    pfr: int = 0
    threebet: int = 0
    bets: int = 0
    raises: int = 0
    calls: int = 0
    checks: int = 0

    @property
    def VPIP(self):
        return self.vpip / self.hands if self.hands else 0.0

    @property
    def PFR(self):
        return self.pfr / self.hands if self.hands else 0.0

    @property
    def ThreeBet(self):
        return self.threebet / self.hands if self.hands else 0.0

    @property
    def AF(self):
        denom = self.calls + self.checks
        return (self.bets + self.raises) / denom if denom else 0.0

class OpponentsBook:
    def __init__(self, n_players: int = 8):
        self.players: Dict[str, OpponentStats] = {f"P{i}": OpponentStats() for i in range(1, n_players+1)}

    def note_preflop(self, pid: str, vpip: bool, pfr: bool, threebet: bool):
        st = self.players[pid]
        st.hands += 1
        st.vpip += int(vpip)
        st.pfr += int(pfr)
        st.threebet += int(threebet)

    def note_postflop(self, pid: str, action: str):
        st = self.players[pid]
        if action == 'bet': st.bets += 1
        elif action == 'raise': st.raises += 1
        elif action == 'call': st.calls += 1
        elif action == 'check': st.checks += 1
