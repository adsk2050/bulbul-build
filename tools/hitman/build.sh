#!/usr/bin/env bash
# Rebuild src/bulbul_build/web/hitman/ from Hitman Cricket plus our commentary hooks.
#
#   tools/hitman/build.sh <path-to-Hitman-Cricket-checkout>
#
# The checkout must be the upstream source (https://github.com/ekcuttingchaidesign/Hitman-Cricket,
# HEAD of 2026-10-15) with `npm ci` done. The script applies bulbul-hooks.patch,
# copies in src/game/bulbul.ts, builds, and drops the public files the game never uses.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
game="$(cd "$1" && pwd)"
out="$repo/src/bulbul_build/web/hitman"

cd "$game"
if ! grep -q "game/bulbul" src/Game.ts; then
  patch -p1 < "$here/bulbul-hooks.patch"
fi
cp "$here/bulbul.ts" src/game/bulbul.ts
cp "$here/vite.bulbul.config.ts" vite.bulbul.config.ts
npx tsc --noEmit
# The boards, careers and name claims go to an origin our CSP blocks, so they fail
# at once and the game plays offline instead of POSTing to our own /api/*.
HITMAN_OUT="$out" VITE_BOARD_API=https://board.invalid npx vite build --config vite.bulbul.config.ts

# Public files nothing in the game references (about 10 MB).
cd "$out"
rm -f ./*.png leaderboard_cover.webp rivals_cover.webp play-qr.svg
cp "$here/CREDITS.txt" CREDITS.txt
# The upstream name filter carries offensive word lists; this repo keeps none.
python "$here/strip_wordlists.py" "$out"
du -sh "$out"
