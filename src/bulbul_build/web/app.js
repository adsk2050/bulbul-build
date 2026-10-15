"use strict";
// One page for every mode: form is built from the mode's JSON schema,
// the result is a 9:16 card drawn on a canvas in time with the audio.

const $ = (id) => document.getElementById(id);
let current = null; // last result
let modes = [];

async function boot() {
  modes = await (await fetch("/api/modes")).json();
  const m = location.pathname.match(/^\/m\/([\w-]+)/);
  const mode = m && modes.find((x) => x.slug === m[1]);
  if (mode) showMode(mode); else showPicker();
}

function showPicker() {
  const el = $("picker");
  el.hidden = false;
  for (const m of modes) {
    const a = document.createElement("a");
    a.className = "tile";
    // The Lab is slides on the author's site, as on the home page.
    a.href = m.slug === "bulbul-lab" ? "https://adsk2050.github.io/blog/speech-you-can-hear.html" : `/m/${m.slug}`;
    const s = document.createElement("strong");
    s.textContent = m.name;
    const p = document.createElement("span");
    p.className = "muted";
    p.textContent = m.tagline;
    a.append(s, p);
    el.append(a);
  }
}

function resolve(schema, prop) {
  if (prop.$ref) return schema.$defs[prop.$ref.split("/").pop()];
  if (prop.allOf && prop.allOf[0].$ref) return { ...schema.$defs[prop.allOf[0].$ref.split("/").pop()], ...prop };
  if (prop.anyOf) return { ...prop.anyOf.find((x) => x.type !== "null"), title: prop.title, description: prop.description, default: prop.default };
  return prop;
}

function field(schema, name, raw) {
  const prop = resolve(schema, raw);
  const label = document.createElement("label");
  label.append(prop.title || name);
  let input;
  if (prop.enum) {
    input = document.createElement("select");
    const names = prop["x-labels"] || {};
    for (const v of prop.enum) {
      const o = document.createElement("option");
      o.value = v; o.textContent = names[v] || v;
      input.append(o);
    }
  } else if (prop.type === "boolean") {
    input = document.createElement("input");
    input.type = "checkbox";
  } else if (prop.type === "array" || (prop.maxLength || 0) > 120) {
    input = document.createElement("textarea");
    input.rows = prop.type === "array" ? 5 : 3;
  } else {
    input = document.createElement("input");
    input.type = prop.type === "integer" || prop.type === "number" ? "number" : "text";
    if (prop.maxLength) input.maxLength = prop.maxLength;
    if (prop.minimum !== undefined) input.min = prop.minimum;
    if (prop.maximum !== undefined) input.max = prop.maximum;
  }
  input.name = name;
  input.dataset.kind = prop.type || "string";
  if (prop.default !== undefined && prop.default !== null) {
    if (input.type === "checkbox") input.checked = !!prop.default;
    else input.value = Array.isArray(prop.default) ? prop.default.join("\n") : prop.default;
  }
  if (prop.examples) input.placeholder = String(prop.examples[0]);
  if ((schema.required || []).includes(name)) input.required = true;
  label.append(input);
  if (prop.description) {
    const small = document.createElement("small");
    small.textContent = prop.description;
    label.append(small);
  }
  return label;
}

