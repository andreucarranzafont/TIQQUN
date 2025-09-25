
# modules/ranges.py
import json
from pathlib import Path
from typing import List
from .equity import expand_range

class PreflopRanges:
    def __init__(self, path: str = "data/refs/preflop_ranges.json"):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def combos_for(self, position: str, action: str = "open") -> List[List[str]]:
        masks = self.data.get(position, {}).get(action, [])
        combos = []
        for m in masks:
            combos += expand_range(m)
        return combos
