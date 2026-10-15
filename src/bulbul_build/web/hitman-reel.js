"use strict";
// Highlight reel for Gully Bhaiya Cricket, built while the innings is played.
//
// Every ball is recorded in the browser from the bowler's run-up: the game's
// canvas and the game's own sound. Gully Bhaiya's voice is not taken from that
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
    // Sixes always; fours while there is plenty of room; wickets only as the ending
    // (the last ball). A reel of getting out is not one anybody posts.
    const runs = c.ball.detail.runs;
    c.final = !!summary;
    if (c.final || runs === 6 || (runs === 4 && (cut ? cut.used : 0) < FOURS_UNTIL)) queue.push(c);
    else { spare.push(c); spare = spare.slice(-3); }
    pump();
  }

  // ---- cutting the reel as the innings goes ----
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
    gain.gain.value = p.line ? 0.45 : 1; // the game's sound sits under Bhaiya
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

  function start() {
    innings++;
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
    reel = { state: "building", progress: 30 };
    renderButton();
    // The last ball's clip and line, then whatever is still queued.
    const t = performance.now();
    while (performance.now() - t < LINE_WAIT + AFTER_BALL + 2000) {
      if (mine !== innings) return;
      const pending = live.size || queue.length || (cut && cut.busy);
      if (!pending) break;
      await sleep(250);
      pump();
    }
    if (mine !== innings) return;
    // Nothing big happened: the last couple of balls, so there is still a reel.
    if (!cut || !cut.used) {
      for (const c of spare.slice(-2)) {
        const p = plan(c);
        if ((cut ? cut.used : 0) + p.len <= MAX_REEL - OUTRO) await play(cutter(), c, p);
      }
    }
    if (!cut || mine !== innings) { reel = { state: "failed" }; return renderButton(); }
    reel.progress = 80; renderButton();
    const c = cut;
    c.draw = () => outroCard(c.ctx);
    c.rec.resume();
    await sleep(OUTRO * 1000);
    const done = new Promise((r) => (c.rec.onstop = r));
    c.rec.stop();
    await done;
    clearInterval(c.tick); c.actx.close();
    if (mine !== innings) return;
    const name = `gully-bhaiya-${summary.runs}-${summary.wickets}.${EXT}`;
    reel = { state: "ready", file: new File([new Blob(c.chunks, { type: MIME })], name, { type: MIME.split(";")[0] }) };
    cut = null;
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
  function outroCard(ctx) {
    backdrop(ctx);
    const s = summary || { runs: 0, wickets: 0, balls: 0, name: "" };
    centred(ctx, "GULLY BHAIYA CRICKET", 250, 40, "#ffb347");
    if (s.name) centred(ctx, s.name, 360, 64, "#ffffff");
    centred(ctx, `${s.runs}/${s.wickets}`, 520, 140, "#ffffff", 900);
    centred(ctx, `${s.balls} balls`, 600, 36, "#cfe3f5", 600);
    centred(ctx, "Gully Bhaiya", 790, 76, "#ffffff");
    centred(ctx, "on Sarvam Bulbul Flash", 870, 44, "#ffb347");
    centred(ctx, `Can you beat ${s.runs}?`, 1020, 56, "#ffffff");
    centred(ctx, location.host + "/gully-bhaiya", 1110, 38, "#7fd3ff", 700);
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
    ctx.fillText("🎙️ Gully Bhaiya on Sarvam Bulbul Flash", W / 2, H - 60);
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
      label(shareBtn, "SHARE", "#mcard-share");
      label(saveBtn, row.contains(shareBtn) ? "DOWNLOAD" : "DOWNLOAD HIGHLIGHTS");
      saveBtn.style.display = shareBtn.style.display = "";
    } else {
      // One wide key, showing progress, until the file is ready.
      label(saveBtn, reel.state === "building" ? `HIGHLIGHTS ${reel.progress || 0}%` : "NO HIGHLIGHTS THIS TIME");
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
    const text = `Maine Gully Bhaiya Cricket mein ${summary.runs} banaye, Gully Bhaiya ki live commentary ke saath! Tum beat karo: ${location.origin}/gully-bhaiya/`;
    try { await navigator.share({ files: [reel.file], text }); } catch (e) { if (e.name !== "AbortError") download(); }
  }

  window.bulbulReel = {
    runup, ball, line, pcm, heard, lineEnd, skip, start, end,
    debug: () => ({ queue, spare, cut: cut && { used: cut.used, busy: cut.busy }, reel, summary, MIME, lines: lines.size }),
  };
})();
