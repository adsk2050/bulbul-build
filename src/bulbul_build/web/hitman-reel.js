"use strict";
// Highlight reel for Bulbul Flash Cricket, built while the innings is played.
//
// Every ball is recorded in the browser from the bowler's run-up: the game's
// canvas and the game's own sound. Bulbul's voice is not taken from that
// recording; every line's audio arrives whole from the server (hitman-voice.js
// hands it over), so each clip gets its line complete and clean. Each four, six
// and wicket is cut into its own finished segment as soon as its line is in; at
// the end the best of the whole match (30 s at most, the last ball always in) are
// joined on the server without re-encoding, with an end card and its sting.
//
// The end card gets a Share button: the phone's share sheet (WhatsApp Status is
// one tap from there) or, where a page cannot share files, a download.
// The only server call is /api/reel (ffmpeg joins the segments); no Sarvam cost.

(function () {
  if (!window.MediaRecorder || !HTMLCanvasElement.prototype.captureStream) return;

  const MAX_REEL = 30;      // seconds, end card included
  const KEEP_SEGMENTS = 8;  // finished highlight segments held while the innings goes on
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

  function worth(kind, d) {
    if (kind === "wicket") return d.how === "caught" || d.how === "caught behind" ? 6 : 5;
    if (d.runs === 6) return 7;
    if (d.runs === 4) return 4;
    return d.runs > 0 ? 1 : 0;
  }

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
    c.score = worth(c.ball.kind, c.ball.detail);
    c.final = !!summary; // the innings' last ball: the reel's ending
    if (c.final || c.score >= 4) queue.push(c);
    else { spare.push(c); spare = spare.slice(-3); }
    pump();
  }

  // ---- each highlight cut into its own finished segment, while the innings goes on ----
  // A segment is the clip with its tag, its caption and its line, recorded on our own
  // canvas. At the end the best are picked from the whole match and the server joins
  // them without re-encoding, so the reel is ready moments after the last ball.
  let stage = null; // { canvas, ctx, actx, dest, stream, draw, recording, busy, tick }
  let segs = [];    // { blob, len, score, n, final }
  function stager() {
    if (stage) return stage;
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    const actx = new AC();
    actx.__bulbulNoTap = true;
    const dest = actx.createMediaStreamDestination();
    const stream = new MediaStream([...canvas.captureStream(30).getVideoTracks(), ...dest.stream.getAudioTracks()]);
    const s = { canvas, ctx, actx, dest, stream, draw: () => backdrop(ctx), recording: false, busy: false };
    // Frames are drawn on a timer: animation frames stop in a hidden tab.
    s.tick = setInterval(() => s.recording && s.draw(), 1000 / 30);
    stage = s;
    return s;
  }
  // Records whatever `body` sets up to draw and play on the stage, for `secs`, as one segment.
  async function record(s, secs, body) {
    const rec = new MediaRecorder(s.stream, { mimeType: MIME, videoBitsPerSecond: 4_000_000 });
    const chunks = [];
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    const done = new Promise((r) => (rec.onstop = r));
    if (s.actx.state === "suspended") await s.actx.resume().catch(() => {});
    const t0 = s.actx.currentTime + 0.05;
    const after = await body(t0);
    s.draw();
    s.recording = true;
    rec.start(500);
    await sleep(secs * 1000);
    s.recording = false;
    rec.stop();
    await done;
    if (after) after();
    return new Blob(chunks, { type: MIME });
  }
  function lineReady(c) {
    const l = lines.get(c.id);
    return !l || l.done || l.skipped || performance.now() - c.decidedAt > LINE_WAIT;
  }
  function plan(c) {
    // How long this clip runs: its picture, or its whole line, whichever is longer.
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
  async function cutClip(clip) {
    const s = stager();
    const p = plan(clip);
    const v = document.createElement("video");
    v.playsInline = true; v.preload = "auto";
    v.src = URL.createObjectURL(clip.blob);
    const src = s.actx.createMediaElementSource(v);
    const gain = s.actx.createGain();
    gain.gain.value = p.line ? 0.45 : 1; // the game's sound sits under the commentary
    src.connect(gain).connect(s.dest);
    await new Promise((r) => { v.onloadeddata = r; v.onerror = r; setTimeout(r, 4000); });
    const blob = await record(s, p.len, async (t0) => {
      s.draw = () => { backdrop(s.ctx); cover(s.ctx, v); overlay(s.ctx, clip); };
      if (p.line) {
        const buf = s.actx.createBuffer(1, p.line.samples, RATE);
        const ch = buf.getChannelData(0);
        let o = 0;
        for (const k of p.line.chunks) { for (let i = 0; i < k.length; i++) ch[o + i] = k[i] / 32768; o += k.length; }
        const b = s.actx.createBufferSource();
        b.buffer = buf; b.connect(s.dest); b.start(t0 + p.at);
      }
      await v.play().catch(() => {});
      return () => { v.pause(); URL.revokeObjectURL(v.src); src.disconnect(); };
    });
    return { blob, len: p.len, score: clip.score, n: clip.n, final: clip.final };
  }
  async function pump() {
    if ((stage && stage.busy) || !queue.length || !lineReady(queue[0])) return;
    const clip = queue.shift();
    if (plan(clip).len > MAX_REEL - OUTRO) return pump(); // a clip longer than the whole reel
    const s = stager();
    s.busy = true;
    const mine = innings;
    try {
      const seg = await cutClip(clip);
      if (mine !== innings) return;
      segs.push(seg);
      // Keep the best few; the last ball is never dropped.
      while (segs.length > KEEP_SEGMENTS) {
        const drop = segs.filter((x) => !x.final).reduce((lo, x) => (x.score < lo.score || (x.score === lo.score && x.n < lo.n) ? x : lo));
        segs = segs.filter((x) => x !== drop);
      }
    } catch (e) {
      console.warn("[reel] segment", e);
    } finally {
      s.busy = false;
    }
    pump();
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
  async function cutOutro() {
    const s = stager();
    return record(s, OUTRO, async (t0) => {
      s.draw = () => outroCard(s.ctx);
      sting(s.actx, s.dest, t0 + 0.15);
      return null;
    });
  }
  // The reel: the best segments of the whole match that fit in 30 s, the last ball
  // always among them, in the order they happened, then the end card.
  function choose() {
    const room = MAX_REEL - OUTRO;
    const final = segs.find((x) => x.final);
    const chosen = final ? [final] : [];
    let used = final ? final.len : 0;
    for (const x of segs.filter((x) => x !== final).sort((a, b) => b.score - a.score || b.n - a.n)) {
      if (used + x.len <= room) { chosen.push(x); used += x.len; }
    }
    return chosen.sort((a, b) => a.n - b.n);
  }
  // Seconds of work left at the end of the innings: the last ball's clip and line,
  // segments still to cut, the end card and the join.
  function estimate() {
    const busy = stage && stage.busy ? 4 : 0;
    const est = (live.size ? 6 : 0) + queue.length * 6 + busy + OUTRO + 2;
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
  // Two joins race: the server's (a lossless copy, a few seconds) and the browser's
  // own (the finished segments played back to back into one recording, as long as
  // the reel). Whichever finishes first is the reel; the other is stopped.
  async function serverJoin(parts, signal) {
    const type = MIME.split(";")[0];
    const r = await fetch("/api/reel", {
      method: "POST", body: new Blob(parts, { type }), signal,
      headers: { "Content-Type": type, "X-Parts": parts.map((b) => b.size).join(",") },
    });
    if (!r.ok) throw new Error(`join ${r.status}`);
    return r.blob();
  }
  async function browserJoin(parts, signal) {
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    const actx = new AC();
    actx.__bulbulNoTap = true;
    const dest = actx.createMediaStreamDestination();
    const stream = new MediaStream([...canvas.captureStream(30).getVideoTracks(), ...dest.stream.getAudioTracks()]);
    const rec = new MediaRecorder(stream, { mimeType: MIME, videoBitsPerSecond: 4_000_000 });
    const chunks = [];
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    const done = new Promise((r) => (rec.onstop = r));
    let v = null;
    const tick = setInterval(() => { if (v && v.videoWidth) { backdrop(ctx); cover(ctx, v); } }, 1000 / 30);
    const stopAll = () => { clearInterval(tick); if (v) v.pause(); if (rec.state !== "inactive") rec.stop(); actx.close().catch(() => {}); };
    signal.addEventListener("abort", stopAll, { once: true });
    try {
      if (actx.state === "suspended") await actx.resume().catch(() => {});
      rec.start(500);
      for (const part of parts) {
        if (signal.aborted) throw new Error("aborted");
        v = document.createElement("video");
        v.playsInline = true; v.preload = "auto";
        v.src = URL.createObjectURL(part);
        actx.createMediaElementSource(v).connect(dest);
        await new Promise((r) => { v.onloadeddata = r; v.onerror = r; setTimeout(r, 4000); });
        await v.play().catch(() => {});
        await new Promise((r) => { v.onended = r; signal.addEventListener("abort", r, { once: true }); setTimeout(r, 15000); });
        URL.revokeObjectURL(v.src);
      }
      if (signal.aborted) throw new Error("aborted");
      stopAll();
      await done;
      return new Blob(chunks, { type: MIME });
    } finally {
      clearInterval(tick);
    }
  }
  async function join(parts) {
    const stop = new AbortController();
    const first = (p) => p.then((blob) => { stop.abort(); return blob; });
    // Promise.any: the first that succeeds; only if both fail does this throw.
    return Promise.any([first(serverJoin(parts, stop.signal)), first(browserJoin(parts, stop.signal))]);
  }

  function start() {
    innings++;
    posterImage(); // loaded by the time the end card is drawn
    if (waiting) finish(waiting);
    queue = []; spare = []; segs = []; live.clear(); balls = 0; summary = null; reel = null; lines.clear();
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
    // The last ball's clip and line, then whatever is still being cut.
    const t = performance.now();
    while (performance.now() - t < LINE_WAIT + AFTER_BALL + 15000) {
      if (mine !== innings) return;
      if (!live.size && !queue.length && !(stage && stage.busy)) break;
      await sleep(250);
      pump();
    }
    if (mine !== innings) return;
    // Nothing big happened: the last couple of balls, so there is still a reel.
    if (!segs.length) {
      for (const c of spare.slice(-2)) {
        try { segs.push(await cutClip(c)); } catch (e) { console.warn("[reel] spare", e); }
        if (mine !== innings) return;
      }
    }
    if (!segs.length) { reel = { state: "failed" }; return renderButton(); }
    const outro = await cutOutro();
    if (mine !== innings) return;
    const chosen = choose();
    let blob;
    try {
      blob = await join([...chosen.map((x) => x.blob), outro]);
    } catch (e) {
      // Neither join worked: the best single moment is still worth sharing.
      console.warn("[reel] join", e);
      blob = [...chosen].sort((a, b) => b.score - a.score)[0].blob;
    }
    if (mine !== innings) return;
    // Done, often before the bar got near the top: a quick sweep to 100 % first.
    reel.progress = 100;
    renderButton();
    await sleep(450);
    if (mine !== innings) return;
    const name = `bulbul-flash-${summary.runs}-${summary.wickets}.${(blob.type || MIME).includes("webm") ? "webm" : "mp4"}`;
    reel = { state: "ready", file: new File([blob], name, { type: blob.type || "video/mp4" }) };
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
    centred(ctx, location.host + "/bulbul-flash", 1100, 36, "#7fd3ff", 700);
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

  // ---- Share and Download on the end card ----
  // Share opens the phone's share sheet (WhatsApp Status is one tap from there);
  // Download keeps the file, for the gallery or a desktop. Where a page cannot
  // share files, Download is the only button.
  let row = null, shareBtn = null, saveBtn = null;
  const canShareFiles = () => {
    try { return !!(navigator.canShare && navigator.canShare({ files: [new File([""], "x.mp4", { type: "video/mp4" })] })); } catch (_) { return false; }
  };
  // The game's own button (Kit.ts cta()): a coloured face on a ledge, its display font.
  function button(kind, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `k-cta k-cta--${kind}`;
    b.style.cssText = "flex:1 1 0;min-width:0";
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
  function renderButton() {
    if (!row) {
      row = document.createElement("div");
      row.id = "bb-share";
      row.style.cssText = "flex:1 1 100%;display:flex;gap:10px;margin:0 0 10px";
      shareBtn = button("share-wide", share);
      saveBtn = button("secondary", download);
      if (canShareFiles()) row.append(shareBtn);
      row.append(saveBtn);
    }
    if (!reel) { row.remove(); return; }
    const ready = reel.state === "ready";
    for (const b of [shareBtn, saveBtn]) b.disabled = !ready;
    if (ready) {
      saveBtn.firstChild.style.backgroundImage = "";
      label(shareBtn, "SHARE", "#mcard-share");
      label(saveBtn, row.contains(shareBtn) ? "DOWNLOAD" : "DOWNLOAD HIGHLIGHTS");
      saveBtn.style.display = shareBtn.style.display = "";
    } else {
      // One wide key, showing progress, until the file is ready.
      label(saveBtn, reel.state === "building" ? `HIGHLIGHTS ${reel.progress || 0}%` : "NO HIGHLIGHTS THIS TIME");
      // The key fills up behind its label as the reel is made.
      const pct = reel.state === "building" ? reel.progress || 0 : 0;
      saveBtn.firstChild.style.backgroundImage = pct
        ? `linear-gradient(90deg, rgba(255,255,255,.32) ${pct}%, transparent ${pct}%)` : "";
      // Disabled keys are dimmed by the game; this one is a progress bar, so it stays bright.
      saveBtn.style.opacity = "1";
      saveBtn.style.filter = "none";
      shareBtn.style.display = "none";
      saveBtn.style.display = "";
    }
    place();
  }
  function place() {
    const again = document.getElementById("again");
    if (!row || !reel || !again || row.parentElement === again.parentElement) return;
    again.parentElement.style.flexWrap = "wrap";
    again.parentElement.insertBefore(row, again);
  }
  setInterval(place, 400); // the end card is rebuilt each innings

  function download() {
    if (!reel || reel.state !== "ready") return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(reel.file); a.download = reel.file.name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  }
  async function share() {
    if (!reel || reel.state !== "ready") return;
    const text = `Maine Bulbul Flash Cricket mein ${summary.runs} banaye, Bulbul ki live commentary ke saath! Tum beat karo: ${location.origin}/bulbul-flash/`;
    try { await navigator.share({ files: [reel.file], text }); } catch (e) { if (e.name !== "AbortError") download(); }
  }

  window.bulbulReel = {
    runup, ball, line, pcm, heard, lineEnd, skip, start, end,
    debug: () => ({ queue, spare, segs: segs.map((x) => ({ n: x.n, score: x.score, len: x.len, final: x.final, kb: Math.round(x.blob.size / 1024) })), busy: !!(stage && stage.busy), reel, summary, MIME, lines: lines.size }),
  };
})();
