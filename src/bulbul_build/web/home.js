"use strict";
// The home page's list of voice toys, after Bulbul Flash Cricket and Talking Bulbul.
(async function () {
  const box = document.getElementById("demos");
  let modes = [];
  try { modes = await (await fetch("/api/modes")).json(); } catch (_) { return; }
  for (const m of modes) {
    const a = document.createElement("a");
    a.className = "tile demo";
    a.href = `/m/${m.slug}`;
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
