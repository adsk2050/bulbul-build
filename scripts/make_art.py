"""Generate Talking Bulbul sprites with the OpenAI Images API (gpt-image-2).

Run with:  uv run --with pillow --with httpx python scripts/make_art.py <cmd> ...

  gen  <out.png> --prompt TEXT [--size 1024x1536] [--quality medium] [--opaque]
  edit <out.png> --image base.png [--image ref2.png] [--mask mask.png] --prompt TEXT ...

Every call is logged to src/bulbul_build/web/art/COSTS.md with its token usage
and cost. A call is refused if its worst-case estimate would take the running
total above BUDGET_USD, or if MAX_CALLS calls have been made.

The key is read at runtime from the OPENAI_API_KEY environment variable, or
from the OPENAI_API_KEY line of the file named by OPENAI_API_KEY_FILE. It is
never printed or written anywhere.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "src" / "bulbul_build" / "web" / "art"
RAW = ART / "raw"
COSTS = ART / "COSTS.md"
ENV_FILE = Path(os.environ["OPENAI_API_KEY_FILE"]) if os.environ.get("OPENAI_API_KEY_FILE") else None
MODEL = "gpt-image-2"
BUDGET_USD = 2.39  # first pass $4 cap; second pass (hand fix) capped at $1.20 more over $1.19
MAX_CALLS = 30

# USD per token (OpenAI pricing page, read 2026-10-14).
PRICE_TEXT_IN = 5 / 1e6
PRICE_IMAGE_IN = 8 / 1e6
PRICE_OUT = 30 / 1e6

# Worst-case output tokens by quality (measured: high 1024x1024 = 7024).
WORST_OUT_TOKENS = {"low": 1000, "medium": 3000, "high": 11000}


def load_key() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"].strip()
    if ENV_FILE is None or not ENV_FILE.exists():
        sys.exit("set OPENAI_API_KEY or OPENAI_API_KEY_FILE")
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENAI_API_KEY not found")


def ledger() -> tuple[int, float]:
    """Return (calls so far, total USD so far) from COSTS.md."""
    if not COSTS.exists():
        return 0, 0.0
    rows = [r for r in COSTS.read_text(encoding="utf-8").splitlines() if re.match(r"^\| \d{4}-", r)]
    total = sum(float(r.split("|")[-3].strip().lstrip("$")) for r in rows)
    return len(rows), total


def estimate(quality: str, n_images_in: int) -> float:
    out = WORST_OUT_TOKENS[quality] * PRICE_OUT
    image_in = n_images_in * 6300 * PRICE_IMAGE_IN  # generous: high-fidelity input
    return out + image_in + 500 * PRICE_TEXT_IN


def record(name: str, quality: str, size: str, usage: dict) -> float:
    details = usage.get("input_tokens_details") or {}
    text_in = details.get("text_tokens", 0)
    image_in = details.get("image_tokens", 0)
    if not details:
        text_in = usage.get("input_tokens", 0)
    out = usage.get("output_tokens", 0)
    cost = text_in * PRICE_TEXT_IN + image_in * PRICE_IMAGE_IN + out * PRICE_OUT
    _, total = ledger()
    if not COSTS.exists():
        COSTS.write_text(
            "# Art generation costs\n\n"
            f"Model `{MODEL}`. Prices: text in $5/1M, image in $8/1M, image out $30/1M.\n"
            f"Budget: ${BUDGET_USD:.2f}, at most {MAX_CALLS} calls.\n\n"
            "| time | sprite | model | quality | size | text in | image in | out | cost | running total |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = (
        f"| {now} | {name} | {MODEL} | {quality} | {size} | {text_in} | {image_in} | {out} "
        f"| ${cost:.4f} | ${total + cost:.4f} |\n"
    )
    with COSTS.open("a", encoding="utf-8") as f:
        f.write(row)
    return total + cost


def call(args: argparse.Namespace, edit: bool) -> None:
    n_in = len(args.image or []) if edit else 0
    est = estimate(args.quality, n_in)
    calls, total = ledger()
    print(f"calls so far {calls}, spent ${total:.4f}, this call est <= ${est:.4f}")
    if calls >= MAX_CALLS:
        sys.exit("call limit reached")
    if total + est > BUDGET_USD:
        sys.exit("budget would be exceeded; refusing")
    headers = {"Authorization": f"Bearer {load_key()}"}
    fields = {
        "model": MODEL,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": "1",
    }
    if not args.opaque:
        fields["background"] = "transparent"
        fields["output_format"] = "png"
    with httpx.Client(timeout=300) as client:
        if edit:
            files = [("image[]", (Path(p).name, Path(p).read_bytes(), "image/png")) for p in args.image]
            if args.mask:
                files.append(("mask", ("mask.png", Path(args.mask).read_bytes(), "image/png")))
            r = client.post("https://api.openai.com/v1/images/edits", headers=headers, data=fields, files=files)
        else:
            body = dict(fields, n=1)
            r = client.post("https://api.openai.com/v1/images/generations", headers=headers, json=body)
    if r.status_code != 200:
        sys.exit(f"HTTP {r.status_code}: {r.text[:800]}")
    data = r.json()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(data["data"][0]["b64_json"]))
    usage = data.get("usage", {})
    new_total = record(out.stem, args.quality, args.size, usage)
    print(f"wrote {out}; usage {usage}; running total ${new_total:.4f}")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("gen", "edit"):
        s = sub.add_parser(name)
        s.add_argument("out")
        s.add_argument("--prompt", required=True)
        s.add_argument("--size", default="1024x1536")
        s.add_argument("--quality", default="medium", choices=list(WORST_OUT_TOKENS))
        s.add_argument("--opaque", action="store_true", help="no transparent background")
        if name == "edit":
            s.add_argument("--image", action="append", required=True)
            s.add_argument("--mask")
    args = p.parse_args()
    if args.prompt.startswith("@"):
        args.prompt = Path(args.prompt[1:]).read_text(encoding="utf-8")
    call(args, edit=args.cmd == "edit")


# ---------------------------------------------------------------- local steps
# These cost nothing: mask making, pasting an edited region back onto the base
# (so everything outside the region stays pixel-identical), and chroma keying.


def make_mask(out: str, size: tuple[int, int], box: tuple[int, int, int, int]) -> None:
    """OpenAI edit mask: opaque everywhere, transparent ellipse where edits may happen."""
    from PIL import Image, ImageDraw

    m = Image.new("RGBA", size, (0, 0, 0, 255))
    ImageDraw.Draw(m).ellipse(box, fill=(0, 0, 0, 0))
    m.save(out)


def paste_region(
    base: str, edited: str, box: tuple[int, int, int, int], feather: int, out: str, ellipse: bool = True
) -> None:
    """Copy changed pixels inside rectangle `box` from `edited` onto `base`.

    The region is the soft ellipse inscribed in `box`, plus any pixel in the box
    that changed noticeably (so an open beak that pokes past the ellipse is kept).
    Outside the box the base is untouched.
    """
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter

    b = Image.open(base).convert("RGB")
    e = Image.open(edited).convert("RGB").resize(b.size)
    x0, y0, x1, y1 = box
    ell = Image.new("L", b.size, 0)
    if ellipse:  # without it, only changed pixels are taken
        ImageDraw.Draw(ell).ellipse((x0 + feather, y0 + feather, x1 - feather, y1 - feather), fill=255)
    diff = np.abs(np.asarray(e, np.int16) - np.asarray(b, np.int16)).sum(2)
    changed = np.zeros(diff.shape, np.uint8)
    changed[y0:y1, x0:x1] = (diff[y0:y1, x0:x1] > 60) * 255
    # Without the ellipse, grow the changed area more so no edge of the old shape ghosts through.
    ch = Image.fromarray(changed).filter(ImageFilter.MaxFilter(9 if ellipse else 25))
    alpha = Image.fromarray(np.maximum(np.asarray(ell), np.asarray(ch)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(feather / 3))
    rect = Image.new("L", b.size, 0)
    ImageDraw.Draw(rect).rectangle(box, fill=255)
    alpha = Image.fromarray(np.minimum(np.asarray(alpha), np.asarray(rect)))
    Image.composite(e, b, alpha).save(out)


def chroma_key(src: str, out: str) -> None:
    """Remove the flat #00FF00 background; despill green fringes."""
    import numpy as np
    from PIL import Image

    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = g - np.maximum(r, b)  # ~255 on pure background, <=0 on most art
    alpha = np.clip((200 - green) / 120, 0, 1)  # >=200 transparent, <=80 opaque
    # Despill: cap green at the max of red/blue where it leaks.
    a[..., 1] = np.where(green > 0, np.maximum(r, b) + np.minimum(green, 0), g)
    rgba = np.dstack([a, alpha * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(out, optimize=True)


# Regions (x0, y0, x1, y1) where each variant may differ from its base.
# Uncle (second pass): uncle2_base is 1024x1536, waist-up, right palm held out.
U_MOUTH = (410, 415, 640, 555)
U_EYES = (395, 275, 665, 370)
U_BROWS_EYES = (395, 225, 665, 370)
U_ARM = (140, 560, 1024, 1536)  # raised left arm in uncle2_cover_raw2
HAND_BOX = (215, 670, 540, 880)  # the left hand, drawn above the bird
# Bird: bird_base is 1024x1024.
BIRD_BEAK = (225, 200, 470, 420)
BIRD_EYES = (315, 215, 485, 315)

# sprite: (base raw, [(edited raw, region, ellipse?), ...]) applied in order.
VARIANTS = {
    "uncle_closed": ("uncle2_base", []),
    "uncle_half": ("uncle2_base", [("uncle2_half_raw", U_MOUTH, True)]),
    "uncle_open": ("uncle2_base", [("uncle2_open_raw", U_MOUTH, True)]),
    "uncle_blink": ("uncle2_base", [("uncle2_blink_raw", U_EYES, True)]),
    "uncle_surprised": (
        "uncle2_base",
        [("uncle2_surp_eyes_raw", U_BROWS_EYES, True), ("uncle2_surp_mouth_raw", U_MOUTH, True)],
    ),
    # Covering pose: left arm raised, index finger out. Pixels outside the arm come from the base.
    "uncle_cover_closed": ("uncle2_base", [("uncle2_cover_raw2", U_ARM, False)]),
    "uncle_cover_half": (
        "uncle2_base",
        [("uncle2_cover_raw2", U_ARM, False), ("uncle2_half_raw", U_MOUTH, True)],
    ),
    "uncle_cover_open": (
        "uncle2_base",
        [("uncle2_cover_raw2", U_ARM, False), ("uncle2_open_raw", U_MOUTH, True)],
    ),
    "bird_closed": ("bird_base", []),
    "bird_half": ("bird_base", [("bird_half_raw", BIRD_BEAK, True)]),
    "bird_open": ("bird_base", [("bird_open_raw", BIRD_BEAK, True)]),
    "bird_blink": ("bird_base", [("bird_blink_raw", BIRD_EYES, True)]),
    "bird_surprised": ("bird_base", [("bird_surprised_raw", BIRD_EYES, True)]),
}

CANVAS = (1080, 1920)
# Uncle sprite (1024x1536) scaled 1.25 to fill the canvas height.
UNCLE_PLACE = (-100, 0, 1280, 1920)
# Bird placement in uncle-sprite pixels (x, y, scale_x, scale_y) of the 1024x1024 bird.
BIRD_ON_PALM = (-12, 472, 0.55, 0.55)
# Covered: bird ducks (squashed ~16%, widened 10%) and scoots right so its beak
# lands under the uncle's fingertip; feet stay on the palm.
BIRD_COVERED = (40, 551, 0.605, 0.46)
MAX_BYTES = 600_000


def uncle_to_canvas(px: float, py: float) -> list[int]:
    x, y, w, _ = UNCLE_PLACE
    s = w / 1024
    return [round(x + px * s), round(y + py * s)]


def bird_rect(p: tuple) -> dict:
    bx, by, sx, sy = p
    x, y = uncle_to_canvas(bx, by)
    s = UNCLE_PLACE[2] / 1024
    return {"x": x, "y": y, "w": round(1024 * sx * s), "h": round(1024 * sy * s)}


def save_small(img, out: Path) -> None:
    """Save PNG; quantise to 256 colours if it is over MAX_BYTES."""
    img.save(out, optimize=True)
    if out.stat().st_size > MAX_BYTES:
        img.quantize(256, method=2 if img.mode == "RGBA" else 0, dither=1).save(out, optimize=True)


def hand_overlay(cover_png: Path, base_png: Path, out: Path) -> None:
    """Cut the raised left hand out of the keyed covering sprite (drawn above the bird)."""
    import numpy as np
    from PIL import Image, ImageFilter

    cov = Image.open(cover_png).convert("RGBA")
    base = Image.open(base_png).convert("RGBA")
    diff = np.abs(np.asarray(cov, np.int16)[..., :3] - np.asarray(base, np.int16)[..., :3]).sum(2)
    c = np.asarray(cov, np.int16)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    # Skin (orange) that is new in this pose, closed to take in the nail and creases.
    skin = (r > 150) & (g > 70) & (g < 200) & (b < 130) & (r - b > 80) & (diff > 50)
    box = np.zeros(diff.shape, bool)
    x0, y0, x1, y1 = HAND_BOX
    box[y0:y1, x0:x1] = True
    sk = Image.fromarray(((skin & box) * 255).astype(np.uint8))
    sk = sk.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))
    # Add the dark outline that hugs the skin, but no light kurta pixels.
    near = np.asarray(sk.filter(ImageFilter.MaxFilter(11))) > 0
    dark = (r + g + b) < 360
    m = (np.asarray(sk) > 0) | (near & dark & box)
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    rgba = np.asarray(cov).copy()
    rgba[..., 3] = np.minimum(np.asarray(mi), rgba[..., 3])
    save_small(Image.fromarray(rgba, "RGBA"), out)


