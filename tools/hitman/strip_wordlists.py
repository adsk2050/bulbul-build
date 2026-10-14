"""Empty the upstream game's name-filter word lists in a built bundle.

Hitman Cricket ships arrays of offensive words to filter leaderboard names.
This repository is public and keeps no such lists, and our build has no
shared leaderboard, so the arrays become []. Run after every build:
    python tools/hitman/strip_wordlists.py src/bulbul_build/web/hitman
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# A JS array of plain string literals.
ARRAY = re.compile(r'\[(?:"[^"\\\n]{1,40}",){5,}"[^"\\\n]{1,40}"\]')
# Words that mark an array as a name filter (written as hex so this file holds none).
MARKERS = [bytes.fromhex(h).decode() for h in ("6675636b", "63687574697961", "61737368")]


def strip(text: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        if any(f'"{w}' in m.group(0) for w in MARKERS):
            count += 1
            return "[]"
        return m.group(0)

    return ARRAY.sub(repl, text), count


def main(folder: str) -> None:
    total = 0
    for path in Path(folder).rglob("*"):
        if path.suffix not in (".js", ".html", ".json") or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="surrogateescape")
        new, n = strip(text)
        if n:
            path.write_text(new, encoding="utf-8", errors="surrogateescape", newline="")
            print(f"{path}: emptied {n} word list(s)")
            total += n
    print(f"total: {total}")


if __name__ == "__main__":
    main(sys.argv[1])
