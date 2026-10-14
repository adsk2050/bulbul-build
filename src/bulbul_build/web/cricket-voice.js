"use strict";
// Gully Bhaiya: sends each game event to /ws/cricket and plays the commentary
// Bulbul streams back. The game (cricket.html) calls gv.event / gv.swing.
// Protocol: see src/bulbul_build/commentary.py.

(function () {
  const RATE = 24000;
  const $ = (id) => document.getElementById(id);
  let ws, ac, bus;
  let nextId = 1;
  const sent = new Map(); // id -> performance.now() when the event was sent
  let playingId = -1;
  let sources = []; // { id, src }
  let playAt = 0;
  let carry = new Int16Array(0);

  const stats = {
    swings: 0, contacts: 0, early: 0, late: 0, sumTiming: 0,
    sixes: 0, fours: 0, dots: 0, lastTiming: null,
  };

  function audio() {
    if (!ac) {
      ac = new (window.AudioContext || window.webkitAudioContext)();
      bus = ac.createGain();
      bus.gain.value = 1.4;
      bus.connect(ac.destination);
    }
    if (ac.state === "suspended") ac.resume();
    return ac;
  }
  // The first tap or key anywhere unlocks audio (browsers need a gesture).
  ["pointerdown", "keydown", "touchstart"].forEach((t) => window.addEventListener(t, audio, { once: false, passive: true }));

  function connect() {
    ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/cricket`);
    ws.binaryType = "arraybuffer";
    ws.onmessage = (e) => (typeof e.data === "string" ? onMsg(JSON.parse(e.data)) : onPcm(e.data));
    ws.onclose = () => setTimeout(connect, 1500);
  }
  connect();

  function state() { return window.gameState ? window.gameState() : {}; }

  function player() {
    const n = Math.max(1, stats.swings);
    return {
      swings: stats.swings, middled: stats.contacts, early: stats.early, late: stats.late,
      avg_timing_ms: Math.round(stats.sumTiming / n), // positive = early
      last_timing_ms: stats.lastTiming, sixes: stats.sixes, fours: stats.fours, dots: stats.dots,
    };
  }

  function stopAll() {
    for (const s of sources) { try { s.src.stop(); } catch (_) {} }
    sources = [];
    carry = new Int16Array(0);
    playAt = 0;
  }

  function onMsg(m) {
    if (m.type === "line") {
      stopAll(); // a new line takes the mic
      playingId = m.id;
      $("mic-line").textContent = m.text;
      if (window.triggerPopup) triggerPopup("🎙️ " + (m.kind || "").toUpperCase());
    } else if (m.type === "skip") {
      if (m.id === playingId) stopAll();
    } else if (m.type === "line_end") {
      const t = sent.get(m.id);
      const first = firstAudioAt.get(m.id);
      const total = t && first ? Math.round(first - t) : null;
      $("mic-speed").textContent =
        `⚡ Bulbul first audio ${m.ttfa_ms ?? "–"} ms · LLM ${m.llm_ms} ms` + (total ? ` · shot → voice ${total} ms` : "");
    } else if (m.type === "error") {
      $("mic-line").textContent = m.message;
    }
  }

  const firstAudioAt = new Map();
  function onPcm(buf) {
    const id = new DataView(buf).getUint32(0, true);
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
    if (!firstAudioAt.has(id)) firstAudioAt.set(id, performance.now() + (at - ac.currentTime) * 1000);
    playAt = at + b.duration;
    sources.push({ id, src });
  }

  window.gv = {
    event(kind, detail) {
      if (kind === "hit") {
        if (detail.runs === 6) stats.sixes++;
        if (detail.runs === 4) stats.fours++;
      }
      if (kind === "miss") stats.dots++;
      const id = nextId++;
      sent.set(id, performance.now());
      if (ws && ws.readyState === 1) {
        ws.send(JSON.stringify({ type: "event", id, game: "gully", kind, detail, state: state(), player: player() }));
      }
    },
    swing(timingMs, contact) {
      stats.swings++;
      if (contact) stats.contacts++;
      if (timingMs > 60) stats.early++;
      if (timingMs < -60) stats.late++;
      stats.sumTiming += timingMs;
      stats.lastTiming = timingMs;
    },
    ballBowled() {},
    shareLink() {
      const url = location.origin + "/cricket";
      const s = state();
      const text = `Gully Bhaiya ne meri commentary ki 🏏🎙️ ${s.runs}/${s.wickets} chasing ${s.target}. Tu kitna maarega? ${url}`;
      if (navigator.share) navigator.share({ text }).catch(() => {});
      else navigator.clipboard.writeText(text);
    },
  };
})();
