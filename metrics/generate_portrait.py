"""
generate_portrait.py

Converts a photo into ASCII-art and injects it into dark_mode.svg and
light_mode.svg, replacing the existing portrait. Produces two polarities:
 - dark_mode.svg:  bright photo pixels -> dense characters  (light text on dark bg)
 - light_mode.svg: bright photo pixels -> sparse characters (dark text on light bg)
so the face reads correctly on either background.

Usage:
    python3 generate_portrait.py photo.jpg
    python3 generate_portrait.py photo.jpg --width 44 --height 25
    python3 generate_portrait.py photo.jpg --invert       # flip polarity if it looks negative
    python3 generate_portrait.py photo.jpg --contrast 1.6 # boost contrast for flat photos

The stats card to the right expects exactly 25 rows, so keep --height 25
unless you also adjust the SVG layout.
"""
import argparse
import re
import sys

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    sys.exit("Pillow is required. Install with:  python3 -m pip install pillow")

# Density ramp from most "ink" to least. Index 0 = darkest/most-dense character.
RAMP = "@%#*+=:-. "

SVG_FILES = {
    "dark_mode.svg": "dark",
    "light_mode.svg": "light",
}


def build_rows(img, width, height, invert, contrast):
    """Return a list of `height` strings, each `width` characters wide."""
    img = ImageOps.grayscale(img)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    # Auto-stretch levels so the full ramp is used regardless of photo exposure.
    img = ImageOps.autocontrast(img, cutoff=2)
    # High-quality downscale, then sharpen to keep facial features crisp at
    # small character grids.
    img = img.resize((width, height), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=160, threshold=2))
    px = img.load()

    steps = len(RAMP) - 1
    rows = []
    for y in range(height):
        line = []
        for x in range(width):
            v = px[x, y]  # 0 (black) .. 255 (white)
            if invert:
                v = 255 - v
            # v high (bright) -> ramp index 0 (@, most dense)
            idx = int((255 - v) / 255 * steps + 0.5)
            line.append(RAMP[idx])
        rows.append("".join(line))
    return rows


def rows_to_tspans(rows, start_y, line_height):
    out = []
    for i, row in enumerate(rows):
        y = round(start_y + i * line_height, 2)
        safe = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        out.append(f'<tspan x="15" y="{y}">{safe}</tspan>')
    return "\n".join(out)


def inject(svg_path, tspans):
    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()
    pattern = re.compile(r'(<text[^>]*class="ascii">)(.*?)(</text>)', re.DOTALL)
    if not pattern.search(svg):
        sys.exit(f'Could not find <text class="ascii"> block in {svg_path}')
    new_svg = pattern.sub(lambda m: m.group(1) + "\n" + tspans + "\n" + m.group(3), svg)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(new_svg)


def main():
    ap = argparse.ArgumentParser(description="Generate ASCII portrait into the SVGs.")
    ap.add_argument("image", help="path to your photo (jpg/png)")
    ap.add_argument("--width", type=int, default=40, help="portrait width in characters")
    ap.add_argument("--height", type=int, default=None,
                    help="rows; omit to auto-fit the photo's real proportions (no stretch)")
    ap.add_argument("--char-aspect", type=float, default=0.5,
                    help="monospace glyph width/height ratio; ~0.5 keeps the photo undistorted")
    ap.add_argument("--start-y", type=float, default=30, help="y of the first character row")
    ap.add_argument("--line-height", type=float, default=20, help="vertical px between rows")
    ap.add_argument("--invert", action="store_true",
                    help="flip light/dark polarity if the portrait looks like a negative")
    ap.add_argument("--contrast", type=float, default=1.4)
    args = ap.parse_args()

    img = Image.open(args.image)

    # Preserve the photo's real proportions. A character cell is taller than it
    # is wide (~0.5), so rows must be scaled by char_aspect to avoid stretching.
    if args.height:
        height = args.height
    else:
        w0, h0 = img.size
        height = max(1, round(args.width * args.char_aspect * (h0 / w0)))
    args.height = height

    # The character grid is identical in both files: the "ink" marks the
    # subject and the background stays empty. Only the SVG text *color* differs
    # between dark/light mode, which the SVGs already handle via their fill.
    rows = build_rows(img, args.width, args.height, args.invert, args.contrast)
    tspans = rows_to_tspans(rows, args.start_y, args.line_height)
    for svg_path, mode in SVG_FILES.items():
        inject(svg_path, tspans)
        print(f"Updated {svg_path}.")

    print("\nDone. Open dark_mode.svg / light_mode.svg to preview.")


if __name__ == "__main__":
    main()
