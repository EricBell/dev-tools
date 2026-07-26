# PDF to Markdown

**Version:** 1.0.0

CLI for converting PDFs into structured Markdown, including table reconstruction.

## Use

```bash
./pdfconvert/pdf2md sources/dont-need-mcp.pdf
./pdfconvert/pdf2md sources/feedback-examples.pdf -o /tmp/feedback.md
./pdfconvert/pdf2md sources/ -o /tmp/all.md
./pdfconvert/pdf2md sources/dont-need-mcp.pdf --page-markers -o /tmp/with-pages.md
```

Or run the Python script directly through uv:

```bash
uv run --with pymupdf --with rapidocr-onnxruntime --with numpy python pdfconvert/pdf_to_markdown.py sources/dont-need-mcp.pdf
```

## What it does

- keeps text in reading order
- infers heading levels (`#`/`##`/`###`) from relative font size
- preserves bold/italic spans and turns PDF link annotations into `[text](url)`
- formats monospace-font spans as inline code
- reconstructs label/description tables into real Markdown tables, even
  when a row is split across several PDF text blocks or a page break
- keeps bullet/numbered list structure when possible
- removes common line-wrap hyphenation
- strips repeated print/browser-chrome boilerplate (timestamps, page
  counters, a tab title repeated on every page) left over from PDFs that
  were captured via "print this webpage"

## Notes

- Uses `uv` to fetch dependencies transiently
- Falls back to OCR for image-only/scanned pages
- Works on a single PDF file or a directory of PDFs
- Writes combined output to stdout unless `-o/--output` is given
- By default, pages flow together with no page boundary markers. Use
  `--page-markers` only when you want a `---` rule and an `<!-- page N -->`
  comment before each page
- See [PROCEDURE.md](PROCEDURE.md) for the rationale behind the table and
  boilerplate-stripping heuristics
