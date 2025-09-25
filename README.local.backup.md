
# TIQQUN — Prototip v0.1

Sistema de suport al pòquer amb fusió **simbòlica** i **tècnica** (heurística).

## Estructura

```
TIQQUN/
├── tiqqun_cli.py                # CLI per provar el sistema
├── modules/
│   ├── simbolic.py              # Sefirots, senders i 'flow' simbòlic
│   ├── logic.py                 # Heurístiques tècniques (p_win, EV, posició)
│   ├── motor.py                 # Fusió (ponderació) i decisió final
│   └── parser.py                # Parser d'ordres (NEW/SEATS/BB/A/F/T/R/END)
├── moduls/
│   ├── modul_T9.py              # Paràmetres específics per 9 jugadors
│   ├── modul_T6.py
│   ├── modul_T5.py
│   ├── modul_T4.py
│   └── modul_T3.py
├── tests/
│   └── demo_session.txt         # Sessió de prova
├── registre/                    # (es guardarà més endavant)
├── docs/                        # (els teus .docx)
└── logs/                        # (sortides/errors)
```

## Ús ràpid

1) Obre terminal dins `TIQQUN/` i executa:
```bash
python tiqqun_cli.py
```
2) Prova enganxant línies de `tests/demo_session.txt` una a una.

Cada pas veuràs **REF** (mapa d'acció) o **RECOM** (decisió i confiança).

> Nota: Les probabilitats actuals són heurístiques molt simples (placeholder).
