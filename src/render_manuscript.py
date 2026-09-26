"""
Render the manuscript Markdown to a print-ready PDF.

WHY THIS EXISTS
---------------
Zenodo accepts a preprint as a PDF, and the machine has no pandoc or LaTeX. fpdf2 is
pure Python, so this keeps the whole toolchain installable from requirements.txt with
no system packages.

This is a deliberately small renderer for the subset of Markdown used in
paper/manuscript.md: ATX headings, paragraphs, bullet and numbered lists, pipe
tables, blockquotes, horizontal rules, and inline bold/code. It is not a general
Markdown implementation and does not try to be.

LaTeX math is converted to readable plain text, because fpdf2 cannot typeset it.

Usage:
    python src/render_manuscript.py
    python src/render_manuscript.py --input paper/manuscript.md --output paper/manuscript.pdf
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from fpdf import FPDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# A4 in millimetres with 22 mm margins, which gives a measure suitable for a preprint.
PAGE_FORMAT = "A4"
MARGIN = 22
BODY_FONT = "Times"
BODY_SIZE = 10.5

# Characters fpdf2's core fonts (latin-1) cannot encode. Mapped rather than dropped
# so text does not lose meaning.
UNICODE_MAP = {
    "\u2013": "-", "\u2014": "-", "\u2012": "-", "\u2010": "-", "\u2011": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2026": "...", "\u00a0": " ",
    "\u2264": "<=", "\u2265": ">=", "\u00d7": "x", "\u2212": "-",
    "\u2192": "->", "\u2190": "<-", "\u2248": "~",
    "\u00b5": "u", "\u03b1": "alpha", "\u03b2": "beta", "\u03c7": "chi",
    "\u00b2": "^2", "\u00b3": "^3", "\u00bd": "1/2",
}

LATEX_SYMBOLS = {
    r"\mathbb{1}": "1",
    r"\times": "x",
    r"\le": "<=",
    r"\ge": ">=",
    r"\approx": "~",
}


def latin1_safe(text: str) -> str:
    """Convert to something the core PDF fonts can encode."""
    for original, replacement in UNICODE_MAP.items():
        text = text.replace(original, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def latex_to_text(latex: str) -> str:
    """Approximate LaTeX maths as readable plain text.

    Handles the constructs actually used in the manuscript: \\text{}, \\mathbb{1},
    and _{...} subscripts. Anything else is stripped of its braces so no LaTeX
    command survives into the PDF as visible noise.
    """
    text = latex.strip()
    for command, replacement in LATEX_SYMBOLS.items():
        text = text.replace(command, replacement)
    # \text{...} and similar single-argument commands keep their content.
    text = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", text)
    # Subscripts become underscore notation.
    text = re.sub(r"_\{([^{}]*)\}", r"_\1", text)
    text = re.sub(r"\^\{([^{}]*)\}", r"^\1", text)
    text = text.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\s+", " ", text).strip()


def preprocess(text: str) -> str:
    """Convert LaTeX and Markdown constructs fpdf2 cannot handle into plain text."""
    # Display maths blocks.
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: latex_to_text(m.group(1)), text, flags=re.S)
    # Inline maths.
    text = re.sub(r"\$(.+?)\$", lambda m: latex_to_text(m.group(1)), text)

    def render_link(match: re.Match) -> str:
        """Keep the visible text; add the target only when it differs.

        Relative links in this manuscript usually repeat their text, e.g.
        [outline.md](outline.md), which would otherwise render as
        "outline.md (outline.md)".
        """
        label, target = match.group(1), match.group(2)
        if label.strip() == target.strip():
            return label
        return f"{label} ({target})"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", render_link, text)
    # Bare angle-bracket URLs become plain URLs.
    text = re.sub(r"<((?:https?|mailto):[^>]+)>", r"\1", text)
    # Backticked code loses its ticks but keeps the text, which is what a reader needs.
    text = text.replace("`", "")
    return text


class ManuscriptPDF(FPDF):
    """A4 PDF with a running footer showing page numbers."""

    def footer(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font(BODY_FONT, "", 8)
        self.set_text_color(110)
        self.cell(0, 5, str(self.page_no()), align="C")
        self.set_text_color(0)


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_table_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:\-|]+\|", line.strip()))


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    """Read a pipe table starting at `start`. Returns (rows, next_index)."""
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and is_table_row(lines[index]):
        line = lines[index]
        if not is_table_separator(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
        index += 1
    return rows, index


def render(markdown_text: str, output: Path) -> None:
    pdf = ManuscriptPDF(format=PAGE_FORMAT, unit="mm")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(True, margin=18)
    pdf.add_page()

    text = preprocess(markdown_text)
    lines = text.splitlines()
    width = pdf.w - 2 * MARGIN

    index = 0
    while index < len(lines):
        raw = lines[index]
        line = raw.rstrip()
        stripped = line.strip()

        # Blank line.
        if not stripped:
            pdf.ln(2.2)
            index += 1
            continue

        # Horizontal rule.
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            pdf.ln(1)
            y = pdf.get_y()
            pdf.set_draw_color(190)
            pdf.line(MARGIN, y, MARGIN + width, y)
            pdf.ln(3)
            index += 1
            continue

        # Headings.
        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            sizes = {1: 16, 2: 13, 3: 11.5, 4: 10.5}
            pdf.ln(4 if level <= 2 else 2.5)
            pdf.set_font(BODY_FONT, "B", sizes.get(level, 10.5))
            if level == 1:
                pdf.set_text_color(0)
            pdf.multi_cell(width, 6.5, latin1_safe(title))
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            pdf.ln(1.2)
            index += 1
            continue

        # Tables.
        if is_table_row(stripped):
            rows, index = parse_table(lines, index)
            if rows:
                try:
                    pdf.set_font(BODY_FONT, "", 8.5)
                    with pdf.table(
                        width=width,
                        line_height=5,
                        first_row_as_headings=True,
                        borders_layout="HORIZONTAL_LINES",
                    ) as table:
                        for row in rows:
                            cells = table.row()
                            for cell_text in row:
                                cells.cell(latin1_safe(cell_text))
                    pdf.set_font(BODY_FONT, "", BODY_SIZE)
                    pdf.ln(2.5)
                except Exception as exc:  # noqa: BLE001 - degrade instead of failing
                    # A malformed table must not abort the whole document.
                    pdf.set_font(BODY_FONT, "", BODY_SIZE)
                    pdf.multi_cell(width, 5, latin1_safe(" ".join(rows[0])))
                    pdf.ln(1)
                    print(f"  [warn] table fallback used: {exc}")
            continue

        # Blockquote.
        if stripped.startswith(">"):
            quote = stripped.lstrip(">").strip()
            pdf.set_font(BODY_FONT, "I", BODY_SIZE - 0.5)
            pdf.set_text_color(70)
            pdf.multi_cell(width - 6, 5.2, latin1_safe(quote))
            pdf.set_text_color(0)
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            pdf.ln(1.5)
            index += 1
            continue

        # Bullet list.
        bullet = re.match(r"^[-*+]\s+(.*)$", stripped)
        if bullet:
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            pdf.multi_cell(width, 5.4, latin1_safe("  \u2022  " + bullet.group(1)), markdown=True)
            index += 1
            continue

        # Numbered list.
        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            pdf.multi_cell(
                width, 5.4,
                latin1_safe(f"  {numbered.group(1)}.  {numbered.group(2)}"),
                markdown=True,
            )
            index += 1
            continue

        # Paragraph: gather until a blank line or a structural line.
        paragraph = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate:
                break
            if re.match(r"^#{1,4}\s", candidate) or candidate.startswith(">"):
                break
            if is_table_row(candidate) or re.match(r"^[-*+]\s", candidate):
                break
            if re.match(r"^\d+\.\s", candidate):
                break
            if re.fullmatch(r"-{3,}", candidate):
                break
            paragraph.append(candidate)
            index += 1

        pdf.set_font(BODY_FONT, "", BODY_SIZE)
        joined = " ".join(paragraph)
        # fpdf2 reads __ as italic markup; identifiers with double underscores would
        # be mangled, so escape them before handing the text over.
        joined = joined.replace("__", "_\\_")
        pdf.multi_cell(width, 5.4, latin1_safe(joined), markdown=True)
        pdf.ln(1.8)

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))


# Patterns that mean "this text is a working note, not part of the paper". A deposit
# is permanent, so every one of these must be reported rather than quietly rendered.
DRAFT_MARKERS: list[tuple[str, str]] = [
    (r"\[TODO[^\]]*\]", "bracketed TODO"),
    (r"\*\*TODO[^*]*\*\*", "bold TODO marker"),
    (r"^## HOW TO FINISH THIS DRAFT", "author-facing instruction section"),
]


def find_draft_markers(markdown_text: str) -> list[tuple[str, int]]:
    """Report every working-note marker that would be visible in the PDF."""
    found: list[tuple[str, int]] = []
    for pattern, label in DRAFT_MARKERS:
        count = len(re.findall(pattern, markdown_text, flags=re.M))
        if count:
            found.append((label, count))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="paper/manuscript.md")
    parser.add_argument("--output", default="paper/manuscript.pdf")
    args = parser.parse_args()

    source = PROJECT_ROOT / args.input
    target = PROJECT_ROOT / args.output

    if not source.exists():
        raise SystemExit(f"Input not found: {source}")

    markdown_text = source.read_text(encoding="utf-8")
    render(markdown_text, target)

    print(f"Rendered {source.name} -> {target}")
    print(f"  size : {target.stat().st_size / 1024:.0f} KB")

    markers = find_draft_markers(markdown_text)
    if markers:
        total = sum(count for _, count in markers)
        print(
            f"\n  [WARN] {total} draft marker(s) will be visible in the PDF:"
        )
        for label, count in markers:
            print(f"           {count:>2} x {label}")
        print(
            "         This is a WORKING DRAFT, not a finished preprint. A Zenodo\n"
            "         record is permanent and cannot be deleted, so do not deposit\n"
            "         the PDF until these are gone.\n"
            "\n"
            "         Note that the author-facing instruction sections are meant to\n"
            "         be deleted before submission, not just the TODOs."
        )
    else:
        print("\n  [ OK ] No draft markers. The manuscript is presentation-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
