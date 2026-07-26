#!/usr/bin/env python3
"""Convert PDF files to structured Markdown.

Usage:
  ./pdf_to_markdown.py input.pdf [more.pdf ...] [-o out.md]
  ./pdf_to_markdown.py some_directory/ -o combined.md

Improvements over a plain text dump:
- infers heading levels (#, ##, ###) from relative font size
- preserves bold/italic spans as **bold** / *italic*
- turns PDF hyperlink annotations into [text](url) links
- detects two-column page layouts and reads each column top-to-bottom
- keeps bullet/numbered list markers and fenced code blocks intact
- removes end-of-line hyphenation artifacts from justified text
- falls back to OCR for scanned/image-only pages
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "PyMuPDF is required. Run the bundled ./pdf_to_markdown wrapper (uses uv) "
        "or `pip install pymupdf`."
    ) from exc

OCR_SCALE = 3
_OCR_ENGINE = None
_OCR_IMPORT_ERROR: Optional[Exception] = None

BULLET_RE = re.compile(r"^([*\-+•‣◦])\s+")
NUMBERED_RE = re.compile(r"^(\d+)[\.)]\s+")
MULTISPACE_RE = re.compile(r"[ \t]+")
HARD_HYPHEN_RE = re.compile(r"(?<=\w)-\n(?=\w)")
FENCE_RE = re.compile(r"^```")

# Print/browser-chrome artifacts that show up per-page on PDFs produced by
# "print this webpage" (timestamps, page counters, the browser tab title
# repeated on every page).
TIMESTAMP_LINE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[AP]M$")
PAGE_COUNTER_LINE_RE = re.compile(r"^\d+\s*/\s*\d+$")
BOILERPLATE_LINE_RES = (TIMESTAMP_LINE_RE, PAGE_COUNTER_LINE_RE)


# ---------------------------------------------------------------------------
# Layout: reading order
#
# This document is single-column prose with embedded label/description
# tables — the side-by-side blocks that show up are table rows, not a real
# multi-column article layout. A "split into left column then right column"
# heuristic would read those tables column-then-column instead of row by
# row, so reading order is simply top-to-bottom, left-to-right; the table
# detector below is what reconstructs the side-by-side rows correctly.
# ---------------------------------------------------------------------------

def ordered_blocks(page: "fitz.Page") -> List[dict]:
    raw = page.get_text("dict")
    blocks = [b for b in raw.get("blocks", []) if b.get("type") == 0 and b.get("lines")]
    return sorted(blocks, key=lambda b: (round(b["bbox"][1], 1), b["bbox"][0]))


# ---------------------------------------------------------------------------
# Font-size based heading inference
# ---------------------------------------------------------------------------

def body_font_size(blocks: List[dict]) -> float:
    sizes = Counter()
    for block in blocks:
        for line in block["lines"]:
            for span in line["spans"]:
                chars = len(span["text"])
                if chars:
                    sizes[round(span["size"], 1)] += chars
    if not sizes:
        return 10.0
    return sizes.most_common(1)[0][0]


def heading_prefix(size: float, base: float, word_count: int) -> str:
    if word_count > 18:
        return ""
    ratio = size / base if base else 1.0
    if ratio >= 1.6:
        return "# "
    if ratio >= 1.35:
        return "## "
    if ratio >= 1.15:
        return "### "
    return ""


# ---------------------------------------------------------------------------
# Span formatting: bold / italic / links
# ---------------------------------------------------------------------------

def is_bold(span: dict) -> bool:
    flags = span.get("flags", 0)
    font = span.get("font", "").lower()
    return bool(flags & 2 ** 4) or "bold" in font


def is_italic(span: dict) -> bool:
    flags = span.get("flags", 0)
    font = span.get("font", "").lower()
    return bool(flags & 2 ** 1) or "italic" in font or "oblique" in font


def link_for_span(span_bbox: Tuple[float, float, float, float], links: List[dict]) -> Optional[str]:
    sx0, sy0, sx1, sy1 = span_bbox
    scx, scy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    for link in links:
        uri = link.get("uri")
        if not uri:
            continue
        lx0, ly0, lx1, ly1 = link["from"]
        if lx0 - 1 <= scx <= lx1 + 1 and ly0 - 1 <= scy <= ly1 + 1:
            return uri
    return None


def is_code(span: dict) -> bool:
    return "mono" in span.get("font", "").lower()


def format_span_text(text: str, span: dict, links: List[dict]) -> str:
    text = text.strip("­")
    if not text.strip():
        return text

    uri = link_for_span(span["bbox"], links)

    leading = re.match(r"^\s*", text).group()
    trailing = re.search(r"\s*$", text).group()
    core = text.strip()
    if not core:
        return text

    if is_code(span):
        core = f"`{core}`"
    elif is_bold(span) and is_italic(span):
        core = f"***{core}***"
    elif is_bold(span):
        core = f"**{core}**"
    elif is_italic(span):
        core = f"*{core}*"

    if uri:
        core = f"[{core}]({uri})"

    return f"{leading}{core}{trailing}"


# ---------------------------------------------------------------------------
# Table detection
#
# In this document each table row is laid out as a label column followed by
# a description column further right — sometimes as lines within a single
# PDF text block, sometimes (when a label wraps to two lines) split across
# several adjacent blocks. Plain wrapped paragraphs never do this: every
# wrapped line restarts at the same left margin. So: cluster a set of lines
# by x0 into "column bands"; if that produces 2+ bands separated by a real
# gap, it's a table row, regardless of which original block each line came
# from.
# ---------------------------------------------------------------------------

COLUMN_JUMP_PT = 36.0
COLUMN_TOL_PT = 12.0
ROW_MERGE_GAP_PT = 14.0


def cluster_column_bands(x0_values: List[float]) -> List[float]:
    """Group x0 positions into column bands, return each band's leftmost x0
    in ascending order."""
    uniq = sorted(set(round(x, 1) for x in x0_values))
    bands: List[List[float]] = []
    for x in uniq:
        if bands and x - bands[-1][-1] <= COLUMN_TOL_PT:
            bands[-1].append(x)
        else:
            bands.append([x])
    return [band[0] for band in bands]


def detect_table_columns(lines: List[dict]) -> Optional[List[float]]:
    if len(lines) < 2:
        return None
    bands = cluster_column_bands([line["bbox"][0] for line in lines])
    if not (2 <= len(bands) <= 6):
        return None
    if any(b - a < COLUMN_JUMP_PT for a, b in zip(bands, bands[1:])):
        return None
    return bands


def join_cell_fragment(existing: str, addition: str) -> str:
    if not existing:
        return addition
    if existing.rstrip("*").endswith(("-", "_", "/")):
        return existing + addition
    return f"{existing} {addition}"


def lines_to_row_cells(
    lines: List[dict], links: List[dict], boilerplate: set
) -> Optional[Tuple[List[str], List[float]]]:
    visible = [l for l in lines if not is_boilerplate_line(raw_line_text(l), boilerplate)]
    bands = detect_table_columns(visible)
    if bands is None:
        return None

    columns: List[List[dict]] = [[] for _ in bands]
    for line in visible:
        x0 = line["bbox"][0]
        col = min(range(len(bands)), key=lambda i: abs(x0 - bands[i]))
        columns[col].append(line)

    cells = []
    for col_lines in columns:
        col_lines.sort(key=lambda l: l["bbox"][1])
        text = ""
        for line in col_lines:
            t, _, _ = line_to_text(line, links)
            t = normalize_line(dehyphenate(t), False)
            if t:
                text = join_cell_fragment(text, t)
        cells.append(text)

    if not any(cells):
        return None
    return cells, bands


def block_to_row_cells(
    block: dict, links: List[dict], boilerplate: set
) -> Optional[Tuple[List[str], List[float]]]:
    return lines_to_row_cells(block["lines"], links, boilerplate)


def try_absorb_continuation(
    block: dict, bands: List[float], links: List[dict], boilerplate: set
) -> Optional[Tuple[int, str]]:
    """A block that isn't a table row on its own (often a single indented
    line, e.g. a command snippet) may still belong to the last row's
    description cell if every line lines up with a non-label column band."""
    visible = [l for l in block["lines"] if not is_boilerplate_line(raw_line_text(l), boilerplate)]
    if not visible:
        return None

    cols = set()
    for line in visible:
        x0 = line["bbox"][0]
        matches = [i for i, b in enumerate(bands) if abs(x0 - b) <= COLUMN_TOL_PT and i >= 1]
        if not matches:
            return None
        cols.add(matches[0])
    if len(cols) != 1:
        return None

    text = ""
    for line in sorted(visible, key=lambda l: l["bbox"][1]):
        t, _, _ = line_to_text(line, links)
        t = normalize_line(dehyphenate(t), False)
        if t:
            text = join_cell_fragment(text, t)
    if not text:
        return None
    return next(iter(cols)), text


def merge_wrapped_row_fragments(blocks: List[dict]) -> List[dict]:
    """PyMuPDF sometimes splits one (wrapped) table row into several small
    blocks. Merge runs of small, vertically-adjacent blocks back together
    when doing so reveals a clean multi-column table row."""
    merged: List[dict] = []
    i, n = 0, len(blocks)
    while i < n:
        group = [blocks[i]]
        max_y1 = blocks[i]["bbox"][3]
        j = i + 1
        while (
            j < n
            and len(group) < 10
            and len(blocks[j]["lines"]) <= 3
            and blocks[j]["bbox"][1] - max_y1 <= ROW_MERGE_GAP_PT
        ):
            group.append(blocks[j])
            max_y1 = max(max_y1, blocks[j]["bbox"][3])
            j += 1

        if len(group) > 1:
            combined_lines = [line for b in group for line in b["lines"]]
            if len(combined_lines) <= 16 and detect_table_columns(combined_lines) is not None:
                bbox = (
                    min(b["bbox"][0] for b in group),
                    min(b["bbox"][1] for b in group),
                    max(b["bbox"][2] for b in group),
                    max(b["bbox"][3] for b in group),
                )
                merged.append({"type": 0, "bbox": bbox, "lines": combined_lines})
                i = j
                continue

        merged.append(blocks[i])
        i += 1
    return merged


def escape_table_cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_table(rows: List[List[str]]) -> str:
    num_cols = max(len(r) for r in rows)
    padded = [r + [""] * (num_cols - len(r)) for r in rows]
    lines = ["| " + " | ".join(escape_table_cell(c) for c in padded[0]) + " |"]
    lines.append("| " + " | ".join("---" for _ in range(num_cols)) + " |")
    for row in padded[1:]:
        lines.append("| " + " | ".join(escape_table_cell(c) for c in row) + " |")
    return "\n".join(lines)


def raw_line_text(line: dict) -> str:
    """Plain, unformatted text of a line — used to detect repeated boilerplate."""
    text = "".join(span.get("text", "") for span in line["spans"])
    return MULTISPACE_RE.sub(" ", text).strip()


def detect_repeated_boilerplate(pages_blocks: List[List[dict]]) -> set:
    """Find lines that repeat verbatim across most pages (headers/footers from
    a browser "print to PDF") so they can be dropped from the output."""
    num_pages = len(pages_blocks)
    if num_pages < 3:
        return set()

    pages_per_line: dict = {}
    for blocks in pages_blocks:
        seen_this_page = set()
        for block in blocks:
            for line in block["lines"]:
                text = raw_line_text(line)
                if len(text) < 3 or text in seen_this_page:
                    continue
                seen_this_page.add(text)
                pages_per_line[text] = pages_per_line.get(text, 0) + 1

    threshold = max(3, (num_pages * 2) // 5)
    return {text for text, count in pages_per_line.items() if count >= threshold}


def line_to_text(line: dict, links: List[dict]) -> Tuple[str, float, bool]:
    """Return (formatted text, max font size, any-bold) for one PDF line."""
    parts = []
    max_size = 0.0
    any_bold = False
    for span in line["spans"]:
        txt = span.get("text", "")
        if not txt:
            continue
        max_size = max(max_size, span.get("size", 0.0))
        if is_bold(span):
            any_bold = True
        parts.append(format_span_text(txt, span, links))
    return "".join(parts).strip(), max_size, any_bold


# ---------------------------------------------------------------------------
# Cleanup helpers (whitespace, hyphenation, lists, code fences)
# ---------------------------------------------------------------------------

def normalize_line(line: str, in_code_block: bool) -> str:
    if in_code_block:
        return line.rstrip()
    line = line.strip()
    line = MULTISPACE_RE.sub(" ", line)
    line = re.sub(r"\s+([,.;:!?])", r"\1", line)
    return line


def dehyphenate(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("­", "")
    return HARD_HYPHEN_RE.sub("", text)


def apply_list_markers(stripped: str) -> str:
    bullet_match = BULLET_RE.match(stripped)
    if bullet_match:
        return f"- {stripped[bullet_match.end():].strip()}"
    numbered_match = NUMBERED_RE.match(stripped)
    if numbered_match:
        return f"{numbered_match.group(1)}. {stripped[numbered_match.end():].strip()}"
    return stripped


# ---------------------------------------------------------------------------
# OCR fallback for scanned/image-only pages
# ---------------------------------------------------------------------------

def _get_ocr_engine():
    global _OCR_ENGINE, _OCR_IMPORT_ERROR
    if _OCR_ENGINE is not None:
        return _OCR_ENGINE
    if _OCR_IMPORT_ERROR is not None:
        return None
    try:
        import numpy as np  # type: ignore
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except Exception as exc:  # pragma: no cover
        _OCR_IMPORT_ERROR = exc
        return None
    _OCR_ENGINE = (np, RapidOCR())
    return _OCR_ENGINE


def normalize_ocr_line(text: str) -> str:
    text = text.replace("­", "")
    text = MULTISPACE_RE.sub(" ", text).strip()
    text = re.sub(r"([,.;:!?])(?=\S)", r"\1 ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    return MULTISPACE_RE.sub(" ", text).strip()


def ocr_page_lines(page: "fitz.Page") -> List[str]:
    engine = _get_ocr_engine()
    if engine is None:
        return []
    np, ocr = engine
    pix = page.get_pixmap(matrix=fitz.Matrix(OCR_SCALE, OCR_SCALE), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 1:
        img = np.repeat(img, 3, axis=2)
    elif pix.n > 3:
        img = img[:, :, :3]
    try:
        result, _ = ocr(img)
    except Exception:
        return []
    if not result:
        return []
    ordered = []
    for item in result:
        if not item or len(item) < 2:
            continue
        box, text = item[0], item[1]
        if not text or not str(text).strip():
            continue
        try:
            top = min(point[1] for point in box)
            left = min(point[0] for point in box)
        except Exception:
            top, left = 0, 0
        ordered.append((top, left, normalize_ocr_line(str(text))))
    ordered.sort()
    return [text for _, _, text in ordered]


# ---------------------------------------------------------------------------
# Page -> Markdown
# ---------------------------------------------------------------------------

def is_boilerplate_line(raw_text: str, boilerplate: set) -> bool:
    if raw_text in boilerplate:
        return True
    return any(pattern.match(raw_text) for pattern in BOILERPLATE_LINE_RES)


def page_to_markdown(
    page: "fitz.Page",
    page_number: int,
    boilerplate: set,
    blocks: Optional[List[dict]] = None,
    show_page_markers: bool = False,
) -> str:
    if blocks is None:
        blocks = ordered_blocks(page)
    links = page.get_links()

    if not blocks:
        ocr_lines = ocr_page_lines(page)
        if not ocr_lines:
            if show_page_markers:
                return f"\n\n---\n\n<!-- page {page_number}: empty -->\n"
            return ""
        ocr_lines = [l for l in ocr_lines if not is_boilerplate_line(l, boilerplate)]
        body = "\n".join(apply_list_markers(dehyphenate(l)) for l in ocr_lines)
        if show_page_markers:
            return f"\n\n---\n\n<!-- page {page_number} (OCR) -->\n\n{body}\n"
        return f"\n\n{body}\n"

    base_size = body_font_size(blocks)
    blocks = merge_wrapped_row_fragments(blocks)
    md_lines: List[str] = []
    in_code_block = False
    blank_run = 0
    table_rows: List[List[str]] = []
    table_bands: List[float] = []

    def flush_table() -> None:
        if not table_rows:
            return
        if len(table_rows) >= 2:
            md_lines.append(render_table(table_rows))
            md_lines.append("")
        else:
            # A single tabular-looking block isn't enough to be confident
            # it's really a table; fall back to plain cell-per-line text.
            for cell in table_rows[0]:
                if cell:
                    md_lines.append(cell)
            md_lines.append("")
        table_rows.clear()
        table_bands.clear()

    def bands_compatible(a: List[float], b: List[float]) -> bool:
        return len(a) == len(b) and all(abs(x - y) <= COLUMN_TOL_PT * 2 for x, y in zip(a, b))

    for block in blocks:
        if not in_code_block:
            result = block_to_row_cells(block, links, boilerplate)
            if result is not None:
                cells, bands = result
                if table_rows and not bands_compatible(bands, table_bands):
                    flush_table()
                table_rows.append(cells)
                table_bands[:] = bands
                continue

            if table_rows:
                absorbed = try_absorb_continuation(block, table_bands, links, boilerplate)
                if absorbed is not None:
                    col, text = absorbed
                    table_rows[-1][col] = join_cell_fragment(table_rows[-1][col], text)
                    continue
        flush_table()

        for line in block["lines"]:
            if not in_code_block and is_boilerplate_line(raw_line_text(line), boilerplate):
                continue

            text, size, _ = line_to_text(line, links)
            text = dehyphenate(text)
            text = normalize_line(text, in_code_block)

            if FENCE_RE.match(text):
                blank_run = 0
                md_lines.append(text)
                in_code_block = not in_code_block
                continue

            if not text:
                blank_run += 1
                if blank_run <= 1:
                    md_lines.append("")
                continue
            blank_run = 0

            if in_code_block:
                md_lines.append(text)
                continue

            word_count = len(text.split())
            prefix = heading_prefix(size, base_size, word_count)
            if prefix:
                md_lines.append(f"{prefix}{text}")
                continue

            md_lines.append(apply_list_markers(text))

        md_lines.append("")  # blank line between PDF text blocks (paragraphs)

    flush_table()

    while md_lines and md_lines[-1] == "":
        md_lines.pop()

    body = "\n".join(md_lines)
    if show_page_markers:
        return f"\n\n---\n\n<!-- page {page_number} -->\n\n{body}\n"
    return f"\n\n{body}\n"


def pdf_to_markdown(pdf_path: Path, show_page_markers: bool = False) -> str:
    with fitz.open(pdf_path) as doc:
        pages_blocks = [ordered_blocks(page) for page in doc]
        boilerplate = detect_repeated_boilerplate(pages_blocks)

        parts = [f"# {pdf_path.stem}"]
        for i, (page, blocks) in enumerate(zip(doc, pages_blocks), start=1):
            parts.append(page_to_markdown(page, i, boilerplate, blocks=blocks, show_page_markers=show_page_markers))
        parts.append("")
        return "\n".join(parts)


def iter_pdfs(paths: Iterable[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_dir():
            yield from sorted(x for x in p.rglob("*.pdf") if x.is_file())
        else:
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert PDF files to structured Markdown")
    parser.add_argument("inputs", nargs="+", help="PDF files or directories")
    parser.add_argument("-o", "--output", help="Write combined output to a file instead of stdout")
    parser.add_argument(
        "--page-markers",
        action="store_true",
        help="Emit an HTML comment + rule marking each page boundary "
        "(default: pages flow together with no per-page markers)",
    )
    args = parser.parse_args()

    pdfs = list(iter_pdfs(Path(p) for p in args.inputs))
    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        return 2

    chunks = []
    for pdf in pdfs:
        if not pdf.exists():
            print(f"Missing file: {pdf}", file=sys.stderr)
            return 2
        if pdf.suffix.lower() != ".pdf":
            print(f"Skipping non-PDF: {pdf}", file=sys.stderr)
            continue
        chunks.append(pdf_to_markdown(pdf, show_page_markers=args.page_markers))

    output = "\n\n".join(chunks).rstrip() + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
