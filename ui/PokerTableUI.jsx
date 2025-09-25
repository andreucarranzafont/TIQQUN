import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Users,
  Crown,
  Eye,
  EyeOff,
  ChevronRight,
  Cards as CardsIcon,
  Coin,
  Check,
  RotateCcw,
  Sparkles,
  Hand,
} from "lucide-react";

const seats = [1, 2, 3, 4, 5, 6];

const defaultPlayers = [
  { id: 1, name: "YOU", stack: 100, bet: 0, active: true },
  { id: 2, name: "MrBlue", stack: 100, bet: 0, active: true },
  { id: 3, name: "MrBlonde", stack: 100, bet: 0, active: true },
  { id: 4, name: "MrWhite", stack: 100, bet: 0, active: true },
  { id: 5, name: "MrPink", stack: 100, bet: 0, active: true },
  { id: 6, name: "MrBrown", stack: 100, bet: 0, active: true },
];

const roleCycle = ["", "BTN", "SB", "BB", "UTG", "MP", "CO"];
const actionCycle = ["", "Check/Call", "Bet/Raise", "Fold"];

const CardSlot = ({ label = "" }) => (
  <div className="w-14 h-20 rounded-xl border border-white/30 bg-white/10 backdrop-blur-sm flex items-center justify-center text-white/80 text-sm shadow-md">
    {label}
  </div>
);

