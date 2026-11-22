"""Original, reproducible red MP community icon for the unofficial PortableApps launcher.

No MEGA trademark artwork is copied. Generate all PortableApps menu sizes and
one Windows multiresolution ICO from the same vector-like drawing. The launcher
must embed byte-for-byte the same ICO that is staged in App/AppInfo.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

MASTER = 1024
SIZES = (16, 32, 75, 128, 256)
ICO_SIZES = (16, 32, 48, 64, 128, 256)


def draw_master() -> Image.Image:
    s = MASTER
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # An original rounded-square mark, rather than the official MEGA circle.
    # High-contrast crimson with a subtle diagonal tint improves 16px legibility.
    d.rounded_rectangle((42, 42, 982, 982), radius=224, fill=(164, 23, 48, 255))
    for i in range(0, 240, 8):
        shade = min(255, int(70 * (1 - i / 240)))
        d.rounded_rectangle((56 + i // 3, 56 + i // 3, 968 - i // 3, 968 - i // 3),
                            radius=max(70, 205 - i // 5), outline=(236, 57 + shade // 3, 76 + shade // 4, max(8, 90 - i // 3)), width=7)
    # The white angular M is deliberately constructed from asymmetric strokes;
    # it is NOT the MEGA logo artwork. Clear at the smallest PortableApps sizes.
    d.polygon([(208, 708), (208, 304), (305, 304), (509, 527),
               (713, 304), (808, 304), (808, 708), (700, 708),
               (700, 475), (512, 675), (493, 675), (316, 475), (316, 708)],
              fill=(255, 255, 255, 255))
    # Tiny portable marker: visible at large sizes, omitted on the 16px image.
    d.rounded_rectangle((676, 676, 900, 900), radius=76, fill=(45, 35, 52, 255), width=1)
    d.rounded_rectangle((704, 700, 869, 869), radius=57, outline=(255, 255, 255, 255), width=16)
    d.line((729, 731, 729, 833), fill=(255, 255, 255, 255), width=18)
    d.arc((728, 731, 836, 806), 260, 100, fill=(255, 255, 255, 255), width=18)
    return img


def generate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    master = draw_master()
    for size in SIZES:
        im = master.resize((size, size), Image.Resampling.LANCZOS)
        im.save(output / f'appicon_{size}.png')
    master.save(output / 'appicon.ico', format='ICO', sizes=[(n, n) for n in ICO_SIZES])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    generate(args.output)


if __name__ == '__main__':
    main()
