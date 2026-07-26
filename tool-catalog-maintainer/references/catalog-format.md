# Catalog README Format

Use this reference when creating or updating a catalog README for a folder of tools, prompts, scripts, docs, workflows, or other reusable resources.

## Recommended README shape

```markdown
# Tool Catalog

This README catalogs the tools and resources in this directory. It is intended for humans and LLM agents to quickly identify what is available and when to use it.

## Catalog

| Tool / Folder | Purpose | Key Files | When to Use |
| --- | --- | --- | --- |
| `example-tool/` | Brief summary of what it does. | `README.md`, `script.py` | Use when... |

## Tools

### `example-tool/`

**Purpose:**  
Describe what this tool/resource does in 1–3 sentences.

**Contents:**
- `README.md` — usage notes and overview
- `script.py` — command-line entry point
- `references/` — supporting documentation

**Use when:**  
Describe the requests or situations where an agent should choose this tool.

**Setup / dependencies:**  
List visible install steps, runtimes, package managers, API keys, or “None noted.”

**Notes:**  
Include cautions, output locations, maintenance hints, or limitations.

## Maintenance Notes

When adding or updating a tool folder, update this README with:

- purpose
- key files and entry points
- usage guidance
- setup requirements
- notable changes or cautions
```

## Cataloging rules

- Prefer accuracy over completeness. If purpose is unclear, say so and name the files inspected.
- Do not claim a tool can do something unless the files support it.
- Keep the table compact; put detail in the per-tool sections.
- Include exact relative paths so future agents can load the right files quickly.
- Distinguish source files from generated `output/` artifacts.
- Mention whether a tool is prompt-only, script-driven, documentation-only, or a workflow.
- If a folder has its own README, use it as the primary source but still verify key files.
- Preserve useful existing catalog notes during updates.
- Remove stale entries only when the corresponding folder is gone or clearly obsolete.
