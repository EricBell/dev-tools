# Procedure: PDF to raw Markdown

## Tool

`tools/pdfconvert/pdf_to_markdown.py` (driven by the `tools/pdfconvert/pdf2md` wrapper).

It uses PyMuPDF to walk each page's text blocks/lines/spans (not a flat text dump), which lets it:

- detect two-column layouts and read each column top-to-bottom instead of
  interleaving lines across columns
- infer heading levels from font size relative to the page's dominant body
  size (`#`/`##`/`###`)
- carry bold/italic span formatting into `**bold**` / `*italic*`
- convert PDF link annotations into `[text](url)` by matching span bounding
  boxes against `page.get_links()`
- keep bullet/numbered list markers and fenced code blocks intact
- strip end-of-line hyphenation from justified text
- fall back to OCR (RapidOCR) per-page when a page has no extractable text
  (scanned/image-only pages)
- strip repeated print/browser-chrome boilerplate (timestamps, page counters,
  a tab title repeated on every page) that "print this webpage to PDF" tends
  to bake into the source — detected by exact-text repetition across most
  pages, plus regexes for date/time stamps and `N/M` page counters

## Steps taken

1. Checked what PDF libraries were already available (`fitz`, `pdfplumber`,
   `pdftotext`) — none were installed system-wide, but `uv` was, so the tool
   fetches `pymupdf`, `rapidocr-onnxruntime`, and `numpy` transiently via
   `uv run --with ...` rather than requiring a manual install step.
2. Wrote `pdf_to_markdown.py`: column-aware block ordering, font-size-based
   heading inference, span-level bold/italic/link formatting, list/hyphenation
   cleanup, OCR fallback.
3. Wrapped it in the `pdf2md` shell script for a single-command entry point.
4. Ran it against the source PDF:
   ```bash
   ./tools/pdfconvert/pdf2md 260626.TritonInstructions.pdf -o instructions.md
   ```
5. Spot-checked the output: confirmed all 14 pages extracted as native text
   (no OCR fallback needed), headings/bold/links rendered correctly, and a
   TOML config block in the source stayed readable in plain-text form.
6. Diffed against a prior manual conversion (`triton-instructions.md`) and
   noticed the source PDF was a "print this webpage" capture: every page
   repeated a timestamp line, a browser tab-title line, and a footer
   URL+page-counter line. Added `detect_repeated_boilerplate()` (flags any
   line that appears verbatim on at least 40% of pages, min 3) plus regexes
   for date/time stamps and `N/M` page counters, and re-ran the conversion —
   dropped ~70 boilerplate lines while leaving genuine one-off content (e.g.
   a "Collapse Instructions" UI label that only appears once) untouched.

## Usage

```bash
./tools/pdfconvert/pdf2md input.pdf [more.pdf ...] [-o out.md]
./tools/pdfconvert/pdf2md some_directory/ -o combined.md
./tools/pdfconvert/pdf2md input.pdf --page-markers -o out.md  # keep per-page markers

# or, without the wrapper:
uv run --with pymupdf --with rapidocr-onnxruntime --with numpy \
    python tools/pdfconvert/pdf_to_markdown.py input.pdf -o out.md
```

By default pages flow together with no boundary markers. Use `--page-markers`
only when you want a `---` rule plus an `<!-- page N -->` (or `(OCR)` / `: empty`)
comment before each page.
