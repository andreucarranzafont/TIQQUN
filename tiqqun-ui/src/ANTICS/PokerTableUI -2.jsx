// src/PokerTableUI.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";

/* ============ Utils cartes ============ */
const SUIT = { p: "♠", c: "♥", d: "♦", t: "♣" }; // piques, cors, diamants, trèvols
const RANKS = "23456789TJQKA";
const RVAL = Object.fromEntries([...RANKS].map((r, i) => [r, i + 2]));

function parseCardToken(tok) {
  if (!tok) return null;
  tok = tok.trim().toLowerCase().replaceAll("10", "t");
  const r = tok[0]?.toUpperCase();
  const s = tok[1];
  if (!RANKS.includes(r) || !SUIT[s]) return null;
  return { rank: r, suit: SUIT[s], asText: r + SUIT[s] };
}
function parseCardsLine(line, max) {
  if (!line) return [];
  const tokens = line
    .replaceAll(",", " ")
    .split(/\s+/)
    .map((t) => parseCardToken(t))
    .filter(Boolean);
  if (max) return tokens.slice(0, max);
  return tokens;
}
function asText(cards) {
  return cards.map((c) => c.asText);
}
function sameSuitCount(cards, targetSuit) {
  return cards.filter((c) => c && c.suit === targetSuit).length;
}
function boardStreet(board) {
  if (!board) return "PREFLOP";
  const n = board.length;
  if (n < 3) return "PREFLOP";
  if (n === 3) return "FLOP";
  if (n === 4) return "TURN";
  return "RIVER";
}

/* Senzillíssim: tiers preflop */
function heroTier(hero) {
  if (hero.length < 2) return 5;
  const [a, b] = hero;
  const pair = a.rank === b.rank;
  const suited = a.suit === b.suit;
  const hi = [a.rank, b.rank].map((r) => RVAL[r]).sort((x, y) => y - x);

  const asStr = (r1, r2, s) => r1 + r2 + (s ? "s" : "o");
  const key = asStr(a.rank, b.rank, suited) + "|" + asStr(b.rank, a.rank, suited);

  // Tier 1 – premium
  if (pair && ["A", "K", "Q", "J"].includes(a.rank)) return 1;
  if ((a.rank === "A" && b.rank === "K") || (a.rank === "K" && b.rank === "A")) return suited ? 1 : 2;

  // Tier 2
  if (pair && ["T"].includes(a.rank)) return 2;
  if (["A", "K", "Q", "J", "T"].includes(a.rank) && ["A", "K", "Q", "J", "T"].includes(b.rank)) {
    if (suited && (a.rank === "Q" || a.rank === "J")) return 2;
  }

  // Tier 3 (mitjanes i broadways)
  if (pair && ["9", "8", "7"].includes(a.rank)) return 3;
  if (suited && (a.rank === "A" || b.rank === "A")) return 3;

  // Tier 4
  if (pair) return 4;
  if (suited && hi[0] >= RVAL["9"]) return 4;

  // Tier 5
  return 5;
}

/* Detecció bàsica al flop/turn */
function hasPair(hero, board) {
  if (hero.length < 2 || board.length < 3) return false;
  const ranks = new Set(board.map((c) => c.rank));
  return hero.some((c) => ranks.has(c.rank));
}
function hasTopPair(hero, board) {
  if (hero.length < 2 || board.length < 3) return false;
  const top = board.map((c) => RVAL[c.rank]).sort((a, b) => b - a)[0];
  return hero.some((c) => RVAL[c.rank] === top);
}
function flushDraw(hero, board) {
  if (!board?.length || hero.length < 2) return false;
  const suits = ["♠", "♥", "♦", "♣"];
  return suits.some((s) => sameSuitCount([...hero, ...board], s) === 4);
}

