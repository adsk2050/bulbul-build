"use strict";
// Talking Bulbul. Mitthu parrots everything you say (your own recording, pitched
// up, no server), and Sharma uncle cuts in when he likes with Bulbul V4 Flash
// audio from the server. "Chacha, ..." talks to Chacha alone.
// Protocol: see src/bulbul_build/talk.py.

const $ = (id) => document.getElementById(id);
const BIRD_RATE = 1.35; // chipmunk replay: higher and faster
const VAD = { startFrames: 3, endFrames: 15, prerollFrames: 15, minFrames: 20, maxFrames: 500 };
const FRAME_16K = 320; // 20 ms at 16 kHz
const HOLD_AFTER_SPEECH_S = 0.4; // ignore the mic this long after anyone on screen talks

let ctx, ws, micNode;
let birdBus, uncleBus, birdLevel, uncleLevel;
const state = {
  speaking: false, // user, per our VAD
  speechFrames: 0, silentFrames: 0, floor: 0.01,
  preroll: [], // recent 16k frames for the start of speech
  recording: [], // full-rate Float32 chunks of the current utterance, for Mitthu
  prerollFull: [],
  turn: 0,
  lineTurn: -1,
  bird: null, // { src, gain, startedAt }
  birdBusyUntil: 0,
  uncleUntil: 0,
  uncleNext: 0, // when the next uncle chunk may start
  pendingCut: null, // barge that arrived before Mitthu started
  addressWho: null, // "mitthu" | "chacha" | null, from the server's live transcript
  waitingFinal: false, // speech ended before we knew who was addressed
  serverTurn: null, // the server's id for this turn, from its events
  tm: null, // this turn's timings (performance.now ms), sent to the server for the log
  pose: "idle", // idle | listening | repeating | covered
  poseUntil: 0,
  caption: "", captionWho: "", captionUntil: 0,
  partial: "",
  ttfa: null,
};
const fillerCache = new Map();

// ---- start -----------------------------------------------------------------

$("start").addEventListener("click", async () => {
  $("start-wrap").hidden = true;
  try {
    ctx = new AudioContext();
    await ctx.resume();
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 },
    });
    await ctx.audioWorklet.addModule("/static/mic-worklet.js");
    const src = ctx.createMediaStreamSource(stream);
    // Two taps on the mic: full band for Mitthu's replay, and low-passed at 7 kHz
    // for STT so the drop to 16 kHz does not fold hiss into the speech band.
    micNode = new AudioWorkletNode(ctx, "mic");
    src.connect(micNode);
    micNode.port.onmessage = (e) => onMic(e.data);
    let tap = src;
    for (let i = 0; i < 2; i++) { // two 2nd-order sections: a steep 4th-order low-pass
      const lp = ctx.createBiquadFilter();
      lp.type = "lowpass"; lp.frequency.value = 7000; lp.Q.value = 0.707;
      tap.connect(lp); tap = lp;
    }
    const sttNode = new AudioWorkletNode(ctx, "mic");
    tap.connect(sttNode);
    sttNode.port.onmessage = (e) => onSttSamples(e.data);

    birdBus = ctx.createGain(); uncleBus = ctx.createGain();
    birdLevel = meter(birdBus); uncleLevel = meter(uncleBus);
    birdBus.connect(ctx.destination); uncleBus.connect(ctx.destination);
    setupRecorder(src);
    connect();
    say("uncle", "बोलो बेटा, Mitthu सुन रहा है!", 3);
  } catch (err) {
    console.error(err);
    status("Microphone needed. Allow it and reload.");
    $("start-wrap").hidden = false;
  }
});

