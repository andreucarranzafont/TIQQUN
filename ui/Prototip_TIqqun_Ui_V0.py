import React, { useMemo, useState } from "react";

// ──────────────────────────────────────────────────────────────────────────────
// TIQQUN UI v0 — Prototip d'entrada ràpida (client-only)
// - Taula 3/4/5/6/9 jugadors
// - Selecció de BTN/SB/BB fent clic als seients
// - Entrada de cartes pròpies i del board amb clics
// - Marcadors bàsics: pot, to-call, accions per # (relatives a la BB)
// - Recomanació placeholder (fusió simple racional + simbòlica)
// Nota: és un prototip visual. La lògica completa (Monte Carlo, flux cabalístic ple)
//       viurà al backend o mòduls Python. Aquí fem una heurística suau per testing.
// ──────────────────────────────────────────────────────────────────────────────

const ALL_SUITS = ["C", "D", "T", "P"]; // Cors, Diamants, Trèvols, Piques
const ALL_RANKS = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"];

const SEATS_9 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "C1"]; // C1 = pos extra
const SEATS_6 = ["N", "NE", "E", "S", "W", "NW"]; // Hero és S
const SEATS_5 = ["N", "NE", "S", "E", "NW"];
const SEATS_4 = ["N", "NE", "S", "NW"];
const SEATS_3 = ["N", "S", "NW"];

function deck() {
  const out: string[] = [];
  for (const r of ALL_RANKS) for (const s of ALL_SUITS) out.push(r + s);
  return out;
}

function prettyCard(c?: string) {
  if (!c) return "—";
  const suit = c.slice(-1);
  const rank = c.slice(0, -1);
  const suitGlyph = suit === "C" ? "♥" : suit === "D" ? "♦" : suit === "T" ? "♣" : "♠";
  return `${rank}${suitGlyph}`;
}

function suitColor(s: string) {
  return s === "C" || s === "D" ? "text-red-600" : "text-gray-800";
}

// Heurística suau: puntuació tècnica segons nº de cartes destapades i posició
function techHeuristic(players: number, street: "preflop"|"flop"|"turn"|"river", heroIndex: number) {
  const base = 0.5 / Math.max(2, players / 2);
  const streetBonus = street === "preflop" ? 0 : street === "flop" ? 0.05 : street === "turn" ? 0.1 : 0.15;
  const pos = Math.max(0, Math.min(1, (players - heroIndex) / Math.max(1, players - 1)));
  return { pwin: Math.min(0.85, base + streetBonus), pos };
}

// Heurística simbòlica mínima: premiar centre (flop/turn/river) i penalitzar desequilibri lleu
function flowHeuristic(hero: string[], board: string[], street: string) {
  const valMap: Record<string, number> = { A: 0.9, K: 0.82, Q: 0.8, J: 0.78, "10": 0.7, "9": 0.66, "8": 0.64, "7": 0.62, "6": 0.6, "5": 0.58, "4": 0.56, "3": 0.55, "2": 0.54 };
  const suitBonus: Record<string, number> = { C: 0.03, D: 0.03, T: 0.03, P: 0.02 };
  const base = hero.reduce((acc, c) => acc + (valMap[c.slice(0, -1)] ?? 0.55) + (suitBonus[c.slice(-1)] ?? 0), 0) / Math.max(1, hero.length);
  const middle = Math.min(0.4, board.length * 0.06);
  const river = street === "river" ? 0.05 : 0;
  return Math.max(0, Math.min(1, base + middle + river));
}

function fuse(tech: {pwin:number,pos:number}, flow: number) {
  const techConf = Math.max(0, Math.min(1, 0.7*tech.pwin + 0.3*tech.pos));
  const conf = 0.6*techConf + 0.4*flow;
  let decision: "FOLD"|"CALL"|"RAISE"|"ALLIN" = "FOLD";
  if (conf >= 0.75) decision = "RAISE";
  else if (conf >= 0.58) decision = "CALL";
  return { conf, decision };
}