function showMode(mode) {
  $("mode").hidden = false;
  $("mode-name").textContent = mode.name;
  $("mode-tagline").textContent = mode.tagline;
  document.title = `${mode.name} · Bulbul Build`;
  const form = $("form");
  for (const [name, prop] of Object.entries(mode.schema.properties)) form.append(field(mode.schema, name, prop));
  const btn = document.createElement("button");
  btn.textContent = "Bolo! 🔊";
  form.append(btn);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {};
    for (const el of form.elements) {
      if (!el.name) continue;
      const k = el.dataset.kind;
      if (el.type === "checkbox") body[el.name] = el.checked;
      else if (el.value === "") continue;
      else if (k === "integer") body[el.name] = parseInt(el.value, 10);
      else if (k === "number") body[el.name] = parseFloat(el.value);
      else if (k === "array") body[el.name] = el.value.split("\n").map((s) => s.trim()).filter(Boolean);
      else body[el.name] = el.value;
    }
    btn.disabled = true;
    $("status").textContent = "Bulbul is speaking…";
    try {
      const r = await fetch(`/api/${mode.slug}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Something went wrong");
      showResult(data);
      $("status").textContent = "";
    } catch (err) {
      $("status").textContent = err.message;
    } finally {
      btn.disabled = false;
    }
  });
}

function showResult(data) {
  current = data;
  current.usePhone = false;
  $("result").hidden = false;
  $("player").src = data.audio_url;
  $("phone-toggle").hidden = !data.phone_audio_url;
  drawCard(0);
  $("result").scrollIntoView({ behavior: "smooth" });
}

// ---- card ----------------------------------------------------------------

function wrap(ctx, text, maxWidth) {
  const words = text.split(/\s+/);
  const lines = [];
  let line = "";
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) { lines.push(line); line = w; } else line = test;
  }
  if (line) lines.push(line);
  return lines;
}

function drawCard(t) {
  const c = $("card"), ctx = c.getContext("2d");
  const card = current.card || {};
  const [c1, c2] = card.bg || ["#2b1055", "#e8590c"];
  const g = ctx.createLinearGradient(0, 0, 0, c.height);
  g.addColorStop(0, c1); g.addColorStop(1, c2);
  ctx.fillStyle = g; ctx.fillRect(0, 0, c.width, c.height);
  ctx.fillStyle = "#fff"; ctx.textAlign = "center";
  const font = (size, weight = 700) => `${weight} ${size}px "Noto Sans", "Noto Sans Devanagari", "Noto Sans Tamil", "Noto Sans Telugu", "Noto Sans Kannada", "Noto Sans Bengali", "Noto Sans Gujarati", "Noto Sans Gurmukhi", sans-serif`;
  if (card.kicker) { ctx.font = font(44, 400); ctx.globalAlpha = .85; ctx.fillText(card.kicker, 540, 200); ctx.globalAlpha = 1; }
  if (card.emoji) { ctx.font = font(220); ctx.fillText(card.emoji, 540, 520); }
  ctx.font = font(76);
  wrap(ctx, current.title, 940).forEach((l, i) => ctx.fillText(l, 540, 700 + i * 92));
  const cap = current.captions.find((x) => t >= x.start && t <= x.end + 0.25) || (t === 0 ? current.captions[0] : null);
  if (cap) {
    ctx.font = font(60, 400);
    const lines = wrap(ctx, cap.text, 920).slice(0, 8);
    const y0 = 1180 - (lines.length * 78) / 2;
    lines.forEach((l, i) => ctx.fillText(l, 540, y0 + i * 78));
  }
  ctx.font = font(36, 400); ctx.globalAlpha = .8;
  if (card.course_ref) { ctx.font = font(32, 400); wrap(ctx, card.course_ref, 900).slice(0, 2).forEach((l, i) => ctx.fillText(l, 540, 1700 + i * 40)); ctx.font = font(36, 400); }
  ctx.fillText(card.footer || "Voice: Sarvam Bulbul V4 Flash", 540, 1820);
  ctx.globalAlpha = 1;
}

function animate() {
  const p = $("player");
  drawCard(p.currentTime);
  if (!p.paused && !p.ended) requestAnimationFrame(animate);
}

$("player").addEventListener("play", () => requestAnimationFrame(animate));
$("play-card").addEventListener("click", () => { const p = $("player"); p.currentTime = 0; p.play(); });
$("phone-toggle").addEventListener("click", () => {
  current.usePhone = !current.usePhone;
  $("player").src = current.usePhone ? current.phone_audio_url : current.audio_url;
  $("phone-toggle").textContent = current.usePhone ? "🎧 Normal" : "📞 Phone line";
  $("player").play();
});

// ---- video + share -------------------------------------------------------

let audioCtx, srcNode;
async function recordVideo() {
  const p = $("player"), c = $("card");
  audioCtx = audioCtx || new AudioContext();
  srcNode = srcNode || audioCtx.createMediaElementSource(p);
  const dest = audioCtx.createMediaStreamDestination();
  srcNode.connect(dest); srcNode.connect(audioCtx.destination);
  const stream = new MediaStream([...c.captureStream(30).getVideoTracks(), ...dest.stream.getAudioTracks()]);
  const type = ["video/mp4;codecs=avc1,mp4a", "video/webm;codecs=vp9,opus", "video/webm"].find((t) => MediaRecorder.isTypeSupported(t));
  const rec = new MediaRecorder(stream, { mimeType: type });
  const chunks = [];
  rec.ondataavailable = (e) => chunks.push(e.data);
  const done = new Promise((res) => (rec.onstop = res));
  p.currentTime = 0;
  rec.start();
  await p.play();
  await new Promise((res) => p.addEventListener("ended", res, { once: true }));
  setTimeout(() => rec.stop(), 400);
  await done;
  srcNode.disconnect(dest);
  const ext = type.startsWith("video/mp4") ? "mp4" : "webm";
  return new File(chunks, `bulbul.${ext}`, { type: type.split(";")[0] });
}

$("make-video").addEventListener("click", async () => {
  $("status").textContent = "Recording the card… keep this tab open.";
  const file = await recordVideo();
  current.video = file;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(file); a.download = file.name; a.click();
  $("status").textContent = "Video saved.";
});

$("share").addEventListener("click", async () => {
  const text = `${current.share_text}\n${location.origin}${location.pathname}`;
  if (current.video && navigator.canShare && navigator.canShare({ files: [current.video] })) {
    try { await navigator.share({ files: [current.video], text }); return; } catch { /* fall through */ }
  }
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener");
});

boot();
