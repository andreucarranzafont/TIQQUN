from modules import parser

lines = [
"NEW T=6 BB=100 STACK=100 HERO=6c 7s",
"SEATS _ _ _ _ _ H",
"A p3 f",
"A p4 r 210",
"A p5 f",
"A p6 f",
"A p1 c",
"A p2 f",
"F 7d 5h 9d",
"A p1 c",
"A p4 c",
"T 7c",
"A p1 c",
"A p4 c",
"R Qh",
"A p1 r 230",
"A p4 f",
"END"
]

for ln in lines:
    out = parser.parse_line(ln)
    if out:
        print(ln)
        print("→", out)
