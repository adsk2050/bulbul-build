# Art notes (Talking Bulbul sprites)

- 2026-10-14: gpt-image-2 rejects `background: transparent` (HTTP 400 "Transparent background is not supported for this model", no charge). Workaround: generate on flat chroma green #00FF00 and key it out locally with Pillow.
- bird_base (high, 1024x1024): 7024 output tokens ($0.21), more than the gpt-image-1 table suggests. Result: good, recognisable red-whiskered bulbul, 3/4 view facing viewer's left, beak closed, feet visible.
- uncle_base (high, 1024x1024): $0.21. Warm, round, white hair, moustache, round glasses, cream kurta. Skin reads a bit orange.
- Edits with a mask cost ~$0.06 each at medium (1024 image-in tokens + 1756 out). All bird and uncle edits came back at zero pixel shift (measured by best-shift search on the body), with only re-render noise (~14/765 mean diff), so variants are made by pasting only the changed region back onto the base (`paste` step): outside that region every variant is pixel-identical to the base.
- Uncle half/open/blink: clean. Bird half/open: clean; the wide-open beak gapes upward past the mask ellipse, so `paste` also takes any changed pixel inside the box. Bird blink: eyes become lines; the edit also redrew the cheek/whisker, but only the eye region is pasted.
- bird_covered: finger enters from the left edge, presses on the beak, eyes go wide. Body did not move.
- palm (edit with uncle_base as style reference, 1024x1536 medium, $0.05), bg (gen 1024x1536 medium, $0.04), uncle_sigh and uncle_surprised (face mask edits). Running total after 12 calls: $1.07.
- First try at sigh/surprised redrew the glasses (rectangular / oval). Re-ran with "keep the glasses perfectly round" in the prompt (`*_raw2`), which fixed it. Moustache and nose shape still vary a little in those two; they are separate poses, not lip-sync frames, so a small jump on switch is acceptable.
- Composition: the uncle base is only head and shoulders, so `build` extends each uncle sprite downward to 2080 px by repeating the bottom row (plain kurta) so his body reaches the canvas bottom. Placements are in `PLACE` in `scripts/make_art.py`; `make_art.py preview out.png <uncle> <bird>` renders a check image.
- Bird is placed at x=-12 so the finger stub in bird_covered starts at the canvas edge; if the bird is moved right, the finger's cut end becomes visible.
- Sprites over 600 KB are quantised to 256 colours with dithering (light speckle on skin, invisible at display scale). bg is blurred 2 px and quantised (440 KB).
- Final: 14 paid calls, $1.19.

## Second pass (2026-10-14, hand attached to the uncle)
- Correction: the first pass was 15 paid calls (not 14), $1.19.
- New base `uncle2_base` (edit of uncle_base as reference, high, 1024x1536, $0.17): waist-up, right forearm out, palm up, attached via the sleeve; left arm hanging. Face and style match well. palm.png, bird_covered.png and uncle_sigh.png are dropped (no sigh on the new base).
- Mouth/blink edits on the new base: clean, pasted back as before.
- Surprised with one big face mask redrew glasses, nose and moustache. Redone as two edits (eyes+brows mask, mouth mask) and combined; glasses still grow slightly in that sprite.
- Covering, first try: edit of the uncle WITH the bird composited in. Failed: the model turned the bulbul into a crow and put a "shush" finger on his own lips. Lessons: do not include the bird, avoid the word "shush".
- Covering, second try: no bird, a red target dot on the input, left-arm-only mask. Worked: left arm raised from the shoulder, index finger pointing left, hanging hand removed. Fingertip landed ~60 px off the dot, so the bird is moved instead: in the covered state bird_surprised is drawn at its `covered` rect (ducked: squashed ~16%, nudged right, feet still on the palm) so the beak sits under the finger.
- `hand_cover.png` = the left hand cut from uncle_cover_closed by an orange-skin mask plus the dark outline next to it (a plain diff mask pulled in kurta lines). Drawn above the bird.
- Arm paste uses only changed pixels grown by 25 px; with a smaller margin the old hanging arm's outline ghosted through.
- Second pass: 10 calls, $0.67. Total: 25 calls, $1.86.
