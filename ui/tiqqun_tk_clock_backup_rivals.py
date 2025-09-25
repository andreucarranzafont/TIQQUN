# -*- coding: utf-8 -*-
# TIQQUN TK Clock (versió amb projectes + logs + reset/end)
from typing import Dict, List
import os, csv, datetime as dt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb

# Core TIQQUN
from modules.parser import STATE as PSTATE
from modules.logic import tech_eval
from modules.simbolic import flow_score
from modules.motor import fuse_scores

POS_OPTS = ("None","SB","BB","BTN")
ACT_OPTS = ("", "bet", "call", "raise", "fold", "allin")

FONT       = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 11)

def ffloat(s: str) -> float:
    try:
        return max(0.0, float((s or "").replace(",", ".").strip()))
    except:
        return 0.0

def contributes(act: str, amt: float) -> float:
    return amt if act in ("bet","raise","call","allin") and amt > 0 else 0.0

class PlayerFrame(ttk.LabelFrame):
    def __init__(self, master, title: str, pid: int, hero: bool=False):
        super().__init__(master, text=title, padding=6)
        self.pid = pid
        self.hero = hero

        for c in range(10):
            self.grid_columnconfigure(c, weight=0)

        r = 0
        # Tag amb ample fix perquè "FOLD/SB/BB/BTN" sempre es vegi
        self.tag = ttk.Label(self, text="-", style="Tag.TLabel", width=6, anchor="center")
        self.tag.grid(row=r, column=0, sticky="w", padx=(0,6), pady=(0,2))

        self.active = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text="Actiu", variable=self.active, command=self._combo_confirm).grid(row=r, column=1, sticky="w", padx=(0,6))
        r += 1

        if hero:
            ttk.Label(self, text="H:", width=2).grid(row=r, column=0, sticky="w")
            self.h1 = ttk.Entry(self, width=5, font=FONT)
            self.h1.grid(row=r, column=1, padx=2, sticky="w")
            self.h2 = ttk.Entry(self, width=5, font=FONT)
            self.h2.grid(row=r, column=2, padx=2, sticky="w")
            r += 1

        ttk.Label(self, text="Pos").grid(row=r, column=0, sticky="w")
        self.pos = ttk.Combobox(self, values=POS_OPTS, state="readonly", width=5)
        self.pos.set("None")
        self.pos.grid(row=r, column=1, padx=(2,6), sticky="w")

        ttk.Label(self, text="Acció").grid(row=r, column=2, sticky="w")
        self.act = ttk.Combobox(self, values=ACT_OPTS, state="readonly", width=6)
        self.act.set("")
        self.act.grid(row=r, column=3, padx=(2,6), sticky="w")

        ttk.Label(self, text="Quant").grid(row=r, column=4, sticky="w")
        self.amt = ttk.Entry(self, width=6, font=FONT)
        self.amt.grid(row=r, column=5, padx=(2,6), sticky="w")
        r += 1

        self.btn_confirm = ttk.Button(self, text=f"Confirm P{pid}", command=self.confirm_and_recompute)
        self.btn_confirm.grid(row=r, column=0, columnspan=6, sticky="w")
        r += 1

        self.info = ttk.Label(self, text="-", font=FONT_SMALL, foreground="#9aa0a6")
        self.info.grid(row=r, column=0, columnspan=8, sticky="w", pady=(3,0))

        self.fields = [self.pos, self.act, self.amt]
        if hero:
            self.fields += [self.h1, self.h2]
        for w in self.fields:
            w.bind("<Return>", self._enter_confirm)
            w.bind("<KP_Enter>", self._enter_confirm)
        self.pos.bind("<<ComboboxSelected>>", self._combo_confirm)
        self.act.bind("<<ComboboxSelected>>", self._combo_confirm)

    def _enter_confirm(self, _=None):
        self.confirm_and_recompute()

    def _combo_confirm(self, _=None):
        self.confirm_and_recompute()

    def read(self) -> Dict:
        pos = self.pos.get()
        act = (self.act.get() or "").lower()
        amt = ffloat(self.amt.get())
        # línia d'info abreujada
        self.info.config(text=f"{'[X]' if self.active.get() else '[ ]'} {pos if pos!='None' else '-'} | {(act.upper() or '-') } {amt if amt>0 else '-'}")

        # Tag visible i consistent
        tag, style = "-", "Tag.TLabel"
        if act == "fold":
            tag, style = "FOLD", "TagFOLD.TLabel"
        elif pos == "BTN":
            tag, style = "BTN", "TagBTN.TLabel"
        elif pos == "SB":
            tag, style = "SB", "TagSB.TLabel"
        elif pos == "BB":
            tag, style = "BB", "TagBB.TLabel"
        self.tag.config(text=tag, style=style)

        out = {"pos": pos, "act": act, "amt": amt, "fold": act=="fold", "active": self.active.get()}
        if self.hero:
            out["H1"] = getattr(self, "h1", None).get().strip() if hasattr(self, "h1") else ""
            out["H2"] = getattr(self, "h2", None).get().strip() if hasattr(self, "h2") else ""
        return out

    def confirm_and_recompute(self):
        app: "App" = self.master.master
        app.recompute(context=f"P{self.pid}")

