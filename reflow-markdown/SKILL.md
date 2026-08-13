---
name: reflow-markdown
description: Use when a markdown (or plain text) file has hard line-wraps inside paragraphs — text that was wrapped at a fixed column so lines break mid-sentence — and you want the paragraphs to flow naturally as single logical lines. Preserves headers, blank lines between paragraphs, section boundaries, lists, and links.
---

# Reflow Markdown Skill

Use this skill when the user asks to "reformat," "reflow," "unwrap," or "remove line breaks" from a markdown file where paragraphs have been hard-wrapped (e.g. copy-pasted from a Google Doc or PDF export), so that each paragraph becomes one continuous line of text instead of several short fixed-width lines.

## Goal

Turn hard-wrapped paragraphs into naturally flowing single lines, without changing any content, while leaving document structure intact.

## What to preserve exactly as-is

- Headers (`#`, `##`, etc.) — keep on their own line, untouched.
- Blank lines between paragraphs — keep the same number of blank lines (including intentional double-blank-line spacing used as visual section breaks).
- List items (bulleted `●`/`-`/`*` or numbered) — keep each item on its own line; do not merge list items into paragraphs or into each other.
- Links, inline code, emphasis, and any markdown syntax — keep exactly as written, including multi-line link references if they span lines for a reason other than wrapping.
- Section boundaries and horizontal structure — do not merge text across a heading or a list into an adjacent paragraph.
- Wording, punctuation, and capitalization — do not rewrite, summarize, or correct the text itself. This is a formatting-only pass.

## What to change

- Within a single paragraph, where line breaks exist only because the original text was wrapped at a column width (not because of an intentional list/structure break), join those lines into one line, using a single space between the joined segments.

## Workflow

1. Read the full file first.
2. Identify paragraph boundaries: a paragraph is a run of consecutive non-blank lines that are not headers and not list items.
3. For each paragraph, join its lines into one line, separated by single spaces. Trim any duplicated whitespace at the join points.
4. Leave headers, blank-line spacing, and list items untouched, in their original positions.
5. Write the full reformatted file back out (Write tool with full content is simplest for a whole-file reflow; use Edit for a partial one).
6. Do a quick pass to confirm: same headers in the same order, same number of list items, no text content changed — only line breaks within paragraphs removed.

## Notes

- If a "paragraph" is actually a single Q/A pair or similar unit that itself was wrapped across many lines, treat the whole Q/A as one paragraph to unwrap into one line.
- If unsure whether a line break is structural (intentional) or just wrapping, prefer treating consecutive plain-text lines with no blank line between them as one paragraph to unwrap — that's almost always wrapping.
- Don't add or remove blank lines that weren't clearly just wrap artifacts; unusual spacing (e.g. multiple blank lines) may be intentional visual separation in the source doc and should be kept as found.
