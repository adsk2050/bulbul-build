"use strict";
// Highlight reel for Hitman Cricket: every ball is recorded in the browser (the
// game's canvas plus all of its audio, Gully Bhaiya included), the best few are
// kept, and at the end of the innings they are cut into a 9:16 video with a
// score card and a "Gully Bhaiya on Sarvam Bulbul Flash" end card. The end card
// gets a Share button: the phone's share sheet (WhatsApp Status is one tap from
// there) or, where a page cannot share files, a download.
//
// hitman-voice.js calls window.bulbulReel.* as the match goes; nothing here
// talks to the server or costs anything.

(function () {
  if (!window.MediaRecorder || !HTMLCanvasElement.prototype.captureStream) return;

  const KEEP = 6;        // clips held while the innings goes on
  const IN_REEL = 4;     // clips in the reel
  const TAIL_MIN = 2500; // ms after the ball is decided, at least
  const TAIL_MAX = 6500; // and at most, if the line runs long
  const W = 720, H = 1280;

  const MIME = ["video/mp4;codecs=avc1,mp4a.40.2", "video/mp4", "video/webm;codecs=vp9,opus", "video/webm"]
    .find((m) => MediaRecorder.isTypeSupported(m));
  if (!MIME) return;
  const EXT = MIME.startsWith("video/mp4") ? "mp4" : "webm";

  // ---- every sound the page makes, mixed into one track ----
  // Any node connected to a context's speakers is also connected to a tap in that
  // context; the taps are mixed in a context of our own. This script loads before
  // the game creates its audio, so the game's bat, crowd and stumps are caught too.
  const taps = new Map();
  let mixCtx = null, mixDest = null;
  function mixer() {
    if (!mixCtx) {
      try {
        mixCtx = new (window.AudioContext || window.webkitAudioContext)();
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
    if (dest instanceof AudioDestinationNode && this.context !== mixCtx) {
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

  // ---- recording each ball ----
  function gameCanvas() {
    let best = null, area = 0;
    for (const c of document.querySelectorAll("#viewport canvas, #app canvas")) {
      const a = c.width * c.height;
      if (a > area && c.getClientRects().length) { best = c; area = a; }
    }
    return best;
  }
  let stream = null, streamCanvas = null;
  function recordStream() {
    const canvas = gameCanvas();
    if (!canvas) return null;
    if (canvas !== streamCanvas) {
      streamCanvas = canvas;
      stream = canvas.captureStream(30);
    }
    const tracks = [...stream.getVideoTracks()];
    const audio = mixer();
    if (audio) tracks.push(...audio.stream.getAudioTracks());
    return new MediaStream(tracks);
  }

  let clips = [];      // { blob, ball, line, score, n }
  let cur = null;      // the clip being recorded
  let balls = 0;
  let summary = null;  // { name, runs, wickets, balls }
  let reel = null;     // { state: 'building' | 'ready' | 'failed', file, progress }
  const byId = new Map();

  function worth(kind, d) {
    if (kind === "wicket") return d.how === "caught" || d.how === "caught behind" ? 6 : 5;
    if (d.runs === 6) return 7;
    if (d.runs === 4) return 4;
    if (d.runs > 0) return 1;
    return 0;
  }

  function stopClip() {
    if (!cur) return;
    const c = cur;
    cur = null;
    clearTimeout(c.timer);
    if (c.rec.state !== "inactive") c.rec.stop();
  }

  function runup() {
    stopClip();
    if (summary) return; // the innings is over
    const s = recordStream();
    if (!s) return;
    let rec;
    try { rec = new MediaRecorder(s, { mimeType: MIME, videoBitsPerSecond: 3_000_000 }); } catch (_) { return; }
    const c = { rec, chunks: [], ball: null, line: "", n: ++balls };
    rec.ondataavailable = (e) => e.data.size && c.chunks.push(e.data);
    rec.onstop = () => {
      if (!c.ball) return;
      const blob = new Blob(c.chunks, { type: MIME });
      clips.push({ blob, ball: c.ball, line: c.line, score: worth(c.ball.kind, c.ball.detail), n: c.n });
      // Keep the best few as the innings goes, so a long one does not eat memory.
      if (clips.length > KEEP) {
        const drop = clips.reduce((lo, x) => (x.score < lo.score || (x.score === lo.score && x.n < lo.n) ? x : lo));
        clips = clips.filter((x) => x !== drop);
      }
      if (summary && !cur) build();
    };
    rec.start(500);
    cur = c;
    c.timer = setTimeout(stopClip, 12000); // a clip that never got its ball
  }

  function ball(id, kind, detail, state) {
    if (!cur || cur.ball) return;
    cur.ball = { kind, detail, state };
    cur.decided = performance.now();
    byId.set(id, cur);
    clearTimeout(cur.timer);
    const c = cur;
    c.timer = setTimeout(() => cur === c && stopClip(), TAIL_MAX);
  }
  function line(id, text) { const c = byId.get(id); if (c) c.line = text; }
  function lineEnd(id) {
    const c = byId.get(id);
    if (!c || c !== cur) return;
    // Let the last words land, but never cut the ball itself short.
    const wait = Math.max(600, TAIL_MIN - (performance.now() - c.decided));
    clearTimeout(c.timer);
    c.timer = setTimeout(() => cur === c && stopClip(), wait);
  }

  function start() {
    stopClip();
    clips = []; balls = 0; summary = null; reel = null; byId.clear();
    renderButton();
  }
  function end(detail, state) {
    summary = {
      name: state.batter || "", runs: detail.runs ?? state.runs ?? 0,
      wickets: detail.wickets ?? state.wickets ?? 0, balls: detail.balls ?? state.balls ?? 0,
    };
    reel = { state: "building", progress: 0 };
    renderButton();
    if (!cur) build(); // otherwise the last clip's onstop builds it
  }

  // ---- the reel ----
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  function pick() {
    const good = clips.filter((c) => c.score > 0).sort((a, b) => b.score - a.score || b.n - a.n).slice(0, IN_REEL);
    const chosen = good.length >= 2 ? good : clips.slice(-3);
    return chosen.sort((a, b) => a.n - b.n);
  }

  function wrap(ctx, text, maxW) {
    const words = text.split(/\s+/), lines = [];
    let ln = "";
    for (const w of words) {
      const t = ln ? ln + " " + w : w;
      if (ctx.measureText(t).width > maxW && ln) { lines.push(ln); ln = w; } else ln = t;
    }
    if (ln) lines.push(ln);
    return lines;
  }
  function backdrop(ctx) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#0b1a2a"); g.addColorStop(1, "#13324d");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  const FONT = '"Noto Sans Devanagari", "Nirmala UI", system-ui, sans-serif';
  function centred(ctx, text, y, size, color, weight = 800) {
    ctx.font = `${weight} ${size}px ${FONT}`;
    ctx.fillStyle = color; ctx.textAlign = "center";
    wrap(ctx, text, W - 100).forEach((l, i) => ctx.fillText(l, W / 2, y + i * size * 1.2));
  }
  function introCard(ctx) {
    backdrop(ctx);
    const who = summary.name ? summary.name : "Batsman";
    centred(ctx, "HITMAN CRICKET", 330, 44, "#ffb347");
    centred(ctx, who, 520, 84, "#ffffff");
    centred(ctx, `${summary.runs}/${summary.wickets}`, 700, 150, "#ffffff", 900);
    centred(ctx, `${summary.balls} balls · highlights`, 820, 38, "#cfe3f5", 600);
    centred(ctx, "🎙️ live commentary by Gully Bhaiya", 1060, 34, "#cfe3f5", 600);
  }
  function outroCard(ctx) {
    backdrop(ctx);
    centred(ctx, "Gully Bhaiya", 380, 88, "#ffffff");
    centred(ctx, "on Sarvam Bulbul Flash", 480, 48, "#ffb347");
    centred(ctx, "⚡ Every ball, a live Hinglish line", 640, 36, "#cfe3f5", 600);
    centred(ctx, `Can you beat ${summary.runs}?`, 820, 64, "#ffffff");
    centred(ctx, location.host + "/hitman", 940, 40, "#7fd3ff", 700);
  }
  function overlay(ctx, clip) {
    const d = clip.ball.detail || {};
    const call = String(d.game_call || (clip.ball.kind === "wicket" ? "OUT!" : d.runs ? `${d.runs} RUN${d.runs > 1 ? "S" : ""}` : "DOT BALL"));
    const tag = `${d.ball ? String(d.ball).replace("over ", "Over ").replace(", ball ", ".") + " · " : ""}${call}`;
    ctx.font = `800 40px ${FONT}`;
    const tw = ctx.measureText(tag).width + 48;
    ctx.fillStyle = clip.ball.kind === "wicket" ? "rgba(200,40,40,.9)" : "rgba(255,140,40,.92)";
    ctx.beginPath(); ctx.roundRect((W - tw) / 2, 60, tw, 64, 32); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.fillText(tag, W / 2, 106);
    if (clip.line) {
      ctx.font = `700 34px ${FONT}`;
      const lines = wrap(ctx, clip.line, W - 120).slice(0, 4);
      const h = lines.length * 44 + 40, y = H - 150 - h;
      ctx.fillStyle = "rgba(10,20,32,.78)";
      ctx.beginPath(); ctx.roundRect(40, y, W - 80, h, 24); ctx.fill();
      ctx.fillStyle = "#fff";
      lines.forEach((l, i) => ctx.fillText(l, W / 2, y + 52 + i * 44));
    }
    ctx.font = `600 26px ${FONT}`; ctx.fillStyle = "rgba(255,255,255,.85)";
    ctx.fillText("🎙️ Gully Bhaiya on Sarvam Bulbul Flash", W / 2, H - 60);
  }
  function cover(ctx, v) {
    const vw = v.videoWidth, vh = v.videoHeight;
    if (!vw || !vh) return;
    const s = Math.max(W / vw, H / vh), dw = vw * s, dh = vh * s;
    ctx.drawImage(v, (W - dw) / 2, (H - dh) / 2, dw, dh);
  }

  async function build() {
    if (!reel || reel.state !== "building" || reel.started) return;
    reel.started = true;
    const chosen = pick();
    if (!chosen.length) { reel = { state: "failed" }; return renderButton(); }
    const token = reel;
    try {
      const canvas = document.createElement("canvas");
      canvas.width = W; canvas.height = H;
      const ctx = canvas.getContext("2d");
      const actx = new (window.AudioContext || window.webkitAudioContext)();
      await actx.resume();
      const dest = actx.createMediaStreamDestination();
      const out = new MediaStream([...canvas.captureStream(30).getVideoTracks(), ...dest.stream.getAudioTracks()]);
      const rec = new MediaRecorder(out, { mimeType: MIME, videoBitsPerSecond: 4_000_000 });
      const chunks = [];
      rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
      const done = new Promise((r) => (rec.onstop = r));
      let draw = () => introCard(ctx);
      let running = true;
      const loop = () => { if (!running) return; draw(); requestAnimationFrame(loop); };
      // A hidden tab stops animation frames; a timer keeps the frames coming.
      const tick = setInterval(() => running && draw(), 1000 / 30);
      loop();
      rec.start(500);
      const total = chosen.length + 2;
      const step = (i) => { token.progress = Math.round((i / total) * 100); renderButton(); };
      await sleep(1800); step(1);
      for (let i = 0; i < chosen.length; i++) {
        if (reel !== token) throw new Error("abandoned");
        const clip = chosen[i];
        const v = document.createElement("video");
        v.playsInline = true; v.src = URL.createObjectURL(clip.blob);
        actx.createMediaElementSource(v).connect(dest);
        await new Promise((r) => { v.onloadeddata = r; v.onerror = r; });
        draw = () => { backdrop(ctx); cover(ctx, v); overlay(ctx, clip); };
        await v.play().catch(() => {});
        await new Promise((r) => { v.onended = r; setTimeout(r, 15000); });
        URL.revokeObjectURL(v.src);
        step(i + 2);
      }
      draw = () => outroCard(ctx);
      await sleep(2400);
      running = false; clearInterval(tick);
      rec.stop(); await done; actx.close();
      if (reel !== token) return;
      const name = `hitman-${summary.runs}-${summary.wickets}.${EXT}`;
      reel = { state: "ready", file: new File([new Blob(chunks, { type: MIME })], name, { type: MIME.split(";")[0] }) };
    } catch (e) {
      if (reel === token) reel = { state: "failed" };
      console.warn("[reel]", e);
    }
    renderButton();
  }

  // ---- the Share button on the end card ----
  let btn = null;
  function renderButton() {
    if (!btn) {
      btn = document.createElement("button");
      btn.type = "button"; btn.id = "bb-share";
      btn.style.cssText = "flex:1 1 100%;margin:0 0 10px;padding:14px 18px;border:0;border-radius:16px;" +
        "background:#25D366;color:#06260f;font:800 18px/1.2 system-ui,sans-serif;cursor:pointer";
      btn.addEventListener("click", share);
    }
    if (!reel) { btn.remove(); return; }
    btn.disabled = reel.state !== "ready";
    btn.style.opacity = reel.state === "ready" ? "1" : ".75";
    btn.textContent = reel.state === "ready" ? "📲 Share highlights"
      : reel.state === "building" ? `🎬 Highlight reel ban rahi hai… ${reel.progress || 0}%`
      : "Highlights could not be made this time";
    place();
  }
  function place() {
    const again = document.getElementById("again");
    if (!btn || !reel || !again || btn.parentElement === again.parentElement) return;
    again.parentElement.style.flexWrap = "wrap";
    again.parentElement.insertBefore(btn, again);
  }
  setInterval(place, 400); // the end card is rebuilt each innings

  async function share() {
    if (!reel || reel.state !== "ready") return;
    const file = reel.file;
    const text = `Maine Hitman Cricket mein ${summary.runs} banaye, Gully Bhaiya ki live commentary ke saath! Tum beat karo: ${location.origin}/hitman/`;
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file], text }); return; } catch (e) { if (e.name === "AbortError") return; }
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(file); a.download = file.name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  }

  window.bulbulReel = { runup, ball, line, lineEnd, start, end, debug: () => ({ clips, cur, reel, summary, MIME }) };
})();
