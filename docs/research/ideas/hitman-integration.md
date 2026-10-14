# Hitman Cricket integration (progress notes)

Source: https://github.com/ekcuttingchaidesign/Hitman-Cricket (by ekcuttingchaidesign,
no licence file; credited, not relicensed). TypeScript + three.js + Vite. Downloaded as a
zip of HEAD on 2026-10-15 into the session scratchpad (a clone outside the worktree is
blocked for the worktree agent).

## 2026-10-15: what the game is (from src/)

- Modes: Blast (classic: 30 balls, 3 wickets, 5 overs, score as many as you can),
  Test Survival (60 balls, 1 wicket, chase a drawn team score, injury meter) and
  Test Marathon (playtest, hidden on production). Our build shows only the Blast
  (`VITE_VERCEL_ENV=production`, no `VITE_SHOW_SURVIVE`).
- Input -> shot (`src/game/InputManager.ts`): keys A/W/D/S (or arrows), combos
  A+W long-on, W+D cover, S+A scoop, S+D reverse scoop (scoops need a full meter).
  Swipes: angle fan, left=LEG, up-left=LONG_ON, up=STRAIGHT, up-right=COVER_LONG_OFF,
  right=SQUARE_CUT, down=DEFEND. A left-hander mirrors left/right.
- Timing (`ShotResolver.ts`): delta = input time - ideal contact time (positive = LATE
  in the game's own sign). |delta| <= 40 PERFECT, 78 GOOD, 135 OK, 205 POOR, else MISS;
  quick styles (FAST, EXPRESS, YORKER) tighten by 0.82.
- Compatibility table line x shot decides whether the stroke suits the ball; < 0.55
  (SOLID_SHOT) skies it (caught 75%, else six). POOR timing skies it and is caught.
- Middled: PERFECT six, GOOD four, OK 1-3 along the ground.
- Deliveries (`DeliveryGenerator.ts`, `config/gameplay.ts`): style decides pace and
  length (NORMAL seam 122-138, FAST 142-158, EXPRESS 164-176, SLOWER 78-98, swing
  118-140, spin 82-96, YORKER 158-170 at the toes, SHORT bouncer 132-168). One spin
  over per Blast innings. Yorker after 3 sixes, slower ball after 4 quick balls,
  bouncer 13% chance.
- Bouncer: only a PERFECT pull (leg-side) scores (six); a cut at a wide one is judged
  on timing; anything else goes through to the keeper. Never bowled/caught off one.
- Confidence meter (Blast): six +28, four +22, three +16, two +12, beaten -18, wicket
  empties. Full meter unlocks the charge (drive a chargeable ball PERFECT/GOOD = six),
  slog sweep vs spin, and scoops.

## Hook points

- `Game.resolve()`: the outcome is computed here, at the moment the ball meets the
  bat (or passes it). Aerial balls are judged here too, but shown when they land; the
  event carries `in_air: true` so the commentator builds up and reveals the result last.
- `Game.start()`: innings start. `Game.end()`: innings end. Over ends: after
  `score.record` when balls % 6 == 0.
- `InputManager`: notes the raw input (swipe angle or keys) before calling shoot.

## Build and serving

- The repo's `vite.single.config.ts` still emits a separate 6.8 MB JS and 1.5 MB CSS
  with every asset as a data URI; the game `fetch`es its audio, and our CSP
  (`default-src 'self'`) blocks `fetch(data:)`. So we use a normal build with
  `base: './'` instead, served at `/hitman/` (trailing slash: the game resolves
  `avatars/...` and `lotties/...` against the page URL).
- `VITE_BOARD_API=https://board.invalid`: the boards, careers and name claims go to an
  origin our CSP blocks, so they fail at once and the game plays offline. Without it the
  game would POST to `/api/name` etc. on our server.
- Unreferenced public files (seven PNGs, two cover webps, ~10 MB) are dropped from the build.

## 2026-10-15: wiring and checks

- Served at `/hitman/` (307 from `/hitman`). CSP for `/hitman/*` adds `font-src 'self'`
  (the game bundles its Jaro font); no inline script needed.
- `hitman-voice.js` defines `window.bulbulCommentary`; it is a classic script after the
  game's module, so it exists before the first innings starts.
- Over and end events are held in the browser until the ball's line has been said (or
  6 s / 4 s pass), because `commentary.py` treats `over` and `end` as urgent and would
  cut the ball's line mid-sentence. A new ball drops a held over.
- First overlay was a strip at the top: it covered the game's scoreboard and its
  clickable credit sat over the sound/board/pause keys. Moved to the bottom, nothing
  in it takes a touch; the clickable credit is in the desktop side note and CREDITS.txt.
- Headless Chromium is a private window to the game, so it shows "You naughty you,
  play anyway" first; then "What's new" cards. A normal phone tab sees the name gate
  instead (name, kit, hand), and the name is sent as `state.batter`.
- Headless timing: real-time key presses land ~300 ms early because SwiftShader renders
  slowly; the check uses Playwright's fake clock, like the game's own `innings-check.mjs`.
- The repo's `.gitignore` ignores `*.mp3`; an exception keeps the game's 12 sound clips.

## 2026-10-15: verified, and what is left

- Headless check (socket stubbed in Playwright, nothing reached the server's socket or
  Sarvam): an innings sent start, hit, wicket, miss, over, end with full payloads;
  player habits filled in (timing, favourite shots/inputs, per-ball-kind record).
- Fixed: a ball left alone that bowled him said "through to the keeper".
- Suggested `commentary.py` changes (owned by the main session, not made here):
  1. Do not treat `over` as urgent: it cancels a line mid-sentence. The browser now
     holds it until the ball's line ends, but a server-side fix is cleaner.
  2. KIND_HINT for `wicket` ("dramatic") and `hit` should defer to `detail.in_air`:
     a caught or skied six is sent at bat-on-ball, ~2 s before it lands, and the line
     should reveal the result last. hitman.md says so, but the hint comes first.
  3. hitman.md is ~960 words (~1.4k tokens) in every system prompt; trim if LLM latency
     suffers.
- Not done: the desktop side note's QR still points at hitmancricket.in (the original).
  Survive and Marathon modes are hidden; events would still fire there (`?mode=SURVIVE`).
