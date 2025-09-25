from modules import parser

lines = [
"NEW T=6 BB=1.0 STACK=120 HERO=As Kd",
"SEATS H _ _ _ _ _",
"A p1 f",
"F 2c 7d Jh",
"END"
]

for ln in lines:
    out = parser.parse_line(ln)
    if out:
        print(ln)
        print("→", out)