export default function PokerTableUI() {
  const [players, setPlayers] = useState(defaultPlayers);
  const [roles, setRoles] = useState({});
  const [actions, setActions] = useState({});
  const [amounts, setAmounts] = useState({});
  const [street, setStreet] = useState("preflop");
  const [recs, setRecs] = useState([]);
  const [handNotes, setHandNotes] = useState("");

  // Posicions circulars (hero a les 18:00)
  const seatPositions = useMemo(() => {
    const angles = [90, 30, -30, -90, -150, 150]; // graus
    const radius = 235;
    return seats.map((s, idx) => {
      const a = (angles[idx] * Math.PI) / 180;
      const x = Math.cos(a) * radius;
      const y = Math.sin(a) * radius;
      return { seat: s, x, y };
    });
  }, []);

  const assignRole = (id) => {
    setRoles((r) => {
      const current = r[id] || "";
      const next = roleCycle[(roleCycle.indexOf(current) + 1) % roleCycle.length];
      return { ...r, [id]: next };
    });
  };

  const assignAction = (id) => {
    setActions((a) => {
      const current = a[id] || "";
      const next = actionCycle[(actionCycle.indexOf(current) + 1) % actionCycle.length];
      return { ...a, [id]: next };
    });
  };

  const toggleActive = (id) => {
    setPlayers((ps) => ps.map((p) => (p.id === id ? { ...p, active: !p.active } : p)));
  };

  const confirmAction = (id) => {
    const p = players.find((x) => x.id === id);
    if (!p) return;

    const amt = Number(amounts[id] || 0);
    const act = actions[id] || "";

    if (act === "Bet/Raise" && amt > 0) {
      setPlayers((ps) =>
        ps.map((x) =>
          x.id === id ? { ...x, bet: x.bet + amt, stack: Math.max(0, x.stack - amt) } : x
        )
      );
    }
    if (act === "Fold") {
      setPlayers((ps) => ps.map((x) => (x.id === id ? { ...x, active: false } : x)));
    }

    setRecs((rr) =>
      [
        `Recomanació: ${p.name} ${act || "(sense acció)"}${act === "Bet/Raise" ? ` ${amt}` : ""}.`,
        ...rr,
      ].slice(0, 6)
    );
  };

  const nextStreet = () => {
    setStreet((s) =>
      s === "preflop" ? "flop" : s === "flop" ? "turn" : s === "turn" ? "river" : s === "river" ? "showdown" : "preflop"
    );
  };

  const resetHand = () => {
    setPlayers(defaultPlayers.map((p) => ({ ...p })));
    setRoles({});
    setActions({});
    setAmounts({});
    setRecs([]);
    setStreet("preflop");
    setHandNotes("");
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-slate-900 via-slate-950 to-black text-white p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          <h1 className="text-xl font-semibold">TIQQUN — Taula de 6 jugadors (UI semi-pro)</h1>
        </div>
        <div className="flex items-center gap-2 text-sm opacity-80">
          <Crown className="w-4 h-4" />
          <span>Hero al seient 1 (6:00)</span>
        </div>
      </div>

      {/* Main layout */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left: Recomanacions / Notes */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <section className="p-3 rounded-2xl bg-white/5 border border-white/10 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4" />
              <h2 className="font-medium">Recomanacions (en viu)</h2>
            </div>
            <div className="space-y-1 text-sm">
              {recs.length === 0 ? (
                <p className="opacity-70">Cap recomanació encara. Confirma una acció per veure suggeriments.</p>
              ) : (
                recs.map((r, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <ChevronRight className="w-3 h-3 mt-1 opacity-60" />
                    <p>{r}</p>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="p-3 rounded-2xl bg-white/5 border border-white/10 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Hand className="w-4 h-4" />
              <h2 className="font-medium">Registrar resultat de la mà</h2>
            </div>
            <textarea
              value={handNotes}
              onChange={(e) => setHandNotes(e.target.value)}
              placeholder="Anota aquí què ha passat (guanys, errors, lectura de rivals, etc.)"
              className="w-full min-h-[120px] rounded-xl bg-black/40 border border-white/10 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400/50"
            />
            <button
              onClick={() => setRecs((r) => ["Fitxa de mà guardada (local).", ...r].slice(0, 6))}
              className="mt-2 w-full py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-semibold"
            >
              Guardar fitxa
            </button>
          </section>
        </div>

        {/* Center: Table */}
        <div className="col-span-12 lg:col-span-6">
          <div className="relative aspect-square rounded-[2rem] border border-emerald-400/20 bg-emerald-900/20 shadow-inner overflow-hidden">
            {/* Felt gradient */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(16,185,129,0.25),rgba(0,0,0,0.6))]" />

            {/* Community cards */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <div className="flex gap-2 mb-3 items-center">
                <CardsIcon className="w-4 h-4 opacity-70" />
                <span className="text-xs uppercase tracking-wider opacity-70">{street.toUpperCase()}</span>
              </div>
              <div className="flex gap-3">
                <CardSlot label={street !== "preflop" ? "🂠" : ""} />
                <CardSlot label={street !== "preflop" ? "🂠" : ""} />
                <CardSlot label={street === "turn" || street === "river" || street === "showdown" ? "🂠" : ""} />
                <CardSlot label={street === "river" || street === "showdown" ? "🂠" : ""} />
                <CardSlot label={street === "showdown" ? "🂠" : ""} />
              </div>
            </div>

            {/* Seat widgets around the circle */}
            <div className="absolute inset-0">
              {seatPositions.map(({ seat, x, y }, idx) => {
                const p = players[seat - 1];
                const isHero = p.name === "YOU";
                return (
                  <motion.div
                    key={seat}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.05 * idx }}
                    className="absolute"
                    style={{ left: `calc(50% + ${x}px)`, top: `calc(50% + ${y}px)` }}
                  >
                    <div
                      className={`-translate-x-1/2 -translate-y-1/2 w-[220px] p-3 rounded-2xl shadow-lg border ${
                        isHero ? "border-emerald-400/60 bg-emerald-900/30" : "border-white/10 bg-white/5"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          {isHero ? (
                            <Crown className="w-4 h-4 text-emerald-300" />
                          ) : (
                            <Users className="w-4 h-4 opacity-70" />
                          )}
                          <span className={`text-sm font-semibold ${isHero ? "text-emerald-200" : ""}`}>{p.name}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="px-1.5 py-0.5 rounded bg-black/40 border border-white/10">Seat {seat}</span>
                          <span className="px-1.5 py-0.5 rounded bg-black/40 border border-white/10">
                            {roles[p.id] || "—"}
                          </span>
                        </div>
                      </div>

                      {/* Row 1: Role / Active toggle */}
                      <div className="flex items-center gap-2 mb-2">
                        <button
                          onClick={() => assignRole(p.id)}
                          className="px-2 py-1 rounded-lg bg-white/10 border border-white/10 text-xs hover:bg-white/15"
                        >
                          Cicle rol
                        </button>
                        <button
                          onClick={() => toggleActive(p.id)}
                          className={`px-2 py-1 rounded-lg border text-xs flex items-center gap-1 ${
                            p.active ? "bg-emerald-500 text-black border-emerald-400" : "bg-white/10 border-white/10"
                          }`}
                        >
                          {p.active ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}{" "}
                          {p.active ? "Actiu" : "Inactiu"}
                        </button>
                      </div>

                      {/* Row 2: Action tabs */}
                      <div className="flex items-center gap-2 mb-2">
                        <button
                          onClick={() => assignAction(p.id)}
                          className="px-2 py-1 rounded-lg bg-white/10 border border-white/10 text-xs hover:bg-white/15"
                        >
                          Acció: {actions[p.id] || "—"}
                        </button>
                        <div className="flex items-center gap-2 text-xs ml-auto">
                          <div className="px-2 py-1 rounded bg-black/40 border border-white/10 flex items-center gap-1">
                            <Coin className="w-3 h-3" />
                            Stack {p.stack.toFixed(1)}
                          </div>
                          <div className="px-2 py-1 rounded bg-black/40 border border-white/10">
                            Bet {p.bet.toFixed(1)}
                          </div>
                        </div>
                      </div>

                      {/* Row 3: Amount + Confirm */}
                      <div className="flex items-center gap-2">
                        <input
                          type="range"
                          min={0}
                          max={Math.max(0, p.stack)}
                          step={1}
                          value={Number(amounts[p.id] || 0)}
                          onChange={(e) =>
                            setAmounts((a) => ({ ...a, [p.id]: Number(e.target.value) }))
                          }
                          className="w-full"
                        />
                        <div className="w-16 text-right text-xs">
                          {Number(amounts[p.id] || 0).toFixed(0)}
                        </div>
                        <button
                          onClick={() => confirmAction(p.id)}
                          className="px-2 py-1 rounded-lg bg-emerald-400 text-black text-xs font-semibold flex items-center gap-1"
                        >
                          <Check className="w-3 h-3" />
                          Confirma
                        </button>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Street controls */}
          <div className="mt-3 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <button
                onClick={nextStreet}
                className="px-3 py-2 rounded-xl bg-white/10 border border-white/10 hover:bg-white/15 flex items-center gap-2"
              >
                <CardsIcon className="w-4 h-4" />
                Següent fase
              </button>
              <button
                onClick={resetHand}
                className="px-3 py-2 rounded-xl bg-white/10 border border-white/10 hover:bg-white/15 flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                Reset mà
              </button>
            </div>
            <div className="text-xs opacity-80">Fase actual: {street}</div>
          </div>
        </div>

        {/* Right: Quick help */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <section className="p-3 rounded-2xl bg-white/5 border border-white/10 shadow-sm">
            <h2 className="font-medium mb-2">Comandes ràpides</h2>
            <ul className="text-sm space-y-1 opacity-90">
              <li>• Cicle de rol → «Cicle rol»</li>
              <li>• Acció → «Acció: …» per canviar</li>
              <li>• Quantitat → slider</li>
              <li>• Confirmar → «Confirma»</li>
              <li>• Actiu/Inactiu → botó amb ull</li>
              <li>• Fase (Flop/Turn/River) → «Següent fase»</li>
              <li>• Reiniciar mà → «Reset mà»</li>
            </ul>
          </section>

          <section className="p-3 rounded-2xl bg-white/5 border border-white/10 shadow-sm">
            <h2 className="font-medium mb-2">Notes</h2>
            <p className="text-sm opacity-90">
              Demo local sense backend. Quan vulguis, la connectem al motor TIQQUN/SAS i registrem cada mà a JSON.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