/* ============ Estat i UI ============ */

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
function makePlayers(n) {
  const arr = [];
  for (let i = 0; i < n; i++) {
    arr.push({
      id: i + 1,
      name: i === 0 ? "USUARI" : `Jugador ${LETTERS[i] || i + 1}`,
      stack: 100.0,
      bet: 0,
      active: true,
      mx: null,
      my: null,
    });
  }
  return arr;
}

const ROLE_CYCLE = ["", "BTN", "SB", "BB"];
const ACTION_CYCLE = ["", "Check/Call", "Bet/Raise", "Fold"];

export default function PokerTableUI() {
  const [numPlayers, setNumPlayers] = useState(6);
  const [layout, setLayout] = useState("manual"); // 'auto' | 'manual'
  const [snap, setSnap] = useState(true);
  const [radius, setRadius] = useState(240);
  const [scale, setScale] = useState(0.95);

  const [players, setPlayers] = useState(() => makePlayers(6));
  const [roles, setRoles] = useState({});
  const [actions, setActions] = useState({});
  const [amounts, setAmounts] = useState({});
  const [boardLine, setBoardLine] = useState("");
  const [heroLine, setHeroLine] = useState("");
  const [board, setBoard] = useState([]);
  const [heroCards, setHeroCards] = useState([]);
  const [reco, setReco] = useState("Obre 2.2BB si s’escau");

  const arenaRef = useRef(null);
  const dragging = useRef(null);

  // actualitza # jugadors conservant estat
  useEffect(() => {
    setPlayers((prev) => {
      const want = makePlayers(numPlayers);
      const byId = Object.fromEntries(prev.map((p) => [p.id, p]));
      return want.map((w) => (byId[w.id] ? { ...w, ...byId[w.id] } : w));
    });
  }, [numPlayers]);

  // auto posicions (USUARI a 6h)
  const autoPositions = useMemo(() => {
    const total = numPlayers;
    const base = 270;
    return players.map((p, i) => {
      const ang = base + (360 / total) * i;
      const a = (ang * Math.PI) / 180;
      return { id: p.id, x: Math.cos(a) * radius, y: Math.sin(a) * radius };
    });
  }, [players, radius, numPlayers]);

  const pos = useMemo(() => {
    const map = new Map();
    players.forEach((p, i) => {
      if (p.mx != null && p.my != null) map.set(p.id, { x: p.mx, y: p.my });
      else map.set(p.id, autoPositions[i]);
    });
    return map;
  }, [players, autoPositions]);

  const pot = useMemo(
    () => players.reduce((s, p) => s + (p.bet || 0), 0),
    [players]
  );
  const street = boardStreet(board);

  /* ───── Recomanació (motor bàsic) ───── */
  useEffect(() => {
    const hero = players.find((p) => p.id === 1);
    if (!hero) return;

    const toCall = Math.max(0, Math.max(...players.map((p) => p.bet || 0)) - (hero.bet || 0));
    const active = players.filter((p) => p.active).length || 1;
    const tier = heroTier(heroCards);

    let msg = "";

    if (street === "PREFLOP") {
      if (toCall === 0) {
        // First in pot: open segons bucket i posició
        const myRole = roles[1] || "";
        const posFactor =
          myRole === "BTN" ? 2.2 : myRole === "SB" || myRole === "BB" ? 2.5 : 2.3;

        if (tier <= 2) msg = `OBRE ${posFactor.toFixed(1)}BB`;
        else if (tier === 3) msg = myRole === "BTN" || myRole === "CO" ? `OBRE 2.2BB` : `Open tight o FOLD`;
        else msg = `FOLD preflop (sense acció prèvia)`;
      } else {
        // facing raise
        if (tier <= 2) {
          const threeBet = Math.max(7, toCall * 3).toFixed(1);
          msg = `3-BET a ${threeBet} BB (o All-in si < 25BB)`;
        } else if (tier === 3) {
          msg = `CALL ${toCall.toFixed(2)} o 3-bet petit vs tardana`;
        } else {
          msg = `FOLD vs puja (${toCall.toFixed(2)} per pagar)`;
        }
      }
    } else {
      // postflop
      const pair = hasPair(heroCards, board);
      const top = hasTopPair(heroCards, board);
      const fd = flushDraw(heroCards, board);

      const anyBet =
        Math.max(...players.map((p) => p.bet || 0)) >
        (hero.bet || 0);

      if (!anyBet) {
        if (top || fd) msg = `CBET 33% del pot`;
        else msg = `Check (controla pot)`;
      } else {
        if (top || fd) msg = `CALL (${toCall.toFixed(2)}) o puja petit`;
        else msg = `FOLD (${toCall.toFixed(2)} per pagar)`;
      }
    }

    setReco(msg || "Obre 2.2BB si s’escau");
  }, [players, roles, board, heroCards, street]);

  /* ───── Handlers ───── */
  function cycleRole(id) {
    setRoles((r) => {
      const cur = r[id] || "";
      const next =
        ROLE_CYCLE[(ROLE_CYCLE.indexOf(cur) + 1) % ROLE_CYCLE.length];
      return { ...r, [id]: next };
    });
  }
  function cycleAction(id) {
    setActions((a) => {
      const cur = a[id] || "";
      const next =
        ACTION_CYCLE[(ACTION_CYCLE.indexOf(cur) + 1) % ACTION_CYCLE.length];
      return { ...a, [id]: next };
    });
  }
  function toggleActive(id) {
    setPlayers((ps) =>
      ps.map((p) => (p.id === id ? { ...p, active: !p.active } : p))
    );
  }
  function confirmAction(id) {
    const p = players.find((x) => x.id === id);
    const act = actions[id] || "";
    const amt = Number((amounts[id] || "0").toString().replace(",", "."));
    if (!p) return;

    if (act === "Bet/Raise" && amt > 0) {
      setPlayers((ps) =>
        ps.map((x) =>
          x.id === id
            ? { ...x, bet: (x.bet || 0) + amt, stack: Math.max(0, (x.stack || 0) - amt) }
            : x
        )
      );
      setAmounts((m) => ({ ...m, [id]: "" }));
    } else if (act === "Fold") {
      setPlayers((ps) => ps.map((x) => (x.id === id ? { ...x, active: false } : x)));
    }
  }
  function onApplyCards() {
    setBoard(parseCardsLine(boardLine, 5));
    setHeroCards(parseCardsLine(heroLine, 2));
  }
  function newHand() {
    setBoardLine(""); setHeroLine(""); setBoard([]); setHeroCards([]);
    setPlayers((ps) => ps.map((p) => ({ ...p, bet: 0, active: true })));
    setActions({}); setAmounts({});
  }

  /* Drag manual */
  function beginDrag(e, id) {
    if (layout !== "manual") return;
    const rect = arenaRef.current.getBoundingClientRect();
    const cx = rect.width / 2, cy = rect.height / 2;
    const startX = e.clientX - rect.left - cx;
    const startY = e.clientY - rect.top - cy;
    const p = pos.get(id) || { x: 0, y: 0 };
    dragging.current = { id, offX: startX - p.x, offY: startY - p.y };
    window.addEventListener("mousemove", onDrag);
    window.addEventListener("mouseup", endDrag);
  }
  function onDrag(e) {
    const d = dragging.current;
    if (!d) return;
    const rect = arenaRef.current.getBoundingClientRect();
    const cx = rect.width / 2, cy = rect.height / 2;
    const px = e.clientX - rect.left - cx - d.offX;
    const py = e.clientY - rect.top - cy - d.offY;
    setPlayers((ps) => ps.map((p) => (p.id === d.id ? { ...p, mx: px, my: py } : p)));
  }
  function endDrag() {
    const d = dragging.current;
    dragging.current = null;
    window.removeEventListener("mousemove", onDrag);
    window.removeEventListener("mouseup", endDrag);
    if (!d || !snap) return;
    // projecta al cercle
    setPlayers((ps) =>
      ps.map((p) => {
        if (p.id !== d.id) return p;
        const ang = Math.atan2(p.my || 0, p.mx || 0);
        return { ...p, mx: Math.cos(ang) * radius, my: Math.sin(ang) * radius };
      })
    );
  }

  /* ───── Render ───── */
  return (
    <div className="w-full h-screen text-white">
      {/* barres */}
      <div className="fixed top-0 left-0 right-0 z-20 bg-black/60 backdrop-blur px-3 py-2 flex items-center gap-3">
        <label className="flex items-center gap-1">
          Jugadors:
          <select className="bg-white text-black rounded px-2 py-1" value={numPlayers}
            onChange={(e) => setNumPlayers(Number(e.target.value))}>
            {Array.from({ length: 8 }, (_, i) => i + 2).map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-1">
          Disposició:
          <select className="bg-white text-black rounded px-2 py-1" value={layout}
            onChange={(e) => setLayout(e.target.value)}>
            <option value="auto">Auto (equidistant)</option>
            <option value="manual">Manual (arrossegar)</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={snap} onChange={(e) => setSnap(e.target.checked)} />
          Snap al cercle
        </label>
        <div className="flex items-center gap-2">
          Radi jugadors
          <input type="range" min="160" max="360" value={radius}
            onChange={(e) => setRadius(Number(e.target.value))} />
        </div>
        <div className="ml-auto flex items-center gap-2">
          Pot: <span className="font-bold">{pot.toFixed(2)}</span>
          <div className="flex items-center gap-2">
            Escala
            <input type="range" min="0.7" max="1.2" step="0.01" value={scale}
              onChange={(e) => setScale(Number(e.target.value))} />
          </div>
        </div>
      </div>

      {/* taula i jugadors */}
      <div className="pt-12 h-full">
        <div ref={arenaRef} className="relative mx-auto"
          style={{ width: "100%", height: "calc(100vh - 230px)", transform: `scale(${scale})`, transformOrigin: "top center" }}>
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-900 to-emerald-950" />
          <div className="absolute left-1/2 top-1/2 rounded-full border-4 border-amber-500/90"
               style={{ width: radius * 2, height: radius * 2, transform: "translate(-50%, -50%)" }} />
          {/* board */}
          <div className="absolute left-1/2 top-1/2 flex gap-3" style={{ transform: "translate(-50%, -50%)" }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="w-12 h-16 rounded-xl border border-white/30 bg-white/10 backdrop-blur-sm flex items-center justify-center text-white/90 text-sm shadow">
                {board[i]?.asText || "?"}
              </div>
            ))}
          </div>
          {/* players */}
          {players.map((p, idx) => {
            const a = pos.get(p.id) || { x: 0, y: 0 };
            return (
              <div key={p.id} className="absolute"
                   style={{ left: `calc(50% + ${a.x}px)`, top: `calc(50% + ${a.y}px)`, transform: "translate(-50%, -50%)" }}>
                <PlayerCard
                  p={p}
                  hero={idx === 0}
                  role={roles[p.id] || ""}
                  action={actions[p.id] || ""}
                  amount={amounts[p.id] || ""}
                  heroCards={idx === 0 ? asText(heroCards) : []}
                  onMouseDown={(e) => beginDrag(e, p.id)}
                  onCycleRole={() => cycleRole(p.id)}
                  onCycleAction={() => cycleAction(p.id)}
                  onAmount={(v) => setAmounts((m) => ({ ...m, [p.id]: v }))}
                  onConfirm={() => confirmAction(p.id)}
                  onSitout={() => toggleActive(p.id)}
                />
              </div>
            );
          })}
        </div>

        {/* recomanació i entrades ràpides */}
        <div className="fixed left-0 right-0 bottom-0 z-20 bg-black/70 backdrop-blur">
          <div className="max-w-6xl mx-auto px-3 py-2">
            <div className="text-emerald-300 text-sm font-semibold">QUÈ FER ARA</div>
            <div className="text-2xl md:text-3xl font-extrabold tracking-wide">{reco}</div>

            <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
              <div className="flex items-center gap-2">
                <span className="shrink-0">Tauler (flop/turn/river):</span>
                <input className="bg-white text-black rounded px-2 py-1 w-full"
                       placeholder="ex: Ap 8p Qd Kc 2t"
                       value={boardLine}
                       onChange={(e) => setBoardLine(e.target.value)} />
              </div>
              <div className="flex items-center gap-2">
                <span className="shrink-0">Cartes USUARI:</span>
                <input className="bg-white text-black rounded px-2 py-1 w-full"
                       placeholder="ex: Ah Qs"
                       value={heroLine}
                       onChange={(e) => setHeroLine(e.target.value)} />
              </div>
              <div className="flex gap-2">
                <button className="bg-blue-600 hover:bg-blue-700 text-white rounded px-3 py-1" onClick={onApplyCards}>Aplicar</button>
                <button className="bg-emerald-600 hover:bg-emerald-700 text-white rounded px-3 py-1" onClick={newHand}>Nova mà</button>
              </div>
            </div>

            <div className="mt-2 text-xs opacity-70">
              Escriviu cartes com <code>Ap</code>, <code>Qc</code>, <code>7d</code>, <code>2t</code>. Pals: p=♠, c=♥, d=♦, t=♣.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* -------- Targeta jugador -------- */
function PlayerCard({
  p, hero, role, action, amount, heroCards,
  onMouseDown, onCycleRole, onCycleAction, onAmount, onConfirm, onSitout,
}) {
  return (
    <div onMouseDown={onMouseDown}
      className={`select-none w-[220px] ${hero ? "ring-2 ring-amber-400" : ""} rounded-xl bg-black/60 backdrop-blur border border-white/10 shadow-md p-3`}>
      <div className="flex items-center justify-between">
        <div className="font-semibold">{hero ? "USUARI" : p.name}</div>
        {!!role && <span className="text-xs bg-yellow-500 text-black rounded px-1.5 py-0.5">{role}</span>}
      </div>
      <div className="text-xs opacity-80 mt-1">
        Pila: {(p.stack || 0).toFixed(2)} | Aposta: {(p.bet || 0).toFixed(2)}
      </div>
      {hero && (
        <div className="mt-2 flex gap-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="w-8 h-12 rounded-md border border-white/30 bg-white/10 flex items-center justify-center text-white/90 text-xs">
              {heroCards[i] || "?"}
            </div>
          ))}
        </div>
      )}

      <div className="mt-2 flex items-center gap-2">
        <button className="bg-amber-600 hover:bg-amber-700 text-white text-xs rounded px-2 py-1"
                onClick={(e) => { e.stopPropagation(); onCycleRole(); }}>Role</button>
        <button className="bg-sky-700 hover:bg-sky-800 text-white text-xs rounded px-2 py-1"
                onClick={(e) => { e.stopPropagation(); onCycleAction(); }}>Acció</button>
        <div className="text-xs opacity-80 ml-auto">{action || "—"}</div>
      </div>

      <div className="mt-2 flex items-center gap-2">
        <input type="number" className="bg-white text-black rounded px-2 py-1 w-24"
               placeholder="Quantitat" value={amount} onChange={(e) => onAmount(e.target.value)}
               onMouseDown={(e) => e.stopPropagation()} />
        <button className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs rounded px-2 py-1"
                onClick={(e) => { e.stopPropagation(); onConfirm(); }}>Confirmar</button>
        <button className="bg-red-600 hover:bg-red-700 text-white text-xs rounded px-2 py-1"
                onClick={(e) => { e.stopPropagation(); onSitout(); }}>{p.active ? "Sit out" : "Torna"}</button>
      </div>
    </div>
  );
}