export default function TiqqunUI(){
  const [players, setPlayers] = useState<3|4|5|6|9>(6);
  const seats = useMemo(()=> players===9?SEATS_9:players===6?SEATS_6:players===5?SEATS_5:players===4?SEATS_4:SEATS_3,[players]);
  const [btn, setBtn] = useState<string>("NE");
  const [bbSize, setBbSize] = useState<number>(1);
  const [pot, setPot] = useState<number>(0);
  const [toCallHero, setToCallHero] = useState<number>(0);

  // Hero sempre S
  const heroSeat = "S";

  // Construir mapa d'acció rotant des de BB
  const [bbSeat, setBbSeat] = useState<string>("N");
  const actionOrder = useMemo(()=>{
    const idx = seats.indexOf(bbSeat);
    const order = idx>=0 ? [...seats.slice(idx), ...seats.slice(0, idx)] : seats;
    return order;
  },[seats, bbSeat]);
  const heroIndex = Math.max(1, actionOrder.indexOf(heroSeat)+1);

  // Cartes
  const [heroCards, setHeroCards] = useState<string[]>([]);
  const [flop, setFlop] = useState<string[]>([]);
  const [turn, setTurn] = useState<string[]>([]);
  const [river, setRiver] = useState<string[]>([]);

  const street: "preflop"|"flop"|"turn"|"river" = river.length?"river":turn.length?"turn":flop.length===3?"flop":"preflop";
  const board = [...flop, ...turn, ...river];

  // Recomanació
  const tech = techHeuristic(players, street, heroIndex);
  const flow = flowHeuristic(heroCards, board, street);
  const fused = fuse(tech, flow);

  // Helpers
  const d = useMemo(()=> deck(), []);
  const used = new Set([...heroCards, ...board]);
  const available = d.filter(c=>!used.has(c));

  function pickCard(target: "hero"|"flop"|"turn"|"river", card: string){
    if (used.has(card)) return;
    if (target==="hero" && heroCards.length<2) setHeroCards([...heroCards, card]);
    if (target==="flop" && flop.length<3) setFlop([...flop, card]);
    if (target==="turn" && turn.length<1) setTurn([card]);
    if (target==="river" && river.length<1) setRiver([card]);
  }

  function resetHand(){ setHeroCards([]); setFlop([]); setTurn([]); setRiver([]); setPot(0); setToCallHero(0); }

  // Accions simples: b/r/c/f que modifiquen pot/to-call (placeholders)
  function act(type: "b"|"r"|"c"|"f"){ 
    if(type==="b"||type==="r"){ setPot(p=>p + bbSize*3); setToCallHero(t=>heroIndex===1?0:Math.max(t, bbSize*3)); }
    if(type==="c"){ setPot(p=>p + toCallHero); setToCallHero(0); }
    if(type==="f"){ /* no-op demo */ }
  }

  // UI
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">TIQQUN UI v0 — Prototip</h1>
      <p className="text-sm opacity-70 mb-6">Entrada ràpida per a mans: selecció de seients, cartes i accions. Recomanació demo (fusió heurística).</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Panell esquerra: Config */}
        <div className="col-span-1 space-y-3">
          <div className="p-4 rounded-2xl shadow bg-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase opacity-60">Jugadors</div>
                <div className="flex gap-2 mt-1">
                  {[3,4,5,6,9].map(n=> (
                    <button key={n} onClick={()=>setPlayers(n as any)} className={`px-3 py-1 rounded-full border ${players===n?"bg-black text-white":"bg-white"}`}>{n}</button>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs uppercase opacity-60">BB</div>
                <input type="number" min={0.1} step={0.1} value={bbSize} onChange={e=>setBbSize(parseFloat(e.target.value||"1"))} className="border rounded px-2 py-1 w-24"/>
              </div>
            </div>
            <div className="mt-3 text-sm">HERO: <span className="font-semibold">S</span> | BTN: <span className="font-semibold">{btn}</span> | BB seat: <span className="font-semibold">{bbSeat}</span></div>
            <div className="mt-2 text-xs opacity-70">Acció rotativa # des de BB: {actionOrder.map((s,i)=> <span key={s} className="mr-2">#{i+1}={s}</span>)}</div>
          </div>

          <div className="p-4 rounded-2xl shadow bg-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs uppercase opacity-60">Cartes HERO</div>
              <button onClick={resetHand} className="text-xs underline">Reset mà</button>
            </div>
            <div className="flex gap-3 mb-3">
              {heroCards.map((c,i)=> (
                <div key={i} className={`px-3 py-2 border rounded-xl ${suitColor(c.slice(-1))}`}>{prettyCard(c)}</div>
              ))}
              {heroCards.length<2 && <div className="px-3 py-2 border rounded-xl opacity-40">—</div>}
              {heroCards.length<1 && <div className="px-3 py-2 border rounded-xl opacity-40">—</div>}
            </div>
            <div className="max-h-40 overflow-auto border rounded-xl p-2">
              <div className="grid grid-cols-8 gap-2 text-sm">
                {available.slice(0,64).map(c=> (
                  <button key={c} onClick={()=>pickCard("hero", c)} className="border rounded px-2 py-1 hover:bg-gray-50">
                    <span className={suitColor(c.slice(-1))}>{prettyCard(c)}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Centre: Taula i seients */}
        <div className="col-span-1 lg:col-span-1 p-4 rounded-2xl shadow bg-white">
          <div className="text-xs uppercase opacity-60 mb-2">Seients (fes clic per marcar BTN o BB)</div>
          <div className="relative h-80 bg-gradient-to-b from-gray-50 to-white rounded-2xl">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-52 h-52 rounded-full border-2 border-dashed flex items-center justify-center">
                <div className="text-center">
                  <div className="text-xs opacity-60">Board</div>
                  <div className="flex gap-2 justify-center mt-1">
                    {[0,1,2].map(i=> (
                      <button key={i} className="w-10 h-14 border rounded-lg flex items-center justify-center" onClick={()=>{}}>
                        <span className="text-sm">{prettyCard(flop[i])}</span>
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-2 justify-center mt-2">
                    <button className="w-10 h-14 border rounded-lg" onClick={()=>{}}>{prettyCard(turn[0])}</button>
                    <button className="w-10 h-14 border rounded-lg" onClick={()=>{}}>{prettyCard(river[0])}</button>
                  </div>
                </div>
              </div>
            </div>

            {/* Seients col·locats en cercle aproximat */}
            <div className="absolute top-3 left-1/2 -translate-x-1/2">
              <SeatTag id="N" active={seats.includes("N")} btn={btn} bb={bbSeat} onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute top-16 right-8">
              <SeatTag id="NE" active={seats.includes("NE")} btn={btn} bb={bbSeat} onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute top-1/2 right-2 -translate-y-1/2">
              <SeatTag id="E" active={seats.includes("E")} btn={btn} bb={bbSeat} onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute bottom-16 right-8">
              <SeatTag id="SE" active={seats.includes("SE")} btn={btn} bb={bbSeat} onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2">
              <SeatTag id="S" active={seats.includes("S")} btn={btn} bb={bbSeat} hero onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute bottom-16 left-8">
              <SeatTag id="SW" active={seats.includes("SW")} btn={btn} bb={bbSeat} onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute top-1/2 left-2 -translate-y-1/2">
              <SeatTag id="W" active={seats.includes("W")} btn={btn} bb={bbSeat} onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute top-16 left-8">
              <SeatTag id="NW" active={seats.includes("NW")} btn={btn} bb={bbSeat} onSetBtn={setBtn} onSetBb={setBbSeat} />
            </div>
            <div className="absolute top-10 left-1/2 -translate-x-1/2 text-xs opacity-60">
              Jugadors: {players} · Acció # des de BB: {actionOrder.map((s,i)=>`#${i+1}=${s}`).join("  ")}
            </div>
          </div>

          <div className="mt-3">
            <div className="text-xs uppercase opacity-60 mb-1">Selecciona cartes del board</div>
            <div className="grid grid-cols-8 gap-2 max-h-32 overflow-auto border rounded-xl p-2">
              {available.slice(0,64).map(c=> (
                <button key={c} className="border rounded px-2 py-1" onClick={()=>{
                  if (flop.length<3) pickCard("flop", c);
                  else if (turn.length<1) pickCard("turn", c);
                  else if (river.length<1) pickCard("river", c);
                }}>
                  <span className={suitColor(c.slice(-1))}>{prettyCard(c)}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Dreta: Accions i recomanació */}
        <div className="col-span-1 space-y-3">
          <div className="p-4 rounded-2xl shadow bg-white">
            <div className="text-xs uppercase opacity-60 mb-2">Pot i accions</div>
            <div className="flex items-center gap-4 mb-2">
              <div className="text-sm">Pot: <span className="font-semibold">{pot.toFixed(2)}</span></div>
              <div className="text-sm">To call HERO: <span className="font-semibold">{toCallHero.toFixed(2)}</span></div>
            </div>
            <div className="flex gap-2">
              <button onClick={()=>act("b")} className="px-3 py-2 rounded-xl border shadow-sm">Bet</button>
              <button onClick={()=>act("r")} className="px-3 py-2 rounded-xl border shadow-sm">Raise</button>
              <button onClick={()=>act("c")} className="px-3 py-2 rounded-xl border shadow-sm">Call</button>
              <button onClick={()=>act("f")} className="px-3 py-2 rounded-xl border shadow-sm">Fold</button>
            </div>
          </div>

          <div className="p-4 rounded-2xl shadow bg-white">
            <div className="text-xs uppercase opacity-60 mb-2">Recomanació (demo)</div>
            <div className="text-lg font-semibold">{fused.decision}</div>
            <div className="text-sm opacity-70">Confiança: {(fused.conf*100).toFixed(1)}%</div>
            <div className="mt-2 text-xs space-y-1">
              <div>Street: <b>{street}</b> | HERO #{heroIndex} / {players}</div>
              <div>p_win≈{(tech.pwin*100).toFixed(0)}% · flow≈{(flow*100).toFixed(0)}%</div>
              <div>HERO: {heroCards.map(prettyCard).join(" ") || "—"}</div>
              <div>Board: {board.map(prettyCard).join(" ") || "—"}</div>
            </div>
          </div>

          <div className="p-4 rounded-2xl shadow bg-white">
            <div className="text-xs uppercase opacity-60 mb-2">BTN / BB ràpid</div>
            <div className="flex gap-2 text-sm">
              {seats.map(s => (
                <button key={s} onClick={()=>setBtn(s)} className={`px-2 py-1 rounded border ${btn===s?"bg-black text-white":""}`}>{s}</button>
              ))}
            </div>
            <div className="mt-2 flex gap-2 text-sm">
              {seats.map(s => (
                <button key={s} onClick={()=>setBbSeat(s)} className={`px-2 py-1 rounded border ${bbSeat===s?"bg-black text-white":""}`}>{s}</button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SeatTag({ id, active, hero, btn, bb, onSetBtn, onSetBb }:{ id:string, active:boolean, hero?:boolean, btn:string, bb:string, onSetBtn:(s:string)=>void, onSetBb:(s:string)=>void }){
  if (!active) return null;
  const isBtn = btn===id; const isBb = bb===id; const isHero = !!hero;
  return (
    <div className={`flex items-center gap-1`}>
      <div className={`px-2 py-1 rounded-full border shadow-sm ${isHero?"bg-emerald-50 border-emerald-300":"bg-white"}`}>
        <span className="font-semibold">{id}</span>
      </div>
      <button onClick={()=>onSetBtn(id)} className={`text-xs px-2 py-1 rounded-full border ${isBtn?"bg-black text-white":"bg-white"}`}>BTN</button>
      <button onClick={()=>onSetBb(id)} className={`text-xs px-2 py-1 rounded-full border ${isBb?"bg-black text-white":"bg-white"}`}>BB</button>
    </div>
  );
}
