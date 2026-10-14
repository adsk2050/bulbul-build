# The five kits

    avatar_7.webp   pink, batter in a helmet
    avatar_1.webp   blue, curly hair
    avatar_2.webp   purple, beard and glasses
    avatar_3.webp   orange
    avatar_6.webp   teal, batter in a helmet

That order is the kit order, and it is recorded in `src/config/board.ts` — each
entry names its file and carries a colour sampled off the ring in that picture.
So a replacement picture only has to keep its file name, and a new one only has
to be named there. Nothing is renamed to match an index, which is why the gap in
the numbering costs nothing.

They are drawn at 44 px in the picker on the innings-end card and 28 px in a
board row, so 160 px square is comfortably enough for a high-density screen.

They arrived as PNG and were converted to WebP at quality 82, which took the
set from 221 KB to 45 KB with the alpha channel bit-identical, so the round
edges are unchanged. Replacements can be any format the browser reads &mdash;
only the file name recorded in `src/config/board.ts` has to match.

Nothing breaks if one fails to load: each kit draws its picture over a disc of
that picture's own ring colour, and a picture that will not load takes itself
off the page and leaves the disc. In a board row the player's name is written
beside it either way. There is a test for that.

These are served as files rather than bundled, which is why they live here in
`public/` and not in `src/assets/` — it is what lets the game build and run
whether or not they are present.
