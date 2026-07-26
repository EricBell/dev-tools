# Tool: Tool Catalog Maintainer

## Purpose
Create and maintain a `README.md` catalog for a user-specified directory containing subfolders of tools, prompts, scripts, docs, workflows, skills, or other reusable resources.

The README is a living catalog. It should improve over time as new subfolders are added and existing ones are updated. Future humans and LLM agents will refer to this README to decide which resource to use for a request.

Invoke this tool when the user asks to:

- create a catalog README for a folder of tools/resources
- update an existing catalog after tools change
- summarize available prompts, scripts, docs, workflows, or reusable assets
- make a directory easier for LLMs to navigate
- document a collection of reusable tools
- generate or refresh an index for agent skills, prompts, scripts, references, or workflows

## Inputs

| Layer | Path | Required | Notes |
| --- | --- | --- | --- |
| Layer 4 working | `<target-folder>/` | Yes | The folder the user points to. It should contain one or more direct subfolders to catalog. |
| Layer 4 working | `<target-folder>/README.md` | No | Existing catalog to preserve and improve when present. |
| Layer 3 reference | `tools/tool-catalog-maintainer/references/catalog-format.md` | Yes | Defines the recommended README structure and cataloging rules. |

## Process

1. Confirm the target folder exists.
2. Inspect the target folder's direct subfolders. Treat each direct subfolder as one catalog entry unless the user's request says otherwise.
3. For each subfolder, inspect enough contents to understand its purpose and use:
   - `README.md`, `CONTEXT.md`, `SKILL.md`, `PROCEDURE.md`, and other Markdown files
   - prompt files
   - scripts such as `.py`, `.sh`, `.js`, `.ts`, `.rb`, `.go`, etc.
   - config files such as `package.json`, `pyproject.toml`, `requirements.txt`, `uv.lock`, `.env.example`
   - `references/`, `docs/`, `assets/`, `output/`, or similarly named support folders
4. Do not deeply read generated outputs, large dependency folders, archives, or binary assets unless they are necessary to identify the tool.
5. If a catalog README already exists, preserve useful existing content and improve it rather than replacing blindly.
6. Write for future LLM consumption:
   - use explicit folder names and paths
   - state when to use each tool
   - name key files and entry points
   - call out setup requirements and cautions
   - prefer structured tables plus short per-tool sections
7. Create or update `<target-folder>/README.md` using the format in `references/catalog-format.md`.
8. Verify the README covers every relevant direct subfolder and does not invent capabilities not supported by the inspected files.

## Outputs

Update or create:

```text
<target-folder>/README.md
```

The README should be a durable catalog, not a one-time summary.

## Verify

Before finishing, verify that:

- the target folder exists
- every relevant direct subfolder is represented in the catalog
- each entry has a purpose and “when to use” guidance
- key files or entry points are listed where known
- setup or dependency notes are included when visible
- existing README content was preserved when useful
- unsupported claims were avoided