function connect() {
  ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/talk`);
  ws.binaryType = "arraybuffer";
  ws.onmessage = (e) => (typeof e.data === "string" ? onEvent(JSON.parse(e.data)) : onPcm(e.data));
  ws.onclose = () => { status("Disconnected. Reconnecting…"); setTimeout(connect, 1500); };
  ws.onopen = () => status("");
}

function status(t) { $("status").textContent = t; }

function meter(node) {
  const a = ctx.createAnalyser();
  a.fftSize = 512;
  node.connect(a);
  return { a, buf: new Float32Array(a.fftSize), v: 0 };
}

// ---- mic, VAD, 16 kHz frames ----------------------------------------------------

let resampleBuf = [];
let resamplePos = 0;
let frame16 = new Int16Array(FRAME_16K);
let frameFill = 0;
let rmsAcc = 0, rmsN = 0;

function onMic(samples) {
  if (state.speaking) state.recording.push(samples);
  else {
    state.prerollFull.push(samples);
    if (state.prerollFull.length > 40) state.prerollFull.shift(); // ~100 ms at 48 kHz
  }
}

function onSttSamples(samples) {
  const busy = ctx.currentTime < Math.max(state.birdBusyUntil, state.uncleUntil) + HOLD_AFTER_SPEECH_S;
  // Already low-passed below 8 kHz, so linear interpolation down to 16 kHz is enough.
  const ratio = ctx.sampleRate / 16000;
  for (const s of samples) resampleBuf.push(s);
  while (resamplePos + 1 < resampleBuf.length) {
    const i = Math.floor(resamplePos), f = resamplePos - i;
    const v = resampleBuf[i] * (1 - f) + resampleBuf[i + 1] * f;
    frame16[frameFill++] = Math.max(-32768, Math.min(32767, v * 32767));
    rmsAcc += v * v; rmsN++;
    if (frameFill === FRAME_16K) {
      onFrame(frame16, Math.sqrt(rmsAcc / rmsN), busy);
      frame16 = new Int16Array(FRAME_16K); frameFill = 0; rmsAcc = 0; rmsN = 0;
    }
    resamplePos += ratio;
  }
  const drop = Math.floor(resamplePos);
  resampleBuf = resampleBuf.slice(drop);
  resamplePos -= drop;
}

function onFrame(frame, rms, busy) {
  const loud = rms > Math.max(0.012, state.floor * 3);
  if (!state.speaking) {
    if (!loud) state.floor = state.floor * 0.95 + rms * 0.05;
    state.preroll.push(frame);
    if (state.preroll.length > VAD.prerollFrames) state.preroll.shift();
    if (busy) { state.speechFrames = 0; return; }
    state.speechFrames = loud ? state.speechFrames + 1 : 0;
    if (state.speechFrames >= VAD.startFrames) startSpeech();
    return;
  }
  send(frame);
  state.frames++;
  state.silentFrames = loud ? 0 : state.silentFrames + 1;
  if (state.silentFrames >= VAD.endFrames || state.frames >= VAD.maxFrames) endSpeech();
}

function send(frame) { if (ws && ws.readyState === 1) ws.send(frame.buffer.slice(0)); }

function mark(key, at = performance.now()) {
  if (state.tm && !(key in state.tm)) state.tm[key] = at;
}

// AudioContext time (seconds) to performance.now() ms.
function ctxToPerf(t) { return performance.now() + (t - ctx.currentTime) * 1000; }

function sendTiming() {
  const tm = state.tm;
  state.tm = null;
  if (!tm || !tm.speech_end || !ws || ws.readyState !== 1) return;
  const ms = {};
  for (const [k, v] of Object.entries(tm)) ms[k] = Math.round(v - tm.speech_end);
  ws.send(JSON.stringify({ type: "timing", turn: state.serverTurn, ms }));
}

function startSpeech() {
  sendTiming();
  state.tm = {};
  state.serverTurn = null;
  mark("speech_start");
  state.turnSettled = false;
  startClip();
  state.speaking = true;
  state.frames = 0; state.silentFrames = 0;
  state.turn++;
  state.pendingCut = null;
  state.addressWho = null;
  state.waitingFinal = false;
  state.partial = "";
  state.recording = state.prerollFull.slice();
  setPose("listening");
  if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "speech_start" }));
  for (const f of state.preroll) send(f);
  state.preroll = [];
}

function endSpeech() {
  mark("speech_end");
  state.speaking = false;
  state.speechFrames = 0;
  if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "speech_end" }));
  if (state.frames < VAD.minFrames) { setPose("idle"); return; }
  // Mitthu only parrots when called by name. If the name has not come
  // through the live transcript yet, wait for it (or the final text).
  // Mitthu parrots everything, unless the visitor was talking to Chacha.
  if (state.addressWho === "chacha") { setPose("idle"); flushPendingBarge(); }
  else birdRepeat();
}

function flushPendingBarge() {
  if (state.pendingCut) {
    const b = state.pendingCut;
    state.pendingCut = null;
    applyBarge(b);
  }
}

const GUARDRAIL = new Set(["abuse", "number"]);

function applyBarge(m) {
  // The hand goes over the beak even if Mitthu is already done.
  if (m.cover || GUARDRAIL.has(m.situation) || (m.cut && state.bird)) cutBird(m);
  else playFiller(m.filler);
}

// ---- Mitthu --------------------------------------------------------------------

function birdRepeat() {
  // Drop the trailing silence the VAD waited through.
  const chunks = state.recording;
  const total = chunks.reduce((n, c) => n + c.length, 0);
  const keep = Math.max(0, total - Math.floor(ctx.sampleRate * (VAD.endFrames * 0.02 - 0.08)));
  const buf = ctx.createBuffer(1, Math.max(1, keep), ctx.sampleRate);
  const data = buf.getChannelData(0);
  let off = 0;
  for (const c of chunks) {
    if (off >= keep) break;
    data.set(c.subarray(0, Math.min(c.length, keep - off)), off);
    off += c.length;
  }
  const src = ctx.createBufferSource();
  src.buffer = buf;
  src.playbackRate.value = BIRD_RATE;
  const gain = ctx.createGain();
  gain.gain.value = 1.6;
  src.connect(gain).connect(birdBus);
  const at = ctx.currentTime + 0.02;
  src.start(at);
  mark("mitthu_start", ctxToPerf(at));
  mark("mitthu_end_planned", ctxToPerf(at + buf.duration / BIRD_RATE));
  state.bird = { src, gain, startedAt: at };
  state.birdBusyUntil = at + buf.duration / BIRD_RATE;
  setPose("repeating", buf.duration / BIRD_RATE);
  src.onended = () => { if (state.bird && state.bird.src === src) state.bird = null; };
  if (state.pendingCut) {
    const b = state.pendingCut;
    state.pendingCut = null;
    // Let Mitthu get a few syllables out first: that is the joke.
    if (b.cut || b.cover || GUARDRAIL.has(b.situation)) setTimeout(() => cutBird(b), 450);
    else playFiller(b.filler);
  }
}

function stopBird() {
  const b = state.bird;
  if (!b) return;
  const t = ctx.currentTime;
  b.gain.gain.setTargetAtTime(0, t, 0.05);
  b.src.stop(t + 0.25);
  state.bird = null;
  state.birdBusyUntil = t + 0.25;
  setPose("idle");
}

function cutBird(barge) {
  const b = state.bird;
  mark("cover");
  if (b) {
    mark("mitthu_cut");
    const t = ctx.currentTime;
    b.gain.gain.setTargetAtTime(0, t, 0.015);
    b.src.stop(t + 0.08);
    state.bird = null;
    state.birdBusyUntil = t;
  }
  setPose("covered", 1.6);
  playFiller(barge.filler);
}

// ---- Sharma uncle ------------------------------------------------------------------

function onEvent(m) {
  if (m.turn != null) state.serverTurn = m.turn;
  if (m.type === "barge") mark("barge_received");
  if (m.type === "final") mark("final_received");
  if (m.type === "partial") state.partial = m.text;
  else if (m.type === "address") {
    state.addressWho = m.who;
    // "Chacha, ..." heard only after Mitthu started: let him trail off.
    if (m.who === "chacha" && state.bird) stopBird();
  } else if (m.type === "final") {
    state.partial = m.text;
    if (!state.bird && !state.speaking) flushPendingBarge();
  } else if (m.type === "barge") {
    if (state.speaking) state.pendingCut = m; // Mitthu has not started yet
    else applyBarge(m);
  } else if (m.type === "line") {
    state.lineTurn = m.turn;
    say("uncle", m.text, 6);
    if (m.audio) { playClip(m.audio); state.turnSettled = true; }
  } else if (m.type === "line_end") {
    state.turnSettled = true;
    if (m.ttfa_ms != null) state.ttfa = m.ttfa_ms;
  } else if (m.type === "quiet") {
    state.turnSettled = true;
  } else if (m.type === "error") {
    state.turnSettled = true;
    say("uncle", m.message, 4);
  }
}

async function clip(url) {
  if (!fillerCache.has(url)) {
    fillerCache.set(url, fetch(url).then((r) => r.arrayBuffer()).then((b) => ctx.decodeAudioData(b)));
  }
  return fillerCache.get(url);
}

function schedule(buffer) {
  const src = ctx.createBufferSource();
  src.buffer = buffer;
  src.connect(uncleBus);
  // Chacha never talks over Mitthu unless he cut him off (cutBird ends birdBusyUntil).
  const at = Math.max(ctx.currentTime + 0.02, state.uncleNext, state.birdBusyUntil + 0.15);
  src.start(at);
  mark("chacha_audio_start", ctxToPerf(at));
  // Keep the hand on the beak for as long as Chacha is talking.
  if (state.pose === "covered") state.poseUntil = Math.max(state.poseUntil, ctxToPerf(at + buffer.duration) + 300);
  state.tm && (state.tm.chacha_audio_end = ctxToPerf(at + buffer.duration));
  state.uncleNext = at + buffer.duration;
  state.uncleUntil = state.uncleNext;
}

async function playFiller(url) { if (url) schedule(await clip(url)); }
async function playClip(url) { schedule(await clip(url)); }

let pcmCarry = new Int16Array(0);
function onPcm(data) {
  const turn = new DataView(data).getUint32(0, true);
  if (turn !== state.lineTurn) return; // a stale line
  const fresh = new Int16Array(data, 4);
  const all = new Int16Array(pcmCarry.length + fresh.length);
  all.set(pcmCarry); all.set(fresh, pcmCarry.length);
  // Schedule in pieces of at least 60 ms so tiny chunks do not click.
  if (all.length < 1440 && ctx.currentTime < state.uncleNext - 0.05) { pcmCarry = all; return; }
  pcmCarry = new Int16Array(0);
  const buf = ctx.createBuffer(1, all.length, 24000);
  const ch = buf.getChannelData(0);
  for (let i = 0; i < all.length; i++) ch[i] = all[i] / 32768;
  schedule(buf);
}

// ---- captions and poses ---------------------------------------------------------

function say(who, text, seconds) {
  state.caption = text; state.captionWho = who;
  state.captionUntil = performance.now() + seconds * 1000;
}

function setPose(pose, seconds = 0) {
  state.pose = pose;
  state.poseUntil = seconds ? performance.now() + seconds * 1000 : 0;
}

// ---- drawing: sprites from /static/art (scripts/make_art.py) ---------------------

const cv = $("stage");
const g = cv.getContext("2d");
const W = cv.width, H = cv.height;
const art = { m: null, img: {} };
let blinkAt = { bird: performance.now() + 2500, uncle: performance.now() + 4000 };

(async function loadArt() {
  const m = await (await fetch("/static/art/manifest.json")).json();
  await Promise.all(Object.entries(m.sprites).map(([name, s]) => new Promise((ok) => {
    const im = new Image();
    im.onload = () => { art.img[name] = im; ok(); };
    im.onerror = ok;
    im.src = `/static/art/${s.file}`;
  })));
  art.m = m;
})();

function level(m) {
  m.a.getFloatTimeDomainData(m.buf);
  let s = 0;
  for (const x of m.buf) s += x * x;
  const rms = Math.sqrt(s / m.buf.length);
  const target = Math.min(1, rms * 9);
  m.v = target > m.v ? m.v + (target - m.v) * 0.6 : m.v + (target - m.v) * 0.18; // open fast, close slow
  return m.v;
}

function blinking(who, now) {
  const at = blinkAt[who];
  if (now < at) return false;
  if (now - at < 120) return true;
  blinkAt[who] = now + 2200 + Math.random() * 3800;
  return false;
}

function sprite(name) {
  const s = art.m.sprites[name];
  const im = art.img[name];
  if (s && im) g.drawImage(im, s.x, s.y, s.w, s.h);
}

function mouthFrame(prefix, open) {
  return open > 0.42 ? `${prefix}_open` : open > 0.14 ? `${prefix}_half` : `${prefix}_closed`;
}

function frame(now) {
  requestAnimationFrame(frame);
  if (state.poseUntil && now > state.poseUntil) setPose(state.speaking ? "listening" : "idle");
  const bird = birdLevel ? level(birdLevel) : 0;
  const uncle = uncleLevel ? level(uncleLevel) : 0;
  const t = now / 1000;
  g.clearRect(0, 0, W, H);
  if (!art.m) { g.fillStyle = "#f6e7cf"; g.fillRect(0, 0, W, H); return; }

  sprite("bg");
  const covered = state.pose === "covered";
  const breathe = Math.sin(t * 1.6);
  const BREATH = 0.004; // vertical stretch about the bottom edge

  // Sharma uncle, holding Mitthu on his own right palm. Mouth from his voice level.
  g.save();
  g.translate(0, H);
  g.scale(1, 1 + breathe * BREATH);
  g.translate(0, -H);
  g.filter = "saturate(0.86)"; // the generated skin reads a little orange
  let u = mouthFrame(covered ? "uncle_cover" : "uncle", uncle);
  if (!covered && u === "uncle_closed" && blinking("uncle", now)) u = "uncle_blink";
  sprite(u);
  g.filter = "none";
  g.restore();

  // Mitthu rides the palm (so he moves with the breathing), plus his own bob,
  // squash on loud syllables and head tilt while listening; pivot at his feet.
  const [fx, fy] = art.m.anchors.bird_feet;
  const palmLift = -(H - fy) * breathe * BREATH;
  if (covered) {
    // Chacha's left hand over the beak; Mitthu ducks under the finger.
    const s2 = art.m.sprites.bird_surprised, r = s2.covered;
    g.save();
    g.translate(0, palmLift);
    if (art.img.bird_surprised) g.drawImage(art.img.bird_surprised, r.x, r.y, r.w, r.h);
    g.restore();
    g.filter = "saturate(0.86)";
    sprite("hand_cover");
    g.filter = "none";
  } else {
    const pose = state.pose;
    const bob = pose === "repeating" ? Math.sin(t * 24) * 7 * bird : Math.sin(t * 2.4) * 3;
    const tilt = pose === "listening" ? 0.08 : Math.sin(t * 0.8) * 0.02;
    const squash = 1 + bird * 0.07;
    g.save();
    g.translate(fx, fy + palmLift + Math.min(0, bob));
    g.rotate(tilt);
    g.scale(1 / Math.sqrt(squash), squash);
    g.translate(-fx, -fy);
    let b = mouthFrame("bird", bird);
    if (b === "bird_closed" && blinking("bird", now)) b = "bird_blink";
    sprite(b);
    g.restore();
  }

  drawCaptions(now);
  drawBadge();
  maybeEndClip(now);
}
requestAnimationFrame(frame);

function wrap(text, maxW) {
  const words = text.split(/\s+/);
  const lines = [];
  let line = "";
  for (const w of words) {
    const test = line ? line + " " + w : w;
    if (g.measureText(test).width > maxW && line) { lines.push(line); line = w; } else line = test;
  }
  if (line) lines.push(line);
  return lines.slice(0, 5);
}

function bubble(text, x, y, color, fg, align, maxW = 820) {
  g.font = '600 54px "Baloo 2", "Noto Sans Devanagari", "Noto Sans Tamil", "Noto Sans Telugu", "Noto Sans Kannada", "Noto Sans Bengali", "Noto Sans Gujarati", "Noto Sans Gurmukhi", sans-serif';
  const lines = wrap(text, maxW);
  const h = lines.length * 70 + 50;
  const w = Math.max(...lines.map((l) => g.measureText(l).width)) + 70;
  const left = align === "left" ? x : x - w;
  g.fillStyle = color;
  g.beginPath(); g.roundRect(left, y, w, h, 36); g.fill();
  g.fillStyle = fg;
  lines.forEach((l, i) => g.fillText(l, left + 35, y + 80 + i * 70));
}

function drawCaptions(now) {
  if (state.partial && (state.speaking || state.pose === "repeating")) {
    bubble(state.partial, 60, 1700, "rgba(255,255,255,0.94)", "#3a2414", "left");
  }
  if (state.caption && now < state.captionUntil) {
    // On his kurta, right of Mitthu: clear of both faces.
    bubble(state.caption, W - 40, 1000, "rgba(200,16,46,0.94)", "#ffffff", "right", 560);
  }
}

function drawBadge() {
  g.font = '700 40px "Baloo 2", sans-serif';
  const txt = state.ttfa != null ? `⚡ Bulbul V4 Flash · ${state.ttfa} ms` : "⚡ Bulbul V4 Flash";
  const w = g.measureText(txt).width + 50;
  g.fillStyle = "rgba(58,36,20,0.85)";
  g.beginPath(); g.roundRect(W / 2 - w / 2, 60, w, 70, 35); g.fill();
  g.fillStyle = "#fff"; g.fillText(txt, W / 2 - w / 2 + 25, 108);
}

// ---- share clip: record each exchange, offer it as an MP4 ---------------------------

const rec = { recorder: null, chunks: [], startedAt: 0, blob: null, mime: "" };

function setupRecorder(micSource) {
  if (!window.MediaRecorder || !cv.captureStream) return;
  const dest = ctx.createMediaStreamDestination();
  birdBus.connect(dest);
  uncleBus.connect(dest);
  micSource.connect(dest); // the visitor's own voice belongs in the clip
  rec.stream = new MediaStream([...cv.captureStream(30).getVideoTracks(), ...dest.stream.getAudioTracks()]);
  rec.mime = ["video/mp4;codecs=avc1,mp4a", "video/mp4", "video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"]
    .find((t) => MediaRecorder.isTypeSupported(t)) || "";
}

function startClip() {
  if (!rec.stream || (rec.recorder && rec.recorder.state === "recording")) return;
  rec.chunks = [];
  rec.recorder = new MediaRecorder(rec.stream, rec.mime ? { mimeType: rec.mime, videoBitsPerSecond: 2_500_000 } : {});
  rec.recorder.ondataavailable = (e) => { if (e.data.size) rec.chunks.push(e.data); };
  rec.recorder.onstop = () => {
    rec.blob = new Blob(rec.chunks, { type: rec.recorder.mimeType || rec.mime || "video/webm" });
    $("share").hidden = false;
    $("share").disabled = false;
  };
  rec.recorder.start(250);
  rec.startedAt = performance.now();
}

function maybeEndClip(now) {
  const r = rec.recorder;
  if (!r || r.state !== "recording" || state.speaking) return;
  const audioDone = ctx.currentTime > Math.max(state.uncleUntil, state.birdBusyUntil) + 1.0;
  if ((state.turnSettled && audioDone) || now - rec.startedAt > 25000) { r.stop(); sendTiming(); }
}

$("share").addEventListener("click", async () => {
  if (!rec.blob) return;
  const btn = $("share");
  btn.disabled = true;
  btn.textContent = "⏳ Making video…";
  try {
    const r = await fetch("/api/clip", { method: "POST", headers: { "Content-Type": rec.blob.type.split(";")[0] }, body: rec.blob });
    if (!r.ok) throw new Error(`clip ${r.status}`);
    const { url } = await r.json();
    const file = new File([await (await fetch(url)).blob()], "talking-bulbul.mp4", { type: "video/mp4" });
    const text = "Mitthu ne mujhe repeat kiya, Chacha ne daant diya 😂 Bulbul V4 Flash pe bana: ";
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], text: text + location.origin + "/talk" });
    } else {
      const a = document.createElement("a");
      a.href = url; a.download = "talking-bulbul.mp4";
      document.body.append(a); a.click(); a.remove();
    }
  } catch (err) {
    if (err.name !== "AbortError") { console.error(err); status("Could not make the video. Try again?"); }
  }
  btn.textContent = "📤 Share this";
  btn.disabled = false;
});

// Preview a pose without talking: /talk#pose=covered (or listening, repeating).
const previewPose = location.hash.match(/pose=(\w+)/);
if (previewPose) setPose(previewPose[1], 3600);
const previewSay = location.hash.match(/say=([^&]+)/);
if (previewSay) say("uncle", decodeURIComponent(previewSay[1]), 3600);
