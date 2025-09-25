from modules import parser

lines = [
    "NEW T=6 BB=1.0 STACK=120 HERO=As Kd",
    "SEATS _ _ H _ _ _",
    "F 2c 7d Jh",
    "A V b 3",
    "T Qh",
    "A V c",
    "R 2h",
    "END"
]

for ln in lines:
    out = parser.parse_line(ln)
    if out:
        print(out)
