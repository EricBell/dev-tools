# Tool Catalog Maintainer

This folder contains the `tool-catalog-maintainer` ICM tool/agent skill.

## Start here

- Agent operating contract: [`CONTEXT.md`](CONTEXT.md)
- Agent Skills adapter: [`SKILL.md`](SKILL.md)
- Catalog README format rules: [`references/catalog-format.md`](references/catalog-format.md)

## Intent

Use this tool to create or update a living `README.md` catalog for a target folder of tools, prompts, scripts, docs, workflows, skills, or reusable resources.

Example request:

```text
Use tool-catalog-maintainer on tools/
```

`CONTEXT.md` is the source of truth for how the tool runs. Keep this README as a short landing page only.
