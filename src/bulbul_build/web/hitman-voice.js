"use strict";
// Bulbul, the commentator, for Bulbul Flash Cricket (upstream: Hitman Cricket): the game (web/hitman/, patched by
// tools/hitman/) calls window.bulbulCommentary.event(kind, detail, state) at
// the moment a ball is decided. This sends it to /ws/cricket with game
// "hitman", plays the line Bulbul streams back, and keeps the player's habits
// so the commentator can coach. Protocol: src/bulbul_build/commentary.py.
// Patterns follow cricket-voice.js (the pixel game's version).

(function () {
  const RATE = 24000;
  let ws, ac, bus;
  let nextId = 1;
  const sent = new Map(); // id -> performance.now() when the event was sent
  const firstAudioAt = new Map();
  let playingId = -1;
  let answeredId = 0; // highest id the server has answered (line or skip)
  let sources = [];
  let playAt = 0;
  let carry = new Int16Array(0);
  let held = null; // an over or end event waiting for the current line to finish

  // ---- overlay: one slim strip at the top, never in the way of a swipe ----
  // The game's scoreboard and its buttons are along the top, and the cover's
  // Play buttons sit a twentieth off the foot; so the line floats low over the
  // pitch below the batter, the credit hugs the bottom edge, and nothing here
  // takes a touch (a swipe anywhere on the field is a shot).
  const css = `
  #bb-mic{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(env(safe-area-inset-bottom,0px) + 14%);
    z-index:2147483000;width:min(92vw,420px);pointer-events:none;font:600 14px/1.3 system-ui,sans-serif;
    color:#fff;text-align:center;text-shadow:0 1px 2px #000}
  #bb-line{display:inline-block;max-width:100%;background:rgba(10,20,32,.72);border-radius:10px;padding:6px 12px;
    transition:opacity .4s;opacity:0}
  #bb-line.on{opacity:1}
  #bb-sub{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(env(safe-area-inset-bottom,0px) + 2px);
    z-index:2147483000;width:min(96vw,440px);pointer-events:none;text-align:center;
    font:500 9.5px/1.2 system-ui,sans-serif;color:#fff;opacity:.8;text-shadow:0 1px 2px #000}
  @media (max-height:500px){#bb-mic{font-size:12px}}`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
  const box = document.createElement("div");
  box.id = "bb-mic";
  box.setAttribute("aria-live", "polite");
  box.innerHTML = '<div id="bb-line"></div>';
  const sub = document.createElement("div");
  sub.id = "bb-sub";
  sub.innerHTML = '<span id="bb-speed">🎙️ Live commentary: Sarvam Bulbul Flash</span>' +
    ' · 3D game: ekcuttingchaidesign (open source)';
  (document.body ? Promise.resolve() : new Promise((r) => addEventListener("DOMContentLoaded", r))).then(() => { document.body.appendChild(box); document.body.appendChild(sub); });
  const $ = (id) => document.getElementById(id);
  let hideTimer = 0;
  function showLine(text) {
    const el = $("bb-line");
    if (!el) return;
    el.textContent = text;
    el.classList.add("on");
    clearTimeout(hideTimer);
  }
  // The game's menus, scorecard and feedback sheet are .modal-overlay screens; a
  // caption on top of them covered their text. The line is hidden while one is
  // up (its audio still plays).
  function screenUp() {
    for (const el of document.querySelectorAll(".modal-overlay, dialog[open]")) {
      if (!el.classList.contains("hidden") && el.getClientRects().length) return true;
    }
    return false;
  }
  setInterval(() => { box.style.visibility = screenUp() ? "hidden" : ""; }, 200);
  function fadeLineSoon() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => $("bb-line") && $("bb-line").classList.remove("on"), 5000);
  }

  // ---- the game's result banner: only the big three are shown ----
  // SIX, FOUR and wickets keep their banner; dots, singles and the game's timing
  // hints stay hidden (see the CSS in the game's index.html). The voice does the rest.
  const BIG = /^(SIX|FOUR|OUT|BOWLED|CAUGHT|LBW|STUMPED|RUN OUT|HIT WICKET|WICKET)/i;
  setInterval(() => {
    const r = document.getElementById("result"), t = document.getElementById("result-text");
    if (r && t) r.classList.toggle("bb-big", BIG.test((t.textContent || "").trim()));
  }, 100);

  // ---- audio ----
  function audio() {
    if (!ac) {
      ac = new (window.AudioContext || window.webkitAudioContext)();
      ac.__bulbulNoTap = true; // the reel lays in the clean line audio itself
      bus = ac.createGain();
      bus.gain.value = 0.9; // was 1.4: too loud over the game
      bus.connect(ac.destination);
    }
    if (ac.state === "suspended") ac.resume();
    return ac;
  }
  // The first tap, swipe or key unlocks audio (browsers need a gesture).
  ["pointerdown", "keydown", "touchstart"].forEach((t) => window.addEventListener(t, audio, { passive: true }));

  function stopAll() {
    for (const s of sources) { try { s.src.stop(); } catch (_) {} }
    sources = [];
    carry = new Int16Array(0);
    playAt = 0;
  }

  function connect() {
    ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/cricket`);
    ws.binaryType = "arraybuffer";
    ws.onmessage = (e) => (typeof e.data === "string" ? onMsg(JSON.parse(e.data)) : onPcm(e.data));
    ws.onclose = () => setTimeout(connect, 1500);
  }
  connect();

  function onMsg(m) {
    const reel = window.bulbulReel;
    if (m.type === "line") {
      reel && reel.line(m.id, m.text);
      answeredId = Math.max(answeredId, m.id);
      stopAll(); // a new line takes the mic
      playingId = m.id;
      // No caption during play: the voice is the point. Errors still show.
    } else if (m.type === "skip") {
      reel && reel.skip(m.id);
      answeredId = Math.max(answeredId, m.id);
      if (m.id === playingId) stopAll();
    } else if (m.type === "line_end") {
      reel && reel.lineEnd(m.id);
      const t = sent.get(m.id);
      const first = firstAudioAt.get(m.id);
      const total = t && first ? Math.round(first - t) : null;
      $("bb-speed").textContent =
        `⚡ Bulbul first audio ${m.ttfa_ms ?? "–"} ms · LLM ${m.llm_ms} ms` + (total ? ` · shot → voice ${total} ms` : "");
      fadeLineSoon();
    } else if (m.type === "error") {
      showLine(m.message);
      fadeLineSoon();
    }
  }

  function onPcm(buf) {
    const id = new DataView(buf).getUint32(0, true);
    // The reel keeps every line's audio whole, played live or not.
    if (window.bulbulReel) window.bulbulReel.pcm(id, new Int16Array(buf.slice(4)));
    if (id !== playingId || !ac) return;
    const fresh = new Int16Array(buf, 4);
    const all = new Int16Array(carry.length + fresh.length);
    all.set(carry); all.set(fresh, carry.length);
    if (all.length < 1440 && playAt > ac.currentTime + 0.05) { carry = all; return; } // ~60 ms pieces
    carry = new Int16Array(0);
    const b = ac.createBuffer(1, all.length, RATE);
    const ch = b.getChannelData(0);
    for (let i = 0; i < all.length; i++) ch[i] = all[i] / 32768;
    const src = ac.createBufferSource();
    src.buffer = b;
    src.connect(bus);
    const at = Math.max(ac.currentTime + 0.01, playAt);
    src.start(at);
    if (!firstAudioAt.has(id)) {
      firstAudioAt.set(id, performance.now() + (at - ac.currentTime) * 1000);
      if (window.bulbulReel) window.bulbulReel.heard(id, firstAudioAt.get(id));
    }
    playAt = at + b.duration;
    sources.push({ id, src });
  }

  // ---- the player's habits, sent with every event so the coach can be specific ----
  const h = {
    balls: 0, swings: 0, early: 0, late: 0, onTime: 0, sumTiming: 0, timed: 0,
    shots: {}, offLine: 0, leftAlone: 0, sixes: 0, fours: 0, dots: 0,
    outs: {}, vs: {}, recent: [],
  };
  const bump = (o, k) => { o[k] = (o[k] || 0) + 1; };
  function ballKind(d) {
    const kinds = [];
    if (!d) return kinds;
    if (/bouncer|back of a length/.test(d.length)) kinds.push("short");
    else if (/yorker|full/.test(d.length)) kinds.push("full");
    if (d.line === "outside off") kinds.push("wide outside off");
    if (d.line === "leg" || d.line === "outside leg") kinds.push("on the pads");
    if (d.bowler === "spinner") kinds.push("spin");
    if (d.pace_kph >= 150) kinds.push("150+ kph");
    return kinds;
  }
  function learn(kind, d) {
    if (!["hit", "miss", "wicket"].includes(kind)) return;
    h.balls++;
    const runs = d.out ? "W" : String(d.runs ?? 0);
    h.recent = [...h.recent, runs].slice(-8);
    if (d.runs === 6) h.sixes++;
    if (d.runs === 4) h.fours++;
    if (!d.out && !d.runs) h.dots++;
    if (d.out) bump(h.outs, d.how);
    const shot = d.swung ? d.shot_code : "LEFT_ALONE";
    if (!d.swung) h.leftAlone++;
    else {
      h.swings++;
      bump(h.shots, d.shot_code);
      if (d.early_or_late === "early") h.early++;
      else if (d.early_or_late === "late") h.late++;
      else if (d.early_or_late === "on time") h.onTime++;
      if (typeof d.timing_ms === "number") { h.sumTiming += d.timing_ms; h.timed++; }
      if (d.suits_line === false) h.offLine++;
    }
    for (const k of ballKind(d.delivery)) {
      const v = (h.vs[k] = h.vs[k] || { balls: 0, runs: 0, outs: 0, shots: {} });
      v.balls++;
      v.runs += d.runs || 0;
      if (d.out) v.outs++;
      bump(v.shots, shot);
    }
  }
  const top = (o, n = 2) => Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, n).map(([k, c]) => `${k} x${c}`).join(", ");
  function player() {
    const vs = {};
    for (const [k, v] of Object.entries(h.vs)) vs[k] = `${v.balls} balls, ${v.runs} runs, ${v.outs} out; played: ${top(v.shots, 3)}`;
    return {
      balls_faced: h.balls, swings: h.swings, left_alone: h.leftAlone,
      timing: { early: h.early, late: h.late, on_time: h.onTime, avg_ms: h.timed ? Math.round(h.sumTiming / h.timed) : null, note: "positive ms = early" },
      favourite_shots: top(h.shots, 3) || null,
      wrong_shot_for_the_line: h.offLine,
      against: vs,
      sixes: h.sixes, fours: h.fours, dots: h.dots,
      dismissals: top(h.outs, 3) || null,
      last_balls: h.recent.join(" "),
    };
  }

  // ---- sending ----
  function send(kind, detail, state) {
    const id = nextId++;
    if (["hit", "miss", "wicket"].includes(kind) && window.bulbulReel) window.bulbulReel.ball(id, kind, detail, state);
    sent.set(id, performance.now());
    if (ws && ws.readyState === 1) {
      ws.send(JSON.stringify({ type: "event", id, game: "hitman", kind, detail, state, player: player() }));
    }
    if (window.BULBUL_DEBUG) console.log("[bulbul]", kind, detail, state);
  }
  // Bulbul is still busy with the last ball: waiting for its line, or speaking it.
  function busy() {
    const waiting = nextId - 1 > answeredId && performance.now() - (sent.get(nextId - 1) || 0) < 3000;
    const speaking = ac && playAt > ac.currentTime + 0.05;
    return waiting || speaking;
  }
  // An over or end line would cut the ball's line short (the server treats them
  // as urgent), so they wait until it has been said, or give up waiting.
  setInterval(() => {
    if (!held) return;
    if (!busy() || performance.now() > held.until) {
      const e = held;
      held = null;
      send(e.kind, e.detail, e.state);
    }
  }, 150);

  // ---- past matches, kept in this browser so the start line can coach from them ----
  const HISTORY_KEY = "bulbul-hitman-history";
  function readHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch (_) { return []; }
  }
  function keepMatch(detail) {
    const p = player();
    const weak = Object.entries(p.against).filter(([, v]) => / [1-9]\d* out/.test(v)).map(([k]) => k);
    const match = {
      runs: detail.runs ?? null, balls: detail.balls ?? null, wickets: detail.wickets ?? null,
      fours: h.fours, sixes: h.sixes, timing: p.timing, dismissals: p.dismissals,
      favourite_shots: p.favourite_shots, out_to: weak, wrong_shot_for_the_line: h.offLine,
    };
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify([...readHistory(), match].slice(-10))); } catch (_) {}
  }
  function pastMatches() {
    const all = readHistory();
    if (!all.length) return { matches_played: 0 };
    const runs = all.map((m) => m.runs || 0);
    const early = all.reduce((s, m) => s + (m.timing?.early || 0), 0);
    const late = all.reduce((s, m) => s + (m.timing?.late || 0), 0);
    return {
      matches_played: all.length,
      average_runs: Math.round(runs.reduce((a, b) => a + b, 0) / all.length),
      best_runs: Math.max(...runs),
      timing_across_matches: { early, late },
      last_matches: all.slice(-3),
    };
  }

  window.bulbulCommentary = {
    event(kind, detail, state) {
      detail = detail || {};
      state = state || {};
      // The run-up is for the highlight reel only; Bulbul says nothing for it.
      if (kind === "runup") return window.bulbulReel && window.bulbulReel.runup();
      if (kind === "start") {
        window.bulbulReel && window.bulbulReel.start();
        for (const k of ["balls", "swings", "early", "late", "onTime", "sumTiming", "timed", "offLine", "leftAlone", "sixes", "fours", "dots"]) h[k] = 0;
        h.shots = {}; h.outs = {}; h.vs = {}; h.recent = [];
        held = null;
        return send(kind, { ...detail, history: pastMatches() }, state);
      }
      learn(kind, detail);
      if (kind === "end") { keepMatch(detail); window.bulbulReel && window.bulbulReel.end(detail, state); }
      if (kind === "over" || kind === "end") {
        held = { kind, detail, state, until: performance.now() + (kind === "end" ? 4000 : 6000) };
        return;
      }
      held = null; // a new ball has been bowled; the over's tip has missed its slot
      send(kind, detail, state);
    },
    habits: player,
  };
})();
