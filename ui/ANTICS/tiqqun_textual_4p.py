
# ui/tiqqun_textual_4p.py
# Textual TUI prototype (needs: pip install textual rich)
# 4 players: West(P1), North(P2), East(P3), South-HERO(P4)
# Panels per player: Position (BTN/SB/BB/None) + Action (bet/raise/call/fold/allin) + amount
# Center: 5 inputs for community cards (F1 F2 F3 T R) + 2 for HERO cards (H1 H2)
# Bottom: Recompute button -> shows recommendation from TIQQUN engine

from typing import Dict, List
from dataclasses import dataclass
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Button, Input, Static, Label, RadioSet, RadioButton
from textual.reactive import reactive

# Reuse TIQQUN engine
from modules.parser import STATE as PSTATE
from modules.logic import tech_eval
from modules.simbolic import flow_score
from modules.motor import fuse_scores

@dataclass
class PlayerState:
    name: str
    pos: str = "None"   # "BTN","SB","BB","None"
    bet: float = 0.0
    folded: bool = False

class PlayerPanel(Static):
    """A small panel with position radios and action buttons for one player."""
    def __init__(self, pid: int, label: str) -> None:
        super().__init__(classes="card")
        self.pid = pid
        self.label = label
        self.bet_input = Input(placeholder="import (€)", id=f"bet{pid}")
        self.info = Label("—", id=f"info{pid}")
        self.radios = RadioSet(
            RadioButton("None", value=True, id=f"posNone{pid}"),
            RadioButton("BTN", id=f"posBTN{pid}"),
            RadioButton("SB", id=f"posSB{pid}"),
            RadioButton("BB", id=f"posBB{pid}"),
            id=f"pos{pid}",
        )

    def compose(self) -> ComposeResult:
        yield Label(self.label, classes="title")
        yield self.radios
        with Horizontal():
            yield Button("Bet", id=f"betBtn{self.pid}")
            yield Button("Raise", id=f"raiseBtn{self.pid}")
            yield Button("Call", id=f"callBtn{self.pid}")
        with Horizontal():
            yield Button("Fold", id=f"foldBtn{self.pid}")
            yield Button("All-in", id=f"allinBtn{self.pid}")
        yield self.bet_input
        yield self.info

class BoardPanel(Static):
    """Center board + hero cards."""
    def __init__(self) -> None:
        super().__init__(classes="card")
        self.f1 = Input(placeholder="F1", id="F1"); self.f2 = Input(placeholder="F2", id="F2"); self.f3 = Input(placeholder="F3", id="F3")
        self.t  = Input(placeholder="T", id="T");    self.r  = Input(placeholder="R", id="R")
        self.h1 = Input(placeholder="H1", id="H1");  self.h2 = Input(placeholder="H2", id="H2")
        self.info = Label("", id="boardinfo")

    def compose(self) -> ComposeResult:
        yield Label("Board i HERO", classes="title")
        with Grid(classes="grid5"):
            yield self.f1; yield self.f2; yield self.f3; yield self.t; yield self.r
        with Horizontal():
            yield Label("HERO:"); yield self.h1; yield self.h2
        yield self.info

class RecPanel(Static):
    rec_text = reactive("RECOM —")
    def compose(self) -> ComposeResult:
        yield Label(self.rec_text, id="reclabel")

