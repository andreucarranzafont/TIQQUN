
from modules.parser import parse_line

def main():
    print("TIQQUN CLI v0 — escriu comandes (NEW/SEATS/BTN/SB/BB/A/F/T/R/END). CTRL+C per sortir.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAdeu!")
            break
        if not line:
            continue
        try:
            out = parse_line(line)
        except Exception as e:
            out = f"ERR: {type(e).__name__}: {e}"
        if out:
            print(out)

if __name__ == "__main__":
    main()
