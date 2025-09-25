# -*- coding: utf-8 -*-
# ui/tiqqun_textual_4p_round.py
# Compact Textual UI with a round ASCII poker table in the center
# Requires: pip install textual rich

from typing import Dict, List
from dataclasses import dataclass
import math

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Grid
from textual.widgets import Header, Footer, Button, Input, Static, Label, RadioSet, RadioButton

# TIQQUN core
from modules.parser import STATE as PSTATE
from modules.logic import tech_eval
from modules.simbolic import flow_score
from modules.motor import fuse_scores

# ... (segueix amb tot el codi que et vaig passar abans)
if __name__ == "__main__":
    TIQQUNRoundApp().run()