def build() -> None:
    """Paste variants, key the green, write sprites and manifest.json."""
    import json

    from PIL import Image, ImageFilter

    tmp, tmp2 = RAW / "_tmp.png", RAW / "_tmp2.png"
    sizes = {}
    for name, (base, edits) in VARIANTS.items():
        src = RAW / f"{base}.png"
        for edited, region, ellipse in edits:
            paste_region(str(src), str(RAW / f"{edited}.png"), region, 24, str(tmp2), ellipse)
            tmp2.replace(tmp)
            src = tmp
        chroma_key(str(src), str(tmp2))
        img = Image.open(tmp2).convert("RGBA")
        save_small(img, ART / f"{name}.png")
        sizes[name] = img.size
    for t in (tmp, tmp2):
        t.unlink(missing_ok=True)
    hand_overlay(ART / "uncle_cover_closed.png", ART / "uncle_closed.png", ART / "hand_cover.png")
    sizes["hand_cover"] = Image.open(ART / "hand_cover.png").size

    bg = Image.open(RAW / "bg_raw.png").convert("RGB")
    scale = CANVAS[1] / bg.height
    bg = bg.resize((round(bg.width * scale), CANVAS[1]), Image.LANCZOS)
    left = (bg.width - CANVAS[0]) // 2
    bg = bg.crop((left, 0, left + CANVAS[0], CANVAS[1]))
    # A light blur reads as depth of field and halves the PNG (wall texture is noisy).
    bg = bg.filter(ImageFilter.GaussianBlur(2)).quantize(256, dither=0)
    bg.save(ART / "bg.png", optimize=True)
    sizes["bg"] = bg.size

    ux, uy, uw, uh = UNCLE_PLACE
    on_palm, covered = bird_rect(BIRD_ON_PALM), bird_rect(BIRD_COVERED)
    sprites = {}
    for n, (w, h) in sizes.items():
        if n == "bg":
            place = {"x": 0, "y": 0, "w": CANVAS[0], "h": CANVAS[1]}
        elif n.startswith("uncle") or n == "hand_cover":
            place = {"x": ux, "y": uy, "w": uw, "h": uh}
        else:
            place = dict(on_palm)
        sprites[n] = {"file": f"{n}.png", "width": w, "height": h, **place}
    sprites["bird_surprised"]["covered"] = covered
    manifest = {
        "canvas": {"width": CANVAS[0], "height": CANVAS[1]},
        "draw_order": {
            "normal": ["bg", "uncle_*", "bird_*"],
            "covered": ["bg", "uncle_cover_*", "bird_surprised (at its 'covered' rect)", "hand_cover"],
        },
        "note": "x,y,w,h are canvas pixels; sprites may extend past the canvas edge on purpose. "
        "hand_cover is a full-size uncle layer (same rect as the uncle) holding only his left hand. "
        "In the covered state the bird ducks (squashed) so its beak sits under the fingertip. "
        "Anchors are canvas pixels.",
        "sprites": sprites,
        "anchors": anchors(on_palm),
    }
    (ART / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for n in sorted(sizes):
        print(n, sizes[n], (ART / f"{n}.png").stat().st_size // 1024, "KB")


def anchors(bird: dict) -> dict:
    def on_bird(px: float, py: float) -> list[int]:
        return [round(bird["x"] + px * bird["w"] / 1024), round(bird["y"] + py * bird["h"] / 1024)]

    return {
        "uncle_mouth": uncle_to_canvas(522, 455),
        "uncle_head_pivot": uncle_to_canvas(520, 560),  # neck
        "palm_centre": uncle_to_canvas(255, 950),  # top of the open palm, where the feet go
        "bird_beak_hinge": on_bird(395, 305),
        "bird_feet": on_bird(485, 860),  # squash/bob pivot
        "finger_tip": uncle_to_canvas(228, 705),
    }


def preview(out: str, uncle: str = "uncle_closed", bird: str = "bird_closed", state: str = "normal") -> None:
    import json

    from PIL import Image

    m = json.loads((ART / "manifest.json").read_text(encoding="utf-8"))
    canvas = Image.new("RGBA", CANVAS)
    layers = ["bg", uncle, bird] + (["hand_cover"] if state == "covered" else [])
    for n in layers:
        s = m["sprites"][n]
        r = s.get("covered", s) if (state == "covered" and n.startswith("bird")) else s
        img = Image.open(ART / s["file"]).convert("RGBA").resize((r["w"], r["h"]), Image.LANCZOS)
        canvas.paste(img, (r["x"], r["y"]), img)  # paste allows negative offsets
    canvas.convert("RGB").resize((540, 960)).save(out)


def local_main(argv: list[str]) -> None:
    cmd, *rest = argv
    if cmd == "mask":  # mask out.png W H x0 y0 x1 y1
        out, w, h, *box = rest
        make_mask(out, (int(w), int(h)), tuple(map(int, box)))
    elif cmd == "paste":  # paste base edited out x0 y0 x1 y1 feather
        base, edited, out, *nums = rest
        *box, feather = map(int, nums)
        paste_region(base, edited, tuple(box), feather, out)
    elif cmd == "key":  # key src out
        chroma_key(*rest)
    elif cmd == "build":  # paste, key, size every sprite; write manifest.json
        build()
    elif cmd == "preview":  # preview out.png [uncle] [bird] [normal|covered]
        preview(*rest)
    else:
        sys.exit(f"unknown local command {cmd}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("mask", "paste", "key", "build", "preview"):
        local_main(sys.argv[1:])
    else:
        main()