class BoardFrame(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Tauler", padding=8)
        for i in range(5):
            self.grid_columnconfigure(i, weight=1)
        self.f1 = ttk.Entry(self, width=10, font=FONT)
        self.f2 = ttk.Entry(self, width=10, font=FONT)
        self.f3 = ttk.Entry(self, width=10, font=FONT)
        self.t  = ttk.Entry(self, width=10, font=FONT)
        self.r  = ttk.Entry(self, width=10, font=FONT)
        for i, w in enumerate((self.f1, self.f2, self.f3, self.t, self.r)):
            w.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            w.bind("<Return>", self._enter_confirm)
            w.bind("<KP_Enter>", self._enter_confirm)
        ttk.Button(self, text="Confirm Board", command=self.confirm_and_recompute).grid(row=1, column=0, columnspan=5, pady=(8,2))
        self.fields = [self.f1, self.f2, self.f3, self.t, self.r]

    def _enter_confirm(self, _=None):
        self.confirm_and_recompute()

    def cards(self) -> List[str]:
        res = []
        f1, f2, f3, t, r = (e.get().strip() for e in (self.f1, self.f2, self.f3, self.t, self.r))
        if f1 and f2 and f3: res += [f1, f2, f3]
        if t: res.append(t)
        if r: res.append(r)
        return res

    def confirm_and_recompute(self):
        app: "App" = self.master.master
        app.recompute(context="BOARD")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TIQQUN — 9 jugadors (rellotge)")
        self.geometry("1380x860")
        self.configure(padx=6, pady=6)

        # Estils
        style = ttk.Style(self); style.theme_use("clam")
        style.configure(".", font=FONT)
        style.configure("TButton", font=FONT)
        style.configure("Tag.TLabel",   relief="ridge", padding=(6,2))
        style.configure("TagBTN.TLabel",background="#fdd663", padding=(6,2))
        style.configure("TagSB.TLabel", background="#8ab4f8", padding=(6,2))
        style.configure("TagBB.TLabel", background="#c58af9", padding=(6,2))
        style.configure("TagFOLD.TLabel", background="#9aa0a6", padding=(6,2))

        # Sessió + logs
        base = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.normpath(os.path.join(base, "..", "logs"))
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, "hands_log.csv")
        self.session = {"hands": 0, "wins": 0, "losses": 0, "splits": 0, "net": 0.0}
        self.hand_id = 1

        main = ttk.Frame(self); main.pack(fill="both", expand=True)

        # 7 columnes (centre = col 3)
        for c in range(7): main.grid_columnconfigure(c, weight=1)
        for r in range(4): main.grid_rowconfigure(r, weight=1)

        # ESQUERRA (de baix a dalt): P1, P2, P3
        self.p1 = PlayerFrame(main, "P1", 1); self.p1.grid(row=2, column=0, sticky="w",  padx=4, pady=4)
        self.p2 = PlayerFrame(main, "P2", 2); self.p2.grid(row=1, column=0, sticky="w",  padx=4, pady=4)
        self.p3 = PlayerFrame(main, "P3", 3); self.p3.grid(row=0, column=0, sticky="nw", padx=4, pady=4)

        # DALT CENTRE (P4/P5 centrats dins contenidor a columna 3)
        self.top_center = ttk.Frame(main)
        self.top_center.grid(row=0, column=3, sticky="n", padx=0, pady=4)
        self.top_center.grid_columnconfigure(0, weight=1)
        self.top_center.grid_columnconfigure(1, weight=1)
        self.p4 = PlayerFrame(self.top_center, "P4", 4); self.p4.grid(row=0, column=0, sticky="e", padx=(0, 6), pady=0)
        self.p5 = PlayerFrame(self.top_center, "P5", 5); self.p5.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=0)

        # DRETA (de dalt cap avall): P6, P7, P8
        self.p6 = PlayerFrame(main, "P6", 6); self.p6.grid(row=0, column=6, sticky="ne", padx=4, pady=4)
        self.p7 = PlayerFrame(main, "P7", 7); self.p7.grid(row=1, column=6, sticky="e",  padx=4, pady=4)
        self.p8 = PlayerFrame(main, "P8", 8); self.p8.grid(row=2, column=6, sticky="se", padx=4, pady=4)

        # TAULER centrat (col=2..4) just sobre HERO
        self.center = BoardFrame(main); self.center.grid(row=2, column=2, columnspan=3, sticky="s", padx=6, pady=(6,0))

        # HERO exactament al mig abaix (col 3)
        self.pH = PlayerFrame(main, "HERO", 4, hero=True); self.pH.grid(row=3, column=3, sticky="n", padx=6, pady=8)

        # Recomanació + Projectes + Sessió + Controls
        bottom = ttk.LabelFrame(self, text="Recomanació", padding=6); bottom.pack(fill="x", padx=6, pady=6)
        self.out = ttk.Label(bottom, text="RECOM —", font=FONT_MONO); self.out.pack(anchor="w")
        self.center_info = ttk.Label(bottom, text="Projectes —", font=FONT_SMALL, foreground="#0a8"); self.center_info.pack(anchor="w", pady=(4,0))
        self.session_lbl = ttk.Label(bottom, text="Sessió — mans:0 | wins:0 | losses:0 | net:0.00", font=FONT_SMALL); self.session_lbl.pack(anchor="w", pady=(2,0))

        ctrl = ttk.Frame(bottom); ctrl.pack(fill="x", pady=(6,0))
        ttk.Label(ctrl, text="Resultat:").pack(side="left")
        self.result_var = tk.StringVar(value="Win pot")
        ttk.Combobox(ctrl, textvariable=self.result_var, values=("Win pot","Lose","Split"), state="readonly", width=8).pack(side="left", padx=(4,8))
        ttk.Label(ctrl, text="Payout (€):").pack(side="left")
        self.result_net = ttk.Entry(ctrl, width=8, font=FONT); self.result_net.insert(0,"0"); self.result_net.pack(side="left", padx=(4,8))
        ttk.Button(ctrl, text="Registrar & Nova mà  [F9]", command=self.end_and_log).pack(side="left", padx=6)
        ttk.Button(ctrl, text="Nova mà (Reset)  [F5]",   command=self.reset_all).pack(side="left", padx=6)

        # Dreceres
        self.bind("<F5>", lambda e: self.reset_all())
        self.bind("<F9>", lambda e: self.end_and_log())

    def reset_all(self):
        frames = (self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8)
        for pf in frames:
            pf.pos.set("None")
            pf.act.set("")
            pf.amt.delete(0, "end")
            pf.active.set(True)
            pf.info.config(text="-")
            pf.tag.config(text="-", style="Tag.TLabel")
        for e in (self.center.f1, self.center.f2, self.center.f3, self.center.t, self.center.r):
            e.delete(0, "end")
        self.pH.pos.set("None"); self.pH.act.set(""); self.pH.amt.delete(0, "end"); self.pH.active.set(True); self.pH.tag.config(text="-", style="Tag.TLabel")
        if hasattr(self.pH, "h1"): self.pH.h1.delete(0, "end")
        if hasattr(self.pH, "h2"): self.pH.h2.delete(0, "end")
        self.out.config(text="RECOM —")
        self.center_info.config(text="Projectes —")
        self.result_var.set("Win pot"); self.result_net.delete(0,"end"); self.result_net.insert(0,"0")

    def recompute(self, context: str = ""):
        P1 = self.p1.read(); P2 = self.p2.read(); P3 = self.p3.read(); P4 = self.pH.read()
        P5 = self.p5.read(); P6 = self.p6.read(); P7 = self.p7.read(); P8 = self.p8.read()
        all_players = [P1, P2, P3, P4, P5, P6, P7, P8]
        active = [p for p in all_players if p.get("active", True)]

        pot = sum(contributes(p["act"], p["amt"]) for p in active)
        mx  = max([contributes(p["act"], p["amt"]) for p in active] + [0.0])
        hero = contributes(P4["act"], P4["amt"]) if P4.get("active", True) else 0.0
        to_call = max(0.0, mx - hero) if P4.get("active", True) else 0.0

        board = self.center.cards()
        hero_cards = [c for c in (P4.get("H1", ""), P4.get("H2", "")) if c]

        n_players = (1 if P4.get("active", True) else 0) + sum(1 for p in (P1, P2, P3, P5, P6, P7, P8) if p.get("active", True))
        if n_players < 2: n_players = 2

        PSTATE["players"] = n_players
        PSTATE["bb"] = 1.0
        PSTATE["board"] = board
        n = len(board)
        PSTATE["street"] = "preflop" if n == 0 else ("flop" if n == 3 else ("turn" if n == 4 else "river"))
        PSTATE["hero_cards"] = hero_cards
        PSTATE["pot"] = pot
        PSTATE["to_call_hero"] = to_call
        PSTATE["hero_seat"] = 4

        tech = tech_eval(PSTATE["hero_cards"], PSTATE["board"], n_players, PSTATE["pot"], PSTATE["to_call_hero"], PSTATE["hero_seat"])
        flow = flow_score(PSTATE["hero_cards"], PSTATE["street"], PSTATE["board"])
        out = fuse_scores(tech, flow)

        self.out.config(text=f"[{context}] RECOM {out.decision} | conf={out.conf_final:.2f} | "
                             f"p_win={out.tech.p_win:.2f} | ev={out.tech.ev_hint:.2f} | "
                             f"flow={out.flow:.2f} | pot={pot:.2f} | to_call={to_call:.2f}")
        # Projectes al centre
        self.update_projects_label(hero_cards, board)

    # ===== Helpers de projectes =====
    def _rank_val(self, c: str) -> int:
        if not c: return 0
        r = c[:-1].upper().replace("T","10")
        table = {"A":14,"K":13,"Q":12,"J":11}
        return table.get(r, int(r) if r.isdigit() else 0)

    def _suit(self, c: str) -> str:
        return c[-1:].upper() if c else ""

    def update_projects_label(self, hero: List[str], board: List[str]) -> None:
        cards = [x for x in hero + board if x]
        txt = []
        suits = {}
        for c in cards: suits[self._suit(c)] = suits.get(self._suit(c), 0) + 1
        maxs = max(suits.values()) if suits else 0
        if maxs >= 5: txt.append("Color fet")
        elif maxs == 4: txt.append("Flush draw")

        vals = sorted(set(self._rank_val(c) for c in cards))
        if 14 in vals: vals = sorted(set(vals + [1]))  # roda A-5
        found_oesd = False; found_gut = False
        for i in range(len(vals)):
            win = [v for v in vals if vals[i] <= v <= vals[i] + 4]
            if len(win) >= 5: 
                found_oesd = True; break
            if len(win) == 4:
                if win[-1] - win[0] == 3: found_oesd = True
                elif win[-1] - win[0] == 4: found_gut = True
        if found_oesd: txt.append("OESD")
        elif found_gut: txt.append("Gutshot")

        bvals = [self._rank_val(c) for c in board]
        if bvals:
            topb = max(bvals)
            hvals = [self._rank_val(c) for c in hero]
            if all(h > topb for h in hvals if h):
                txt.append("Overcards")

        self.center_info.config(text="Projectes — " + (", ".join(txt) if txt else "—"))

    def _update_session_label(self):
        s = self.session
        self.session_lbl.config(text=f"Sessió — mans:{s['hands']} | wins:{s['wins']} | losses:{s['losses']} | net:{s['net']:.2f}")

    def end_and_log(self):
        # actualitza estat
        self.recompute(context="END")
        pot   = float(PSTATE.get("pot", 0.0))
        board = " ".join(PSTATE.get("board", [])) or "-"
        hero  = " ".join(PSTATE.get("hero_cards", [])) or "-"
        recom = self.out.cget("text")
        outcome = self.result_var.get()
        net = 0.0
        try: net = ffloat(self.result_net.get())
        except: net = 0.0
        if outcome == "Win pot" and net == 0.0: net = pot
        if outcome == "Lose" and net > 0:      net = -abs(net)

        newfile = not os.path.exists(self.log_path)
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if newfile: w.writerow(["ts","hand_id","outcome","net","pot","hero","board","recom"])
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"),
                        self.hand_id, outcome, f"{net:.2f}", f"{pot:.2f}", hero, board, recom])

        self.session["hands"] += 1
        if outcome == "Win pot" and net > 0: self.session["wins"] += 1
        elif outcome == "Lose" and net < 0:  self.session["losses"] += 1
        else: self.session["splits"] += 1
        self.session["net"] += net
        self.hand_id += 1
        self._update_session_label()
        self.reset_all()

if __name__ == "__main__":
    App().mainloop()
