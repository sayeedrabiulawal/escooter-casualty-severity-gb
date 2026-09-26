"""
Check that no ink falls inside the page margins of the rendered PDF.

WHY THIS EXISTS
---------------
fpdf2 lays text out from wherever the cursor currently is, and ``multi_cell``
defaults to ``new_x=XPos.RIGHT`` -- it leaves the cursor at the RIGHT edge of the
cell it just drew. A following block therefore starts from there and runs off the
page. The PDF still opens, the file size still looks right, and the text is simply
cut off or stranded in the margin. That is not something a reader can be expected
to catch, so it is checked mechanically instead.

This rasterises every page and fails if any dark pixel lands inside a margin band.
Text is allowed to reach the margin exactly; the tolerance absorbs the anti-aliased
pixel or two at a glyph's edge. The running page number is exempt, since it is
supposed to sit in the bottom margin.

Usage:
    python src/check_layout.py
    python src/check_layout.py --pdf paper/manuscript.pdf --scale 3

Exit code is 1 if any page intrudes into a margin, so this can gate a release.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MARGIN_MM = 22.0
FOOTER_MM = 16.0  # running page number lives inside the bottom margin by design
MM_TO_PT = 72 / 25.4
INK_THRESHOLD = 200  # 0 = black, 255 = white
TOLERANCE_PX = 1  # anti-aliasing slack at the margin boundary


def _penetration(band: np.ndarray, axis: int, from_far_edge: bool) -> float:
    """How far ink reaches into a margin band, in pixels.

    Depth is measured inward from the boundary of the text area, so 0 means the
    band is clear and any positive value is content that has crossed the margin.
    ``from_far_edge`` selects which end of the band that boundary sits at.
    """
    if band.size == 0 or not band.any():
        return 0.0
    reduced = band.any(axis=axis)
    positions = np.where(reduced)[0]
    if from_far_edge:
        # `reduced` has one entry per position along the band, so its length is the
        # extent to measure against -- not band.shape[axis], which is the other axis.
        return float(reduced.shape[0] - positions.min())
    return float(positions.max() + 1)


def measure(
    image, margin_pt: float, scale: float, footer_pt: float = 0.0
) -> dict[str, float]:
    """Margin penetration in points for each side of one rendered page.

    ``footer_pt`` excludes a strip at the foot of the page from the bottom check,
    because the running page number is deliberate furniture that sits inside the
    bottom margin by design.
    """
    arr = np.asarray(image)
    height, width = arr.shape
    edge = int(round(margin_pt * scale))
    footer = int(round(footer_pt * scale))
    ink = arr < INK_THRESHOLD
    slack_pt = TOLERANCE_PX / scale

    bands = {
        "left": (ink[:, :edge], 0, True),
        "right": (ink[:, max(width - edge, 0):], 0, False),
        "top": (ink[:edge, :], 1, True),
        "bottom": (ink[max(height - edge, 0): max(height - footer, 1), :], 1, False),
    }

    return {
        side: max(0.0, _penetration(band, axis, far) / scale - slack_pt)
        for side, (band, axis, far) in bands.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default="paper/manuscript.pdf")
    parser.add_argument("--margin-mm", type=float, default=MARGIN_MM)
    parser.add_argument(
        "--footer-mm",
        type=float,
        default=FOOTER_MM,
        help="strip at the foot of the page exempt from the bottom check",
    )
    parser.add_argument("--scale", type=float, default=2.0)
    args = parser.parse_args()

    target = PROJECT_ROOT / args.pdf
    if not target.exists():
        raise SystemExit(f"PDF not found: {target}")

    doc = pdfium.PdfDocument(str(target))
    margin_pt = args.margin_mm * MM_TO_PT
    footer_pt = args.footer_mm * MM_TO_PT

    print(f"{target.relative_to(PROJECT_ROOT)}  ({len(doc)} pages)")
    print(
        f"margin {args.margin_mm} mm = {margin_pt:.1f} pt, "
        f"footer strip {args.footer_mm} mm, render scale {args.scale}x"
    )
    print()

    failures: list[tuple[int, dict[str, float]]] = []
    header = f"{'page':>4} {'left':>8} {'right':>8} {'top':>8} {'bottom':>8}"
    print(header)
    print("-" * len(header))
    print("     (penetration into the margin, pt; 0.0 means clear)")

    for number, page in enumerate(doc, 1):
        image = page.render(scale=args.scale).to_pil().convert("L")
        sides = measure(image, margin_pt, args.scale, footer_pt)
        worst = max(sides.values())
        flag = "  <-- INTRUDES" if worst > 0 else ""
        if worst > 0:
            failures.append((number, sides))
            print(
                f"{number:>4} {sides['left']:>7.1f} {sides['right']:>8.1f} "
                f"{sides['top']:>8.1f} {sides['bottom']:>8.1f}{flag}"
            )

    print()
    if failures:
        print(f"[FAIL] {len(failures)} page(s) have ink inside the margins.")
        for number, sides in failures:
            worst_side = max(sides, key=lambda k: sides[k])
            print(f"         page {number}: worst is {worst_side} at {sides[worst_side]:.1f}pt")
        return 1

    print("[ OK ] No ink inside the margins on any page.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
