# Prompt: Create a Simple Composable Tool

Use this prompt when I ask you to create a new reusable tool in this repository.

---

You are helping me create a small, agent-friendly CLI tool in the spirit of `sources/dont-need-mcp.md`, without rereading that article. The core idea is: prefer simple Bash-invoked scripts plus concise README documentation over large always-loaded MCP servers. Tools should be easy for future agents to discover, understand, run, compose, modify, and test.

## Operating principles

1. **Keep the interface tiny and obvious**
   - Expose one or a few command-line entry points.
   - Make the common use case the default path.
   - Use clear arguments and flags.
   - Print useful `Usage:` help when arguments are missing or invalid.

2. **Rely on Bash and code composability**
   - Tools should run from the shell and compose with pipes, redirects, temp files, and other scripts.
   - Prefer writing artifacts to files and printing paths/summaries instead of dumping huge data into agent context.
   - Allow agents to chain invocations in one Bash command when useful.

3. **Minimize context burden**
   - Document the tool with a short README that tells future agents:
     - what it does
     - when to use it
     - setup/dependencies
     - exact commands/examples
     - outputs and important cautions
   - Do not require future agents to read implementation code unless they are debugging or extending it.

4. **Make it easy to modify**
   - Keep implementation small and direct.
   - Avoid unnecessary frameworks, daemons, servers, or broad abstractions.
   - Prefer standard language tooling already present in the repo (`uv` for Python where appropriate, shell wrappers for entry points, Node scripts only if that is clearly best).

5. **Design outputs for downstream use**
   - Output stable, parseable formats where possible: JSON, CSV, Markdown, plain paths, or concise key/value lines.
   - For large outputs, write files and print their locations.
   - Include quiet/verbose or output-path options if useful.

6. **Be project-compatible**
   - Inspect existing `tools/` structure before adding anything.
   - Put the new tool under `tools/<tool-name>/` unless I specify otherwise.
   - Follow naming/style patterns already used in this repo.
   - Update `tools/README.md` after adding or changing a tool.

## Before building, ask questions when needed

Ask only the questions required to avoid building the wrong thing. If the request is clear, proceed. If not, ask about:

- the exact task the tool should perform
- expected inputs and formats
- desired outputs and file formats
- whether outputs may be large and should be written to files
- required dependencies or dependency restrictions
- whether the tool must be cross-platform or only for this environment
- examples of intended use
- whether the tool is for humans, agents, or both

Prefer 3–6 targeted questions over a long questionnaire. If reasonable assumptions are obvious, state them and continue.

## Build workflow

When creating a tool:

1. **Inspect context**
   - Read relevant existing tool READMEs/scripts under `tools/`.
   - Check repo conventions, dependency style, and entry point patterns.

2. **Design the minimal interface**
   - Choose the smallest useful CLI surface.
   - Define commands, flags, inputs, outputs, and failure behavior.
   - Prefer explicit examples over elaborate abstractions.

3. **Implement**
   - Create `tools/<tool-name>/`.
   - Add the main script(s) and executable wrapper(s) if helpful.
   - Include clear error messages and `Usage:` output.
   - Make scripts executable when appropriate.
   - Use temporary directories/files for transient artifacts when appropriate.

4. **Document**
   - Add `tools/<tool-name>/README.md` with:
     - title
     - purpose
     - setup/dependencies
     - usage examples in fenced Bash blocks
     - input/output behavior
     - notes/cautions
   - Keep the README short enough that a future agent can read it cheaply.

5. **Test**
   - Run realistic smoke tests.
   - Test missing/invalid argument behavior.
   - Verify outputs are correctly written and are not excessively noisy.

6. **Catalog**
   - Update `tools/README.md` with the new or changed tool:
     - purpose
     - key files
     - when to use it
     - setup/dependency notes
     - cautions

7. **Report back concisely**
   - Summarize what was created/changed.
   - Show exact example commands.
   - Mention tests run and any limitations.

## Quality checklist

Before finalizing, verify:

- [ ] Tool can be run from Bash with a simple command.
- [ ] Missing arguments show concise usage help.
- [ ] Outputs are concise, file-based when large, and easy to consume.
- [ ] README is enough for a future agent to use the tool without reading code.
- [ ] Implementation avoids unnecessary server/MCP/framework complexity.
- [ ] Tool is composable with shell workflows.
- [ ] Dependencies are documented and lightweight where possible.
- [ ] `tools/README.md` is updated.
- [ ] Smoke tests pass or limitations are clearly stated.

## Default style preference

Create boring, durable tools: small scripts, clear command names, simple arguments, practical output, concise docs. If an MCP server, long-running service, or complex framework seems tempting, first explain why a simple CLI script would not be enough.
