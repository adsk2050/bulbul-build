"use strict";
// The home page's list of voice toys, after Bulbul Flash Cricket and Talking Bulbul.
// The Lab lives as slides on the author's site (pre-recorded clips, so it costs nothing to play).
const SLIDES = { "bulbul-lab": "https://adsk2050.github.io/blog/speech-you-can-hear.html" };

(async function () {
  const box = document.getElementById("demos");
  let modes = [];
  try { modes = await (await fetch("/api/modes")).json(); } catch (_) { return; }
  for (const m of modes) {
    const a = document.createElement("a");
    a.className = "tile demo";
    a.href = SLIDES[m.slug] || `/m/${m.slug}`;
    if (SLIDES[m.slug]) { a.target = "_blank"; a.rel = "noopener"; }
    const body = document.createElement("span");
    const s = document.createElement("strong");
    s.textContent = m.name;
    const p = document.createElement("span");
    p.className = "muted";
    p.textContent = m.tagline;
    body.append(s, p);
    a.append(body);
    box.append(a);
  }
})();
