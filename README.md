# Tool Catalog

This README catalogs the tools and resources in this directory. It is intended for humans and LLM agents to quickly identify what is available and when to use it.

## Catalog

| Tool / Folder | Purpose | Key Files | When to Use |
| --- | --- | --- | --- |
| `pdfconvert/` | Converts PDFs into structured Markdown with layout-aware text extraction, basic formatting preservation, table reconstruction, and OCR fallback. | `README.md`, `PROCEDURE.md`, `pdf2md`, `pdf_to_markdown.py` | Use when source material is in PDF form and needs to become Markdown for downstream reading, ingestion, or LLM workflows. |
| `tool-catalog-maintainer/` | ICM tool/Agent Skill for creating and maintaining living `README.md` catalogs for folders of reusable tools/resources. | `CONTEXT.md`, `SKILL.md`, `references/catalog-format.md`, `README.md` | Use when asked to catalog, index, summarize, or update documentation for a folder containing tool subfolders. |
| `url_monitor/` | Repeatedly pings a host/IP to a timestamped log and analyzes that log for timeout outages and recording gaps. | `README.md`, `ping_to_file.sh`, `analyze_ping_log.py` | Use when monitoring internet/host reachability over time or summarizing ping logs for disconnections. |
| `video-align/` | Uses WhisperX to transcribe/align video or audio and converts WhisperX JSON output into utterance-level and word-level CSV files. | `README.md`, `run-whisperx.sh`, `make-csvs.py`, `pyproject.toml` | Use when aligning spoken media to timestamps or when a WhisperX JSON transcript needs CSV exports. |
| `wake-on-lan/` | Sends a Wake-on-LAN magic packet to a machine on the local network. | `README.md`, `wol.py` | Use when you need to wake a sleeping host from the LAN with a tiny `uv`-run Python script. |

## Tools

### `pdfconvert/`

**Purpose:**  
Script-driven PDF-to-Markdown converter. It walks PDF pages with PyMuPDF, preserves reading order and common text formatting, reconstructs some tables, strips repeated print/browser boilerplate, and can fall back to OCR for scanned/image-only pages.

**Contents:**
- `README.md` — overview, examples, feature list, and notes
- `PROCEDURE.md` — implementation rationale and usage details
- `pdf2md` — shell wrapper entry point
- `pdf_to_markdown.py` — Python implementation

**Use when:**  
Use for converting one PDF, multiple PDFs, or a directory of PDFs into Markdown for review, source ingestion, or agent-readable context.

**Setup / dependencies:**  
Uses `uv` to fetch transient dependencies: `pymupdf`, `rapidocr-onnxruntime`, and `numpy`. No manual install step is noted.

**Notes:**  
Run from the repository root with paths like:

```bash
./tools/pdfconvert/pdf2md input.pdf -o output.md
./tools/pdfconvert/pdf2md source-folder/ -o combined.md
```

Use `--page-markers` only when page boundary comments/rules are needed.

### `tool-catalog-maintainer/`

**Purpose:**  
ICM-style tool and Agent Skills-compatible package for creating or updating a living catalog README in a target folder. The catalog is designed to help future humans and LLM agents choose the right tool/resource quickly.

**Contents:**
- `CONTEXT.md` — source-of-truth ICM operating contract
- `SKILL.md` — Agent Skills-compatible adapter/definition
- `references/catalog-format.md` — recommended README structure and cataloging rules
- `README.md` — thin landing page pointing to the operating files
- `output/` — reserved scratch/generated artifact folder

**Use when:**  
Use when a folder contains subfolders of tools, prompts, scripts, docs, workflows, skills, or reusable assets and needs a new or refreshed `README.md` catalog.

**Setup / dependencies:**  
None noted. This is primarily a prompt/workflow tool driven by Markdown instructions.

**Notes:**  
`CONTEXT.md` is the source of truth. `README.md` is intentionally short to avoid duplicating the operating contract.

### `url_monitor/`

**Purpose:**  
Small shell/Python reachability monitor. It appends timestamped `ping` results for a host/IP to a log file and analyzes the log for timeout-based disconnections and missing-record gaps.

**Contents:**
- `README.md` — overview, examples, log format, dependencies, and cautions
- `ping_to_file.sh` — Bash logger that repeatedly pings a target and writes one line per attempt
- `analyze_ping_log.py` — Python analyzer for outage and recording-gap summaries

**Use when:**  
Use to monitor internet or host reachability over time, then summarize when timeouts occurred and whether the logger stopped or paused.

**Setup / dependencies:**  
Requires Bash, the system `ping` command, and Python 3.10+. No third-party Python packages are required.

**Notes:**  
Run from the repository root with paths like:

```bash
./tools/url_monitor/ping_to_file.sh 8.8.8.8 /tmp/ping.log
./tools/url_monitor/analyze_ping_log.py /tmp/ping.log
```

Despite the folder name, the monitor uses ICMP ping reachability for a host/IP, not HTTP status checks for full URL paths.

### `video-align/`

**Purpose:**  
Script-driven helper for running WhisperX on media files and converting the resulting JSON transcript/alignment into CSV files.

**Contents:**
- `README.md` — setup and usage snippets
- `run-whisperx.sh` — shell wrapper that runs `uv run whisperx <input>` with `medium.en`, English language, JSON output, and `output/` as the destination
- `make-csvs.py` — reads `output/input.json` and writes `utterances.csv` and `words.csv`
- `pyproject.toml` — Python project metadata requiring Python `>=3.12` and `whisperx>=3.8.6`
- `main.py` — default uv scaffold entry point; not the main alignment workflow
- `output/` — WhisperX JSON output location; contains generated artifacts

**Use when:**  
Use when you need timestamped speech transcription/alignment from video/audio or need utterance/word CSVs from a WhisperX JSON output.

**Setup / dependencies:**  
Uses `uv`; project dependency is `whisperx>=3.8.6` and Python `>=3.12`.

**Notes:**  
The converter currently expects the WhisperX JSON at `output/input.json`; rename/copy the generated JSON or adjust `make-csvs.py` if the WhisperX output file has a different name.

## Maintenance Notes

When adding or updating a tool folder, update this README with:

- purpose
- key files and entry points
- usage guidance
- setup requirements
- notable changes or cautions

Treat each direct subfolder of `tools/` as one catalog entry unless a future tool explicitly documents a different structure. Avoid cataloging generated `output/` contents as source capabilities.