class TIQQUNTextual(App):
    CSS = """
    Screen { layout: vertical; }
    .row { height: auto; }
    .card { border: round $accent; padding: 1; margin: 1; }
    .title { content-align: center middle; text-style: bold; color: $text; }
    .grid5 { grid-size: 5; grid-gutter: 1 1; }
    #reclabel { text-style: bold; }
    """
    BINDINGS = [("q","quit","Sortir"), ("r","recompute","Recalcular")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(classes="row"):
            self.p1 = PlayerPanel(1, "P1 Oest")
            self.p2 = PlayerPanel(2, "P2 Nord")
            self.p3 = PlayerPanel(3, "P3 Est")
            self.p4 = PlayerPanel(4, "P4 HERO (Sud)")
            yield self.p1; yield self.p2; yield self.p3; yield self.p4
        with Horizontal(classes="row"):
            self.board = BoardPanel()
            yield self.board
        with Horizontal(classes="row"):
            self.recompute_btn = Button("Recompute", id="recompute")
            self.rec = RecPanel()
            yield self.recompute_btn
            yield self.rec
        yield Footer()

        # Internal state
        self.players: Dict[int, PlayerState] = {
            1: PlayerState("P1"), 2: PlayerState("P2"), 3: PlayerState("P3"), 4: PlayerState("HERO"),
        }
        self.hero_seat = 4  # South

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        pid = None
        for i in range(1,5):
            if bid.endswith(str(i)):
                pid = i
        if pid is None:
            if bid == "recompute":
                self.action_recompute()
            return

        panel = getattr(self, f"p{pid}")
        state = self.players[pid]

        # detect selected pos
        pos_value = "None"
        for name in ("BTN","SB","BB","None"):
            rb = panel.query_one(f"#pos{name}{pid}", RadioButton)
            if rb.value:
                pos_value = name
        state.pos = pos_value

        # button action types
        if bid.startswith("betBtn"):
            amt = self._read_amount(panel)
            state.bet += amt if amt>0 else 1.0
            panel.info.update(f"{state.pos} | bet={state.bet:.2f}")
        elif bid.startswith("raiseBtn"):
            amt = self._read_amount(panel)
            state.bet += max(amt, 1.0)
            panel.info.update(f"{state.pos} | raise->{state.bet:.2f}")
        elif bid.startswith("callBtn"):
            max_bet = max(p.bet for p in self.players.values())
            state.bet = max_bet
            panel.info.update(f"{state.pos} | call={state.bet:.2f}")
        elif bid.startswith("foldBtn"):
            state.folded = True
            panel.info.update(f"{state.pos} | FOLD")
        elif bid.startswith("allinBtn"):
            amt = self._read_amount(panel)
            state.bet += max(amt, 1.0)*5
            panel.info.update(f"{state.pos} | ALLIN={state.bet:.2f}")

    def _read_amount(self, panel: 'PlayerPanel') -> float:
        try:
            val = float(panel.bet_input.value.strip())
            return max(0.0, val)
        except:
            return 0.0

    def action_recompute(self) -> None:
        # build engine state
        players = 4
        bb = 1.0
        PSTATE['players']=players
        PSTATE['bb']=bb
        PSTATE['board']=self._board_cards()
    if len(PSTATE['board']) == 0:
        PSTATE['street'] = 'preflop'
    elif len(PSTATE['board']) == 3:
        PSTATE['street'] = 'flop'
    elif len(PSTATE['board']) == 4:
        PSTATE['street'] = 'turn'
    else:
        PSTATE['street'] = 'river'

        # hero cards
        hero_cards = []
        if self.board.h1.value.strip(): hero_cards.append(self.board.h1.value.strip())
        if self.board.h2.value.strip(): hero_cards.append(self.board.h2.value.strip())
        PSTATE['hero_cards']=hero_cards

        # pot and to_call
        pot = sum(p.bet for p in self.players.values())
        hero_bet = self.players[4].bet
        max_bet = max(p.bet for p in self.players.values())
        to_call = max(0.0, max_bet - hero_bet)
        PSTATE['pot']=pot
        PSTATE['to_call_hero']=to_call
        PSTATE['hero_seat']=4

        tech = tech_eval(PSTATE['hero_cards'], PSTATE['board'], PSTATE['players'], PSTATE['pot'], PSTATE['to_call_hero'], PSTATE['hero_seat'])
        flow = flow_score(PSTATE['hero_cards'], PSTATE['street'], PSTATE['board'])
        out = fuse_scores(tech, flow)

        self.query_one("#reclabel", Label).update(f"RECOM {out.decision} | conf={out.conf_final:.2f} | p_win={out.tech.p_win:.2f} | ev={out.tech.ev_hint:.2f} | flow={out.flow:.2f}")

    def _board_cards(self) -> List[str]:
        cards = []
        f1 = self.board.f1.value.strip(); f2 = self.board.f2.value.strip(); f3 = self.board.f3.value.strip()
        t  = self.board.t.value.strip();  r  = self.board.r.value.strip()
        if f1 and f2 and f3: cards += [f1, f2, f3]
        if t: cards.append(t)
        if r: cards.append(r)
        return cards

if __name__ == "__main__":
    TIQQUNTextual().run()
