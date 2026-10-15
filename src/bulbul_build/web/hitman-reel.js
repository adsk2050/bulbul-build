"use strict";
// Highlight reel for Bulbul Flash Cricket, built while the innings is played.
//
// Every ball is recorded in the browser from the bowler's run-up: the game's
// canvas and the game's own sound. Bulbul's voice is not taken from that
// recording; every line's audio arrives whole from the server (hitman-voice.js
// hands it over), so each clip gets its line complete and clean. A ball worth
// showing (four, six, wicket) is cut into the reel as soon as its line is in,
// with the recorder paused in between, so when the innings ends only the end
// card is left to add. The reel is 30 seconds at most and never cuts a line.
//
// The end card gets a Share button: the phone's share sheet (WhatsApp Status is
// one tap from there) or, where a page cannot share files, a download.
// Nothing here talks to the server or costs anything.

(function () {
  if (!window.MediaRecorder || !HTMLCanvasElement.prototype.captureStream) return;

  const MAX_REEL = 30;      // seconds, end card included
  const RESERVE = 7;        // seconds kept free for the innings' last ball
  const FOURS_UNTIL = 12;   // fours go in only while the reel is shorter than this, so later sixes fit
  const OUTRO = 2.6;       // seconds of end card
  const AFTER_BALL = 3200;  // ms of picture kept after the ball is decided
  const LINE_WAIT = 9000;   // ms to wait for a ball's line before cutting without it
  const RATE = 24000;       // the line audio's sample rate
  const W = 720, H = 1280;

  const MIME = ["video/mp4;codecs=avc1,mp4a.40.2", "video/mp4", "video/webm;codecs=vp9,opus", "video/webm"]
    .find((m) => MediaRecorder.isTypeSupported(m));
  if (!MIME) return;
  const EXT = MIME.startsWith("video/mp4") ? "mp4" : "webm";
  const AC = window.AudioContext || window.webkitAudioContext;

  // ---- the game's sound, mixed into one track ----
  // Any node connected to a context's speakers is also connected to a tap in that
  // context, and the taps are mixed in a context of our own. This script loads
  // before the game makes its audio. Contexts marked __bulbulNoTap (the voice, and
  // our own) are left out.
  const taps = new Map();
  let mixCtx = null, mixDest = null;
  function mixer() {
    if (!mixCtx) {
      try {
        mixCtx = new AC();
        mixCtx.__bulbulNoTap = true;
        mixDest = mixCtx.createMediaStreamDestination();
        for (const t of taps.values()) mixCtx.createMediaStreamSource(t.stream).connect(mixDest);
      } catch (_) { mixCtx = null; }
    }
    if (mixCtx && mixCtx.state === "suspended") mixCtx.resume();
    return mixDest;
  }
  const connect = AudioNode.prototype.connect;
  AudioNode.prototype.connect = function (dest, ...rest) {
    const out = connect.call(this, dest, ...rest);
    if (dest instanceof AudioDestinationNode && !this.context.__bulbulNoTap) {
      try {
        let tap = taps.get(this.context);
        if (!tap) {
          tap = this.context.createMediaStreamDestination();
          taps.set(this.context, tap);
          if (mixCtx) mixCtx.createMediaStreamSource(tap.stream).connect(mixDest);
        }
        connect.call(this, tap);
      } catch (_) {}
    }
    return out;
  };
  ["pointerdown", "keydown", "touchstart"].forEach((t) => addEventListener(t, mixer, { passive: true }));

  // ---- the lines, whole ----
  const lines = new Map(); // id -> { text, chunks, samples, done, skipped, heardAt }
  const lineOf = (id) => {
    let l = lines.get(id);
    if (!l) lines.set(id, (l = { text: "", chunks: [], samples: 0, done: false, skipped: false, heardAt: 0 }));
    return l;
  };
  function pcm(id, chunk) { const l = lineOf(id); l.chunks.push(chunk); l.samples += chunk.length; }
  function line(id, text) { lineOf(id).text = text; }
  function heard(id, at) { lineOf(id).heardAt = at; }
  function lineEnd(id) { lineOf(id).done = true; pump(); }
  function skip(id) { lineOf(id).skipped = true; pump(); }

  // ---- recording each ball ----
  function gameCanvas() {
    let best = null, area = 0;
    for (const c of document.querySelectorAll("#viewport canvas, #app canvas")) {
      const a = c.width * c.height;
      if (a > area && c.getClientRects().length) { best = c; area = a; }
    }
    return best;
  }
  let video = null, videoCanvas = null;
  function recordStream() {
    const canvas = gameCanvas();
    if (!canvas) return null;
    if (canvas !== videoCanvas) { videoCanvas = canvas; video = canvas.captureStream(30); }
    const tracks = [...video.getVideoTracks()];
    const audio = mixer();
    if (audio) tracks.push(...audio.stream.getAudioTracks());
    return new MediaStream(tracks);
  }

  let innings = 0;     // bumps every start, so late callbacks from an old innings do nothing
  let waiting = null;  // the clip recording now and waiting for its ball
  const live = new Set(); // clips still recording
  let balls = 0;
  let queue = [];      // finished clips worth showing, in order
  let spare = [];      // the rest, kept in case the reel would otherwise be empty
  let summary = null;
  let reel = null;     // { state, progress, file }

  function runup() {
    if (summary) return;
    if (waiting) finish(waiting); // a run-up that never became a ball
    const s = recordStream();
    if (!s) return;
    let rec;
    try { rec = new MediaRecorder(s, { mimeType: MIME, videoBitsPerSecond: 3_000_000 }); } catch (_) { return; }
    const c = { rec, chunks: [], ball: null, n: ++balls, startedAt: performance.now(), innings };
    rec.ondataavailable = (e) => e.data.size && c.chunks.push(e.data);
    rec.onstop = () => stopped(c);
    rec.start(500);
    live.add(c);
    c.timer = setTimeout(() => finish(c), 12000);
    waiting = c;
  }
  function ball(id, kind, detail, state) {
    const c = waiting;
    if (!c || c.ball) return;
    waiting = null;
    c.ball = { kind, detail, state };
    c.id = id;
    if (keeps(detail.runs)) toast(`🎬 ${detail.runs === 6 ? "SIX" : "FOUR"} saved to your highlights`);
    c.decidedAt = performance.now();
    clearTimeout(c.timer);
    c.timer = setTimeout(() => finish(c), AFTER_BALL);
  }
  function finish(c) {
    clearTimeout(c.timer);
    if (waiting === c) waiting = null;
    c.stoppedAt = performance.now();
    if (c.rec.state !== "inactive") c.rec.stop();
  }
  function stopped(c) {
    live.delete(c);
    if (c.innings !== innings || !c.ball) return;
    c.blob = new Blob(c.chunks, { type: MIME });
    c.final = !!summary; // the innings' last ball: the reel's ending
    if (c.final || keeps(c.ball.detail.runs)) queue.push(c);
    else { spare.push(c); spare = spare.slice(-3); }
    pump();
  }
  // Sixes always; fours while there is plenty of room; wickets only as the ending
  // (the last ball). A reel of getting out is not one anybody posts.
  const keeps = (runs) => runs === 6 || (runs === 4 && (cut ? cut.used : 0) < FOURS_UNTIL);

  // ---- cutting the reel as the innings goes ----
  // One recorder on our own canvas for the whole reel, paused between highlights.
  // Nothing is joined afterwards: separate recordings joined by copying came out
  // glitchy, because each one starts its video stream with its own settings.
  let cut = null; // { canvas, ctx, actx, dest, rec, chunks, draw, used, busy }
  function cutter() {
    if (cut) return cut;
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    const actx = new AC();
    actx.__bulbulNoTap = true;
    const dest = actx.createMediaStreamDestination();
    const out = new MediaStream([...canvas.captureStream(30).getVideoTracks(), ...dest.stream.getAudioTracks()]);
    const rec = new MediaRecorder(out, { mimeType: MIME, videoBitsPerSecond: 4_000_000 });
    const c = { canvas, ctx, actx, dest, rec, chunks: [], draw: () => backdrop(ctx), used: 0, busy: false, innings };
    rec.ondataavailable = (e) => e.data.size && c.chunks.push(e.data);
    // Frames are drawn on a timer: animation frames stop in a hidden tab.
    c.tick = setInterval(() => c.rec.state === "recording" && c.draw(), 1000 / 30);
    rec.start(500);
    rec.pause();
    cut = c;
    return c;
  }
  function lineReady(c) {
    const l = lines.get(c.id);
    return !l || l.done || l.skipped || performance.now() - c.decidedAt > LINE_WAIT;
  }
  function plan(c) {
    // How long this clip runs in the reel: its picture, or its whole line, whichever is longer.
    const l = lines.get(c.id);
    const clipLen = (c.stoppedAt - c.startedAt) / 1000;
    let at = 0, dur = 0;
    if (l && l.done && l.samples) {
      dur = l.samples / RATE;
      at = l.heardAt ? (l.heardAt - c.startedAt) / 1000 : (c.decidedAt - c.startedAt) / 1000 + 0.6;
      at = Math.max(0.2, Math.min(at, clipLen));
    }
    return { line: dur ? l : null, at, dur, len: Math.max(clipLen, at + dur + 0.4) };
  }
  async function pump() {
    const c = cut;
    if ((c && c.busy) || !queue.length || !lineReady(queue[0])) return;
    const clip = queue.shift();
    const p = plan(clip);
    const room = MAX_REEL - OUTRO - (c ? c.used : 0) - (clip.final ? 0 : RESERVE);
    if (p.len > room) return pump(); // too long for what is left; a shorter one may fit
    await play(cutter(), clip, p);
    pump();
  }
  async function play(c, clip, p) {
    c.busy = true;
    const v = document.createElement("video");
    v.playsInline = true; v.preload = "auto";
    v.src = URL.createObjectURL(clip.blob);
    const src = c.actx.createMediaElementSource(v);
    const gain = c.actx.createGain();
    gain.gain.value = p.line ? 0.45 : 1; // the game's sound sits under the commentary
    src.connect(gain).connect(c.dest);
    await new Promise((r) => { v.onloadeddata = r; v.onerror = r; setTimeout(r, 4000); });
    if (c.actx.state === "suspended") await c.actx.resume().catch(() => {});
    c.draw = () => { backdrop(c.ctx); cover(c.ctx, v); overlay(c.ctx, clip); };
    c.rec.resume();
    const t0 = c.actx.currentTime;
    if (p.line) {
      const buf = c.actx.createBuffer(1, p.line.samples, RATE);
      const ch = buf.getChannelData(0);
      let o = 0;
      for (const k of p.line.chunks) { for (let i = 0; i < k.length; i++) ch[o + i] = k[i] / 32768; o += k.length; }
      const s = c.actx.createBufferSource();
      s.buffer = buf;
      s.connect(c.dest);
      s.start(t0 + p.at);
    }
    await v.play().catch(() => {});
    // The last frame holds while the line finishes.
    await sleep(p.len * 1000);
    v.pause();
    c.rec.pause();
    c.used += p.len;
    URL.revokeObjectURL(v.src);
    src.disconnect();
    c.busy = false;
  }

  // The end card's "ta-ding": a quick rising chime and a bell, made here (no music file).
  function sting(actx, dest, t0) {
    const out = actx.createGain();
    out.gain.value = 0.5;
    out.connect(dest);
    const note = (freq, at, len, type, peak) => {
      const o = actx.createOscillator(), g = actx.createGain();
      o.type = type; o.frequency.value = freq;
      g.gain.setValueAtTime(0, at);
      g.gain.linearRampToValueAtTime(peak, at + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, at + len);
      o.connect(g).connect(out);
      o.start(at); o.stop(at + len + 0.05);
    };
    [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => note(f, t0 + i * 0.07, 0.35, "triangle", 0.5));
    const bell = t0 + 0.36;
    [[1046.5, 0.45], [1568, 0.3], [2093, 0.22], [2637, 0.12]].forEach(([f, a]) => note(f, bell, 1.8, "sine", a));
  }
  // Seconds of work left at the end of the innings: the last ball's clip and line,
  // clips still to cut, and the end card.
  function estimate() {
    const busy = cut && cut.busy ? 4 : 0;
    const est = (live.size ? 6 : 0) + queue.length * 6 + busy + OUTRO + 1;
    return Math.max(5, Math.min(40, est));
  }
  function tickProgress(r, secs) {
    const t0 = performance.now();
    const id = setInterval(() => {
      if (reel !== r || r.state !== "building" || r.progress === 100) return clearInterval(id);
      // Speeding up: slow at first, faster towards the end (bars that accelerate feel
      // quicker; a stall near the end feels worst; Harrison et al., UIST 2007). The
      // estimate is padded, so most reels finish before the top and jump to done; one
      // that runs over keeps creeping on towards 99 %, never frozen.
      const f = (performance.now() - t0) / 1000 / (secs * 1.3);
      const pct = f <= 1 ? 6 + 89 * Math.pow(f, 1.6) : 95 + 4 * (1 - Math.exp(-(f - 1) * 2));
      r.progress = Math.max(1, Math.min(99, Math.floor(pct)));
      renderButton();
    }, 150);
  }

  function start() {
    innings++;
    posterImage(); // loaded by the time the end card is drawn
    if (waiting) finish(waiting);
    if (cut) { clearInterval(cut.tick); try { cut.rec.stop(); } catch (_) {} cut.actx.close(); cut = null; }
    queue = []; spare = []; live.clear(); balls = 0; summary = null; reel = null; lines.clear();
    renderButton();
  }
  async function end(detail, state) {
    summary = {
      name: state.batter || "", runs: detail.runs ?? state.runs ?? 0,
      wickets: detail.wickets ?? state.wickets ?? 0, balls: detail.balls ?? state.balls ?? 0,
    };
    const mine = innings;
    reel = { state: "building", progress: 1 };
    // The work left is known only roughly, so the percentage climbs steadily to 99
    // over the time it should take, and jumps to ready the moment the reel is done.
    tickProgress(reel, estimate());
    // The last ball's clip and line, then whatever is still queued.
    const t = performance.now();
    while (performance.now() - t < LINE_WAIT + AFTER_BALL + 15000) {
      if (mine !== innings) return;
      if (!live.size && !queue.length && !(cut && cut.busy)) break;
      await sleep(250);
      pump();
    }
    if (mine !== innings) return;
    // Nothing big happened: the last couple of balls, so there is still a reel.
    if (!cut || !cut.used) {
      for (const c of spare.slice(-2)) {
        const p = plan(c);
        if ((cut ? cut.used : 0) + p.len <= MAX_REEL - OUTRO) await play(cutter(), c, p);
        if (mine !== innings) return;
      }
    }
    if (!cut || !cut.used) { reel = { state: "failed" }; return renderButton(); }
    const c = cut;
    c.draw = () => outroCard(c.ctx);
    c.rec.resume();
    sting(c.actx, c.dest, c.actx.currentTime + 0.15);
    await sleep(OUTRO * 1000);
    const done = new Promise((r) => (c.rec.onstop = r));
    c.rec.stop();
    await done;
    clearInterval(c.tick); c.actx.close();
    cut = null;
    if (mine !== innings) return;
    // Done, often before the bar got near the top: a quick sweep to 100 % first.
    reel.progress = 100;
    renderButton();
    await sleep(450);
    if (mine !== innings) return;
    const name = `bulbul-flash-${summary.runs}-${summary.wickets}.${EXT}`;
    // A plain type: Android's share sheet turns down "video/mp4;codecs=...".
    reel = { state: "ready", file: new File([new Blob(c.chunks, { type: MIME })], name, { type: MIME.split(";")[0] }) };
    renderButton();
  }

  // ---- drawing ----
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const FONT = '"Noto Sans Devanagari", "Nirmala UI", system-ui, sans-serif';
  function wrap(ctx, text, maxW) {
    const out = [];
    let ln = "";
    for (const w of text.split(/\s+/)) {
      const t = ln ? ln + " " + w : w;
      if (ctx.measureText(t).width > maxW && ln) { out.push(ln); ln = w; } else ln = t;
    }
    if (ln) out.push(ln);
    return out;
  }
  function backdrop(ctx) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#0b1a2a"); g.addColorStop(1, "#13324d");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  function centred(ctx, text, y, size, color, weight = 800) {
    ctx.font = `${weight} ${size}px ${FONT}`;
    ctx.fillStyle = color; ctx.textAlign = "center";
    wrap(ctx, text, W - 100).forEach((l, i) => ctx.fillText(l, W / 2, y + i * size * 1.2));
  }
  // The game's cover art, taken from the page (its file name changes every build).
  let poster = null;
  function posterImage() {
    if (!poster) {
      const src = document.querySelector(".cover-art")?.src;
      if (src) { poster = new Image(); poster.src = src; }
    }
    return poster && poster.complete && poster.naturalWidth ? poster : null;
  }
  function outroCard(ctx) {
    const s = summary || { runs: 0, wickets: 0, balls: 0, name: "" };
    backdrop(ctx);
    const img = posterImage();
    if (img) {
      const k = Math.max(W / img.naturalWidth, H / img.naturalHeight);
      ctx.drawImage(img, (W - img.naturalWidth * k) / 2, (H - img.naturalHeight * k) / 2, img.naturalWidth * k, img.naturalHeight * k);
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, "rgba(8,16,28,.55)"); g.addColorStop(0.45, "rgba(8,16,28,.78)"); g.addColorStop(1, "rgba(8,16,28,.92)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    }
    centred(ctx, "BULBUL FLASH CRICKET", 190, 42, "#ffc93c", 900);
    if (s.name) centred(ctx, s.name, 300, 60, "#ffffff");
    centred(ctx, `${s.runs}/${s.wickets}`, 450, 150, "#ffffff", 900);
    centred(ctx, `${s.balls} balls`, 525, 34, "#cfe3f5", 600);
    centred(ctx, `Can you beat ${s.runs}?`, 660, 58, "#ffffff");
    // "Powered by Sarvam AI": a white badge, the one bright block on the card.
    const bw = 520, bh = 190, bx = (W - bw) / 2, by = 770;
    ctx.fillStyle = "#ffffff";
    ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 28); ctx.fill();
    ctx.textAlign = "center";
    ctx.font = `700 26px ${FONT}`; ctx.fillStyle = "#6b7785";
    ctx.fillText("POWERED BY", W / 2, by + 48);
    ctx.font = `900 72px ${FONT}`; ctx.fillStyle = "#0b1a2a";
    ctx.fillText("Sarvam AI", W / 2, by + 122);
    ctx.font = `700 26px ${FONT}`; ctx.fillStyle = "#e0761b";
    ctx.fillText("Live commentary · Bulbul Flash voice", W / 2, by + 165);
    centred(ctx, location.host + "/flash-cricket", 1100, 36, "#7fd3ff", 700);
  }
  function overlay(ctx, clip) {
    const d = clip.ball.detail || {};
    const call = String(d.game_call || (clip.ball.kind === "wicket" ? "OUT!" : d.runs ? `${d.runs} RUN${d.runs > 1 ? "S" : ""}` : "DOT BALL"));
    const tag = `${d.ball ? String(d.ball).replace("over ", "Over ").replace(", ball ", ".") + " · " : ""}${call}`;
    ctx.font = `800 40px ${FONT}`; ctx.textAlign = "center";
    const tw = ctx.measureText(tag).width + 48;
    ctx.fillStyle = clip.ball.kind === "wicket" ? "rgba(200,40,40,.9)" : "rgba(255,140,40,.92)";
    ctx.beginPath(); ctx.roundRect((W - tw) / 2, 60, tw, 64, 32); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.fillText(tag, W / 2, 106);
    const text = (lines.get(clip.id) || {}).text;
    if (text) {
      ctx.font = `700 34px ${FONT}`;
      const ls = wrap(ctx, text, W - 120).slice(0, 4);
      const h = ls.length * 44 + 40, y = H - 150 - h;
      ctx.fillStyle = "rgba(10,20,32,.78)";
      ctx.beginPath(); ctx.roundRect(40, y, W - 80, h, 24); ctx.fill();
      ctx.fillStyle = "#fff";
      ls.forEach((l, i) => ctx.fillText(l, W / 2, y + 52 + i * 44));
    }
    ctx.font = `600 26px ${FONT}`; ctx.fillStyle = "rgba(255,255,255,.85)";
    ctx.fillText("🎙️ Live commentary: Sarvam Bulbul Flash", W / 2, H - 60);
  }
  function cover(ctx, v) {
    const vw = v.videoWidth, vh = v.videoHeight;
    if (!vw || !vh) return;
    const s = Math.max(W / vw, H / vh), dw = vw * s, dh = vh * s;
    ctx.drawImage(v, (W - dw) / 2, (H - dh) / 2, dw, dh);
  }

  // ---- the Highlights widget on the end card ----
  // Shown as soon as the innings ends: a header, a filling progress bar, and Share
  // and Download visible but off, so the player knows they are coming. When the reel
  // is ready the keys switch on and pulse, a short oven "ting" plays and a phone
  // buzzes. Share opens the share sheet (WhatsApp Status is one tap from there) and
  // shows only on phones and tablets; Download keeps the file.
  let box = null, bar = null, head = null, shareBtn = null, saveBtn = null, announced = null;
  const onPhone = () => (navigator.userAgentData && navigator.userAgentData.mobile)
    || matchMedia("(pointer: coarse)").matches;
  const canShareFiles = () => {
    try { return onPhone() && !!(navigator.canShare && navigator.canShare({ files: [new File([""], "x.mp4", { type: "video/mp4" })] })); } catch (_) { return false; }
  };
  (function css() {
    const st = document.createElement("style");
    st.textContent = `
      #bb-share{flex:1 1 100%;margin:0 0 10px;padding:12px;border-radius:18px;background:rgba(10,20,32,.72);
        box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);font-family:var(--f-ui, system-ui)}
      #bb-share .bb-head{display:flex;justify-content:space-between;align-items:baseline;color:#fff;
        font:800 13px/1.2 var(--f-ui, system-ui);letter-spacing:.08em;margin:0 2px 8px}
      #bb-share .bb-head i{font-style:normal;font-weight:700;color:#ffc93c;letter-spacing:0}
      #bb-share .bb-bar{height:6px;border-radius:99px;background:rgba(255,255,255,.14);overflow:hidden;margin:0 2px 10px}
      #bb-share .bb-bar b{display:block;height:100%;width:0;border-radius:99px;background:#ffc93c;transition:width .15s linear}
      #bb-share .bb-keys{display:flex;gap:10px}
      #bb-share .bb-keys .k-cta{flex:1 1 0;min-width:0}
      #bb-share .bb-keys .k-cta:disabled{opacity:.45;filter:grayscale(.6)}
      #bb-share.is-ready .bb-bar{display:none}
      #bb-share.is-ready .bb-keys .k-cta{animation:bb-pulse 1.1s ease-in-out 6}
      @keyframes bb-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
      #bb-toast{position:fixed;left:50%;top:calc(env(safe-area-inset-top,0px) + 92px);transform:translate(-50%,-12px);
        z-index:2147483001;padding:8px 14px;border-radius:999px;background:rgba(10,20,32,.86);color:#fff;
        font:800 14px/1.2 system-ui,sans-serif;box-shadow:0 6px 18px rgba(0,0,0,.35);opacity:0;pointer-events:none;
        transition:opacity .25s,transform .25s;white-space:nowrap}
      #bb-toast.on{opacity:1;transform:translate(-50%,0)}`;
    document.head.appendChild(st);
  })();
  // The game's own button (Kit.ts cta()): a coloured face on a ledge, its display font.
  function button(kind, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `k-cta k-cta--${kind}`;
    b.innerHTML = '<span class="k-cta-face"><span></span></span>';
    b.addEventListener("click", onClick);
    return b;
  }
  function label(b, text, iconFrom) {
    const face = b.firstChild;
    face.lastChild.textContent = text;
    const svg = iconFrom && document.querySelector(`${iconFrom} svg`);
    if (svg && !face.querySelector("svg")) face.prepend(svg.cloneNode(true));
  }
  // An oven's "ting": one bright bell note that rings out.
  function ting() {
    try {
      const a = new AC();
      a.__bulbulNoTap = true;
      const t0 = a.currentTime + 0.02;
      [[1318.5, 0.35], [2637, 0.12], [3951, 0.05]].forEach(([f, peak]) => {
        const o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        g.gain.setValueAtTime(0, t0);
        g.gain.linearRampToValueAtTime(peak, t0 + 0.005);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.4);
        o.connect(g).connect(a.destination);
        o.start(t0); o.stop(t0 + 1.5);
      });
      setTimeout(() => a.close().catch(() => {}), 1800);
    } catch (_) {}
    try { navigator.vibrate && navigator.vibrate([90, 60, 90]); } catch (_) {}
  }
  function renderButton() {
    if (!box) {
      box = document.createElement("div");
      box.id = "bb-share";
      head = document.createElement("div");
      head.className = "bb-head";
      bar = document.createElement("div");
      bar.className = "bb-bar";
      bar.innerHTML = "<b></b>";
      const keys = document.createElement("div");
      keys.className = "bb-keys";
      shareBtn = button("share-wide", share);
      saveBtn = button("secondary", download);
      label(shareBtn, "SHARE", "#mcard-share");
      if (canShareFiles()) keys.append(shareBtn);
      keys.append(saveBtn);
      box.append(head, bar, keys);
    }
    if (!reel) { box.remove(); return; }
    const ready = reel.state === "ready", failed = reel.state === "failed";
    for (const b of [shareBtn, saveBtn]) b.disabled = !ready;
    label(saveBtn, keysHaveShare() ? "DOWNLOAD" : "DOWNLOAD HIGHLIGHTS");
    box.classList.toggle("is-ready", ready);
    head.innerHTML = ready ? "🎬 YOUR HIGHLIGHTS <i>ready!</i>"
      : failed ? "🎬 NO HIGHLIGHTS THIS TIME"
      : `🎬 YOUR HIGHLIGHTS <i>making… ${reel.progress || 0}%</i>`;
    bar.firstChild.style.width = `${ready ? 100 : reel.progress || 0}%`;
    box.style.display = failed ? "none" : "";
    if (ready && announced !== reel) { announced = reel; ting(); }
    place();
  }
  const keysHaveShare = () => !!(shareBtn && shareBtn.parentElement);
  function place() {
    const again = document.getElementById("again");
    if (!box || !reel || !again || box.parentElement === again.parentElement) return;
    again.parentElement.style.flexWrap = "wrap";
    again.parentElement.insertBefore(box, again);
  }
  setInterval(place, 400); // the end card is rebuilt each innings

  // During the match: a six or a four going into the highlights says so.
  let toastEl = null, toastTimer = 0;
  function toast(text) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.id = "bb-toast";
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = text;
    toastEl.classList.add("on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("on"), 2600);
  }

  function download() {
    if (!reel || reel.state !== "ready") return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(reel.file); a.download = reel.file.name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  }
  async function share() {
    if (!reel || reel.state !== "ready") return;
    const text = `Maine Bulbul Flash Cricket mein ${summary.runs} banaye, Bulbul ki live commentary ke saath! Tum beat karo: ${location.origin}/flash-cricket/`;
    try {
      await navigator.share({ files: [reel.file], text });
    } catch (e) {
      // Never a silent download: say so, and leave Download beside it.
      if (e.name !== "AbortError") {
        label(shareBtn, `SHARE FAILED (${e.name}), USE DOWNLOAD`);
        // The error's name only, so a failing phone can be diagnosed from the server log.
        fetch(`/api/reel-share-failed?name=${encodeURIComponent(e.name)}&type=${encodeURIComponent(reel.file.type)}&kb=${Math.round(reel.file.size / 1024)}`, { method: "POST" }).catch(() => {});
      }
      console.warn("[reel] share", e);
    }
  }

  window.bulbulReel = {
    runup, ball, line, pcm, heard, lineEnd, skip, start, end,
    debug: () => ({ queue, spare, used: cut ? cut.used : 0, busy: !!(cut && cut.busy), reel, summary, MIME, lines: lines.size }),
  };
})();
