from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Button
from textual.containers import Horizontal, Vertical

PLAYERS = ["MrBlue","MrBlonde","MrWhite","MrPink","MrBrown","Pluribus"]

class PlayerTable(DataTable):
    def on_mount(self):
        self.add_columns("Seat","Player","Stack","Bet","Cards","State")
        for i, p in enumerate(PLAYERS, start=1):
            self.add_row(str(i), p, "100.0", "0.0", "[], []", "OK")
        self.cursor_type = "row"
        self.focus()

class ActionBar(Static):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("Deal", id="deal", variant="primary")
            yield Button("Bet +1", id="bet1")
            yield Button("Fold", id="fold")
            yield Button("Next", id="next")
            yield Button("Reset", id="reset")
            yield Button("Quit (Q)", id="quit", variant="error")

class TiqqunTUI(App):
    CSS = '''
    Screen { layout: vertical; }
    .title { content-align: center middle; height: 3; }
    DataTable { height: 1fr; }
    '''
    BINDINGS = [("q","quit","Quit"),("d","deal","Deal"),("b","bet","Bet +1"),
                ("f","fold","Fold"),("n","next","Next")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("TIQQUN — Taula 6 jugadors (demo TUI)", classes="title")
        self.table = PlayerTable()
        yield self.table
        yield ActionBar()
        yield Footer()

    def _selected_row(self):
        if self.table.cursor_row is None: return None
        return self.table.cursor_row

    def action_quit(self):
        self.exit()

    def action_deal(self):
        # Marca cartes “repartides” de manera simbòlica
        for r in range(len(PLAYERS)):
            self.table.update_cell(r, 4, "[🂠, 🂠]")
        self.notify("Cards dealt (demo)")

    def action_bet(self):
        r = self._selected_row()
        if r is None: return
        # incrementa aposta +1 i baixa una mica l'stack
        bet = float(self.table.get_cell_at(r,3)) + 1.0
        stack = float(self.table.get_cell_at(r,2)) - 1.0
        self.table.update_cell(r,3, f"{bet:.1f}")
        self.table.update_cell(r,2, f"{stack:.1f}")

    def action_fold(self):
        r = self._selected_row()
        if r is None: return
        self.table.update_cell(r,5,"FOLDED")

    def action_next(self):
        self.notify("Next street (demo)")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        m = event.button.id
        if m == "deal": self.action_deal()
        elif m == "bet1": self.action_bet()
        elif m == "fold": self.action_fold()
        elif m == "next": self.action_next()
        elif m == "reset":
            self.table.clear()
            self.table.on_mount()
        elif m == "quit": self.action_quit()

if __name__ == "__main__":
    TiqqunTUI().run()
