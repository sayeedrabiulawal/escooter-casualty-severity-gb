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

Pandoc-style citations such as [@key] or [@key1; @key2] are resolved against
paper/references.bib into author-year text, and a reference list is generated
from the works actually cited. A key that is missing from the .bib renders as
?key? so a broken citation is visible rather than silent.

LaTeX math is converted to readable plain text, because fpdf2 cannot typeset it.

Usage:
    python src/render_manuscript.py
    python src/render_manuscript.py --input paper/manuscript.md --output paper/manuscript.pdf
"""

from __future__ import annotations

import argparse
import html
import re
import unicodedata
from pathlib import Path

from fpdf import FPDF, XPos, YPos
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# A4 in millimetres with 22 mm margins, which gives a measure suitable for a preprint.
PAGE_FORMAT = "A4"
MARGIN = 22
BODY_FONT = "Times"
BODY_SIZE = 10.5

# Figures are drawn at the full text width unless that would make them taller than
# this, in which case the height is capped and the width reduced to match. A figure
# taller than the text area would be split across pages by fpdf2, which is worse than
# a slightly smaller image.
FIGURE_MAX_HEIGHT_MM = 172.0

# Characters fpdf2's core fonts cannot encode, mapped rather than dropped so text does
# not lose meaning. latin-1 covers U+00A0-U+00FF, and the core Times font has real
# glyphs for that range: superscripts and the multiplication sign are deliberately NOT
# listed here, because mapping them would turn "pseudo-R\u00b2" into "pseudo-R^2" and
# "mode \u00d7 speed" into "mode x speed". Verified by rendering both and inspecting the
# output rather than assuming the range was unsupported.
UNICODE_MAP = {
    "\u2013": "-", "\u2014": "-", "\u2012": "-", "\u2010": "-", "\u2011": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2026": "...", "\u00a0": " ", "\u2022": "-", "\u2032": "'",
    "\u2033": '"',
    "\u2264": "<=", "\u2265": ">=", "\u2212": "-",
    "\u2192": "->", "\u2190": "<-", "\u2248": "~",
    "\u03b1": "alpha", "\u03b2": "beta", "\u03c7": "chi",
    "\u00bd": "1/2",
}

LATEX_SYMBOLS = {
    r"\mathbb{1}": "1",
    r"\times": "x",
    r"\le": "<=",
    r"\ge": ">=",
    r"\approx": "~",
}


def latin1_safe(text: str) -> str:
    """Convert to something the core PDF fonts can encode.

    A character that latin-1 cannot represent but whose accented letters can be
    decomposed (e.g. Polish n-acute) is folded to its base letter rather than
    replaced with "?", so author names survive with a diacritic lost instead of
    being mangled.
    """
    for original, replacement in UNICODE_MAP.items():
        text = text.replace(original, replacement)
    out: list[str] = []
    for char in text:
        try:
            char.encode("latin-1")
        except UnicodeEncodeError:
            folded = unicodedata.normalize("NFKD", char)
            folded = "".join(c for c in folded if not unicodedata.combining(c))
            out.append(folded.encode("latin-1", errors="replace").decode("latin-1"))
        else:
            out.append(char)
    return "".join(out)


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


def plain_emphasis(text: str) -> str:
    """Drop Markdown emphasis markers in contexts where fpdf2 markup is off.

    Table cells are drawn without markdown=True, so a stray **Bold** would reach
    the page as literal asterisks. Single underscores are left untouched because
    they appear in identifiers such as vehicle_type.
    """
    return text.replace("**", "")


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

    # The lookbehind is essential: image syntax is ![caption](path), which this
    # pattern would otherwise match as a link and rewrite into plain text, so the
    # figure line would never reach the render loop as an image. It cost a silent
    # failure once already, where the PDF rendered with no figures in it.
    text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", render_link, text)
    # Bare angle-bracket URLs become plain URLs.
    text = re.sub(r"<((?:https?|mailto):[^>]+)>", r"\1", text)
    # Backticked code loses its ticks but keeps the text, which is what a reader needs.
    text = text.replace("`", "")
    return text


# ---------------------------------------------------------------------------
# Citation resolution.
#
# The manuscript cites with Pandoc-style keys, e.g. [@shichman2022emergency] or
# [@a2020x; @b2021y]. There is no pandoc or LaTeX on this machine, and leaving the
# raw keys in the PDF would make the preprint unpublishable. They are therefore
# resolved here from paper/references.bib into author-year text, and a reference
# list is generated from exactly the works that are cited -- never from the whole
# .bib file, because an uncited entry in a reference list is an error.
#
# A key that is not in the .bib is rendered as ?key? rather than dropped, so a
# broken citation is visible in the PDF instead of silently disappearing.
# ---------------------------------------------------------------------------

BIB_PATH = "paper/references.bib"

# Only these field names are read; anything else in an entry is ignored. Restricting
# the set prevents a stray "=" inside a value from being mistaken for a field name.
BIB_FIELDS = {
    "author", "editor", "title", "year", "journal", "booktitle", "publisher",
    "volume", "number", "pages", "doi", "url", "howpublished", "note", "type",
    "school", "institution",
}

CITATION_RE = re.compile(r"\[([^\]]*@[^\]]+)\]")


def _clean(value: str) -> str:
    """Strip BibTeX braces and escapes from a field value."""
    value = value.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    value = value.replace("{", "").replace("}", "")
    # Crossref returns HTML-escaped ampersands, which must not reach the page as
    # "&amp;". unescape also covers &lt;, &gt;, &quot; and numeric references.
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _parse_bib_fields(body: str) -> dict[str, str]:
    """Read ``name = {value}`` pairs from a single BibTeX entry body."""
    fields: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*", body):
        name = match.group(1).lower()
        if name not in BIB_FIELDS:
            continue
        cursor = match.end()
        if cursor < len(body) and body[cursor] == "{":
            depth = 1
            walk = cursor + 1
            while walk < len(body) and depth > 0:
                if body[walk] == "{":
                    depth += 1
                elif body[walk] == "}":
                    depth -= 1
                walk += 1
            fields[name] = body[cursor + 1:walk - 1].strip()
    return fields


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    """Parse a BibTeX file into ``{key: {field: value}}``."""
    entries: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        key = match.group(2)
        start = match.end()
        depth = 1
        walk = start
        while walk < len(text) and depth > 0:
            if text[walk] == "{":
                depth += 1
            elif text[walk] == "}":
                depth -= 1
            walk += 1
        entries[key] = _parse_bib_fields(text[start:walk - 1])
    return entries


def _split_author_names(raw: str) -> list[tuple[str, str]]:
    """Return ``[(surname, forename), ...]``.

    A value wrapped in a second pair of braces is a corporate author and is kept
    whole, so ``{{Department for Transport}}`` stays one name.
    """
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("{") and raw.endswith("}"):
        return [(raw[1:-1].strip(), "")]
    people: list[tuple[str, str]] = []
    for name in raw.split(" and "):
        name = name.strip()
        if not name:
            continue
        if name.startswith("{") and name.endswith("}"):
            people.append((name[1:-1].strip(), ""))
        elif "," in name:
            surname, forename = name.split(",", 1)
            people.append((surname.strip(), forename.strip()))
        else:
            parts = name.split()
            people.append((parts[-1], " ".join(parts[:-1])))
    return people


def _initials(forename: str) -> str:
    """``Jingjing`` -> ``J.``; ``A.H.`` is left alone."""
    out = []
    for token in forename.split():
        if "." in token:
            out.append(token if token.endswith(".") else token + ".")
        else:
            out.append(token[0].upper() + ".")
    return " ".join(out)


def _in_text_label(entry: dict[str, str] | None, key: str) -> str:
    """Author-year form for an in-text citation."""
    if entry is None:
        return f"?{key}?"
    people = _split_author_names(entry.get("author", ""))
    year = entry.get("year", "n.d.")
    if not people:
        title = _clean(entry.get("title", key)).split(":")[0]
        short = title if len(title) <= 55 else title[:52].rstrip() + "..."
        return f"{short}, {year}"
    surnames = [surname for surname, _ in people]
    if len(surnames) == 1:
        who = surnames[0]
    elif len(surnames) == 2:
        who = f"{surnames[0]} & {surnames[1]}"
    else:
        who = f"{surnames[0]} et al."
    return f"{who}, {year}"


def _reference_entry(entry: dict[str, str]) -> str:
    """Full reference-list line for one work."""
    people = _split_author_names(entry.get("author", ""))
    if len(people) == 1 and not people[0][1]:
        rendered = [people[0][0]]                      # corporate author
    else:
        rendered = [
            f"{surname}, {_initials(forename)}".rstrip(", ")
            for surname, forename in people
        ]
    if not rendered:
        authors = ""
    elif len(rendered) == 1:
        authors = rendered[0]
    elif len(rendered) == 2:
        authors = f"{rendered[0]}, & {rendered[1]}"
    else:
        authors = ", ".join(rendered[:-1]) + f", & {rendered[-1]}"

    year = entry.get("year", "n.d.")
    title = _clean(entry.get("title", ""))
    venue = _clean(
        entry.get("journal")
        or entry.get("booktitle")
        or entry.get("publisher")
        or ""
    )
    doi = entry.get("doi", "").strip()

    parts = [f"{authors} ({year})." if authors else f"({year})."]
    if title:
        parts.append(title + ".")
    if venue:
        parts.append(venue + ".")
    line = " ".join(parts)
    if doi:
        line += f" https://doi.org/{doi}"
    return line


def resolve_citations(
    text: str, bib: dict[str, dict[str, str]], cited: set[str]
) -> str:
    """Replace ``[@key]`` markers with author-year text, recording keys used."""

    def replace(match: re.Match) -> str:
        keys: list[str] = []
        for raw in re.findall(r"@([A-Za-z0-9_:.\-]+)", match.group(1)):
            key = raw.rstrip(".,;")
            if key and key not in keys:
                keys.append(key)
        if not keys:
            return match.group(0)
        labels: list[str] = []
        for key in keys:
            cited.add(key)
            label = _in_text_label(bib.get(key), key)
            if label not in labels:
                labels.append(label)
        return "(" + "; ".join(labels) + ")"

    return CITATION_RE.sub(replace, text)


def build_reference_list(
    bib: dict[str, dict[str, str]], cited: set[str]
) -> list[str]:
    """Alphabetised reference lines for every cited work."""
    rows: list[tuple[str, str]] = []
    for key in cited:
        entry = bib.get(key)
        if entry is None:
            rows.append((key.lower(), f"[{key}] - NOT FOUND in {BIB_PATH}"))
            continue
        people = _split_author_names(entry.get("author", ""))
        sort_key = (
            people[0][0] if people else _clean(entry.get("title", key))
        ).lower()
        rows.append((sort_key, _reference_entry(entry)))
    rows.sort(key=lambda row: row[0])
    return [line for _, line in rows]


# fpdf2's multi_cell defaults to new_x=XPos.RIGHT, which leaves pdf.x at the RIGHT
# edge of the cell just drawn. The next full-width block then starts from there and
# runs off the page -- that is what pushed list items past the right margin. Every
# full-width block therefore goes through _block() or _list_item(), which move x back
# to the left margin before drawing and after finishing.
def _block(
    pdf: FPDF, w: float, h: float, text: str, x: float | None = None, **kwargs
) -> None:
    """Draw a text block, starting and finishing at the left margin."""
    pdf.set_x(pdf.l_margin if x is None else x)
    pdf.multi_cell(w, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, **kwargs)


def _list_item(
    pdf: FPDF, marker: str, text: str, indent: float, width: float, h: float, **kwargs
) -> None:
    """Draw a list item with a hanging indent so wrapped lines stay aligned."""
    pdf.set_x(pdf.l_margin)
    pdf.cell(indent, h, marker)
    pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(
        width - indent, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, **kwargs
    )


def _ensure_room(pdf: FPDF, needed_mm: float) -> None:
    """Start a new page if `needed_mm` no longer fits inside the text area.

    A rule, a heading, or a figure near the foot of a page would otherwise be drawn
    inside the bottom margin, outside the printable block. multi_cell breaks pages on
    its own, but pdf.line() and pdf.image() do not, so they are checked explicitly.
    """
    if pdf.get_y() + needed_mm > pdf.h - pdf.b_margin:
        pdf.add_page()


def _gather(lines: list[str], index: int, first: str) -> tuple[str, int]:
    """Join a block of prose starting with `first` at lines[index].

    Prose in this manuscript is hard-wrapped, and list items are hard-wrapped with
    an indented continuation, so a list item and its following lines have to be
    gathered into one string. Without this, the continuation lines are rendered as
    separate paragraphs at the left margin and the item reads as if it were cut off
    mid-sentence.
    """
    chunks = [first]
    cursor = index
    while cursor < len(lines):
        candidate = lines[cursor].strip()
        if not candidate:
            break
        if re.match(r"^#{1,4}\s", candidate) or candidate.startswith(">"):
            break
        if is_table_row(candidate):
            break
        if IMAGE_RE.match(candidate):
            break
        if re.match(r"^[-*+]\s", candidate) or re.match(r"^\d+\.\s", candidate):
            break
        if re.fullmatch(r"-{3,}", candidate):
            break
        chunks.append(candidate)
        cursor += 1
    return " ".join(chunks), cursor


def _figure(pdf: FPDF, source: str, caption: str, width: float) -> None:
    """Draw an image at the text width, centred, with a caption beneath it.

    The aspect ratio comes from the file rather than from the Markdown, so a figure
    can be regenerated at a different size without silently distorting it here. A
    missing file is reported in the PDF rather than skipped, because a silently
    absent figure is easy to miss and would ship in the preprint.
    """
    path = (PROJECT_ROOT / source).resolve()
    if not path.exists():
        print(f"  [WARN] figure not found, so it will not appear: {source}")
        _block(pdf, width, 5, latin1_safe(f"[missing figure: {source}]"), markdown=True)
        return

    try:
        with Image.open(path) as image:
            px_width, px_height = image.size
    except OSError as exc:
        print(f"  [WARN] figure could not be read: {source} ({exc})")
        return
    if px_width <= 0:
        print(f"  [WARN] figure has zero width: {source}")
        return

    aspect = px_height / px_width
    draw_width = width
    draw_height = draw_width * aspect
    if draw_height > FIGURE_MAX_HEIGHT_MM:
        draw_height = FIGURE_MAX_HEIGHT_MM
        draw_width = draw_height / aspect

    # Keep the image and its caption together on one page.
    _ensure_room(pdf, draw_height + 14)
    pdf.set_x(pdf.l_margin + (width - draw_width) / 2)
    pdf.image(str(path), w=draw_width, h=draw_height)
    pdf.ln(2.5)

    if caption:
        pdf.set_font(BODY_FONT, "", BODY_SIZE - 1.5)
        pdf.set_text_color(60)
        _block(pdf, width, 4.6, latin1_safe(caption), markdown=True)
        pdf.set_text_color(0)
        pdf.set_font(BODY_FONT, "", BODY_SIZE)
    pdf.ln(3.5)


class ManuscriptPDF(FPDF):
    """A4 PDF with a running footer showing page numbers."""

    def footer(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_x(self.l_margin)
        self.set_font(BODY_FONT, "", 8)
        self.set_text_color(110)
        self.cell(0, 5, str(self.page_no()), align="C")
        self.set_text_color(0)


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


# Markdown image syntax carrying a caption: ![caption](relative/path.png). The path
# is resolved against the project root, so figures are referenced as
# outputs/figures/fig1_trends.png.
IMAGE_RE = re.compile(r"^!\[(?P<caption>.*?)\]\((?P<source>[^)]+)\)\s*$")


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


def render(markdown_text: str, output: Path) -> tuple[set[str], list[str]]:
    pdf = ManuscriptPDF(format=PAGE_FORMAT, unit="mm")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    # Break at the margin, not inside it: a smaller value would let body text run
    # closer to the page edge than the margin allows.
    pdf.set_auto_page_break(True, margin=MARGIN)
    pdf.add_page()

    bib_path = PROJECT_ROOT / BIB_PATH
    bib = parse_bib(bib_path.read_text(encoding="utf-8")) if bib_path.exists() else {}
    if not bib:
        print(f"  [WARN] {BIB_PATH} not found; citations will NOT resolve.")

    text = preprocess(markdown_text)
    cited: set[str] = set()
    text = resolve_citations(text, bib, cited)

    # Replace the placeholder References section with the generated list, built only
    # from works actually cited above.
    unknown = sorted(key for key in cited if key not in bib)
    refs = build_reference_list(bib, cited)
    ref_block = "\n\n".join(f"- {line}" for line in refs)
    note = (
        f"Generated from {BIB_PATH}, listing only the {len(refs)} work(s) cited in "
        "this manuscript. DOI links resolve to the publisher record."
    )
    text, replaced = re.subn(
        r"(^## References\s*$).*?(?=^---\s*$|^## |\Z)",
        lambda m: f"{m.group(1)}\n\n{note}\n\n{ref_block}\n\n",
        text,
        flags=re.M | re.S,
    )
    if not replaced:
        # No References heading: append one so the citation list is never lost.
        text += f"\n\n---\n\n## References\n\n{note}\n\n{ref_block}\n"

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
            _ensure_room(pdf, 3)
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
            title = heading.group(2).strip().replace("**", "")
            sizes = {1: 16, 2: 13, 3: 11.5, 4: 10.5}
            pdf.ln(4 if level <= 2 else 2.5)
            # Keep a heading together with a couple of lines under it rather than
            # stranding it alone at the foot of a page.
            _ensure_room(pdf, 20 if level <= 2 else 16)
            pdf.set_font(BODY_FONT, "B", sizes.get(level, 10.5))
            if level == 1:
                pdf.set_text_color(0)
            _block(pdf, width, 6.5, latin1_safe(title))
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            pdf.ln(1.2)
            index += 1
            continue

        # Figure: ![caption](path). Checked before tables and paragraphs so an
        # image line is never absorbed into surrounding prose.
        image = IMAGE_RE.match(stripped)
        if image:
            _figure(
                pdf,
                image.group("source").strip(),
                image.group("caption").strip(),
                width,
            )
            index += 1
            continue

        # Tables.
        if is_table_row(stripped):
            rows, index = parse_table(lines, index)
            if rows:
                try:
                    pdf.set_font(BODY_FONT, "", 8.5)
                    # A hair narrower than the text block and left-aligned: fpdf2
                    # draws a table's rules slightly outside the width it is given,
                    # so a full-width centred table overhangs BOTH margins.
                    with pdf.table(
                        width=width - 1.6,
                        align="LEFT",
                        line_height=5,
                        first_row_as_headings=True,
                        borders_layout="HORIZONTAL_LINES",
                    ) as table:
                        for row in rows:
                            cells = table.row()
                            for cell_text in row:
                                cells.cell(latin1_safe(plain_emphasis(cell_text)))
                    pdf.set_font(BODY_FONT, "", BODY_SIZE)
                    pdf.ln(2.5)
                except Exception as exc:  # noqa: BLE001 - degrade instead of failing
                    # A malformed table must not abort the whole document.
                    pdf.set_font(BODY_FONT, "", BODY_SIZE)
                    _block(pdf, width, 5, latin1_safe(" ".join(rows[0])))
                    pdf.ln(1)
                    print(f"  [warn] table fallback used: {exc}")
            continue

        # Blockquote.
        if stripped.startswith(">"):
            quote = stripped.lstrip(">").strip()
            pdf.set_font(BODY_FONT, "I", BODY_SIZE - 0.5)
            pdf.set_text_color(70)
            pdf.set_x(pdf.l_margin + 4)
            # markdown=True so **bold** inside a note renders as bold; __ would be
            # read as italic markup, so it is escaped first.
            pdf.multi_cell(
                width - 8, 5.2,
                latin1_safe(quote.replace("__", "_\\_")),
                markdown=True,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.set_text_color(0)
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            pdf.ln(1.5)
            index += 1
            continue

        # Bullet list.
        bullet = re.match(r"^[-*+]\s+(.*)$", stripped)
        if bullet:
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            body, index = _gather(lines, index + 1, bullet.group(1))
            item = latin1_safe(body.replace("__", "_\\_"))
            _list_item(pdf, "-", item, 4.5, width, 5.4, markdown=True)
            pdf.ln(0.5)
            continue

        # Numbered list.
        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            pdf.set_font(BODY_FONT, "", BODY_SIZE)
            body, index = _gather(lines, index + 1, numbered.group(2))
            item = latin1_safe(body.replace("__", "_\\_"))
            _list_item(pdf, f"{numbered.group(1)}.", item, 6.5, width, 5.4, markdown=True)
            pdf.ln(0.5)
            continue

        # Paragraph.
        pdf.set_font(BODY_FONT, "", BODY_SIZE)
        joined, index = _gather(lines, index + 1, stripped)
        # fpdf2 reads __ as italic markup; identifiers with double underscores would
        # be mangled, so escape them before handing the text over.
        joined = joined.replace("__", "_\\_")
        _block(pdf, width, 5.4, latin1_safe(joined), markdown=True)
        pdf.ln(1.8)

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    return cited, unknown


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
    cited, unknown = render(markdown_text, target)

    print(f"Rendered {source.name} -> {target}")
    print(f"  size : {target.stat().st_size / 1024:.0f} KB")
    print(f"  cites: {len(cited)} work(s) cited, {len(cited) - len(unknown)} resolved")
    if unknown:
        print(f"  [WARN] citation key(s) not in {BIB_PATH}:")
        for key in unknown:
            print(f"           ?{key}?")

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
