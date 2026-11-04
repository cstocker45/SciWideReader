"""Render the ASCII-art icon set (terminal look) into extension/icons and store/."""
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = "/System/Library/Fonts/Menlo.ttc"
BG, FG = (13, 17, 23, 255), (63, 220, 138, 255)

# A page whose text fills the full width, with arrows pushing outwards.
ART = {
    128: [" .---. ",
          "<|===|>",
          " |===| ",
          "<|===|>",
          " '---' "],
    48:  [" .-. ",
          "<|=|>",
          " '-' "],
    32:  ["<=>"],
    16:  ["<>"],
}


def render(size, lines, scale=8):
    s = size * scale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.2), fill=BG)
    pad = s * (0.12 if size >= 48 else 0.06)
    cols, rows = max(map(len, lines)), len(lines)
    # biggest bold Menlo that fits the box
    fs = 4
    while True:
        f = ImageFont.truetype(FONT, fs + 2, index=1)
        cw = f.getlength("M")
        lh = (fs + 2) * 1.0
        if cw * cols > s - 2 * pad or lh * rows > s - 2 * pad:
            break
        fs += 2
    f = ImageFont.truetype(FONT, fs, index=1)
    cw, lh = f.getlength("M"), fs * 1.0
    x0 = (s - cw * cols) / 2
    y0 = (s - lh * rows) / 2
    text = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(text)
    for i, line in enumerate(lines):
        for j, ch in enumerate(line):
            d.text((x0 + j * cw + cw / 2, y0 + i * lh + lh / 2), ch, font=f, fill=FG, anchor="mm")
    if size >= 48:  # faint phosphor glow
        glow = text.filter(ImageFilter.GaussianBlur(s * 0.02))
        im.alpha_composite(Image.blend(Image.new("RGBA", (s, s), (0, 0, 0, 0)), glow, 0.6))
    im.alpha_composite(text)
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    out = ROOT / "extension" / "icons"
    for size, lines in ART.items():
        render(size, lines).save(out / f"icon{size}.png")
    render(128, ART[128]).save(ROOT / "store" / "icon128.png")
    # big preview for the README / site
    render(512, ART[128], scale=2).save(ROOT / "store" / "icon-preview.png")
    print("ok")
