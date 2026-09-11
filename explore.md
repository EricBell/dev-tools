Deeply explore the current working directory (or a path the user specifies), extract the most salient facts about the codebase, and write them to **OVERVIEW.md** in the project root.

The goal is a document a new developer could read on day one to understand *what the app does*, *how it's structured*, *what it connects to*, and *where the interesting parts are*. Be specific and factual — avoid vague summaries. If you find a concrete detail (a database URL format, an API endpoint, a notable architectural pattern), include it.

## Exploration strategy

Use the tools available to you to explore in parallel where possible. Here's what to look for:

**Start with the high-level anchors:**
- `package.json` / `Cargo.toml` / `pyproject.toml` / `go.mod` — dependencies, scripts, metadata
- `README.md` if it exists — stated purpose
- Main entry point (e.g. `src/main.tsx`, `app.py`, `cmd/main.go`, `index.js`)
- Build/config files (e.g. `vite.config.*`, `webpack.config.*`, `docker-compose.yml`, `.env.example`)

**File and directory structure:**
- Walk the top 2–3 levels of the directory tree
- Identify major groupings (e.g. `routes/`, `components/`, `api/`, `db/`, `services/`)
- Note any monorepo structure (workspaces, `packages/`, `apps/`)

**Tech stack:**
- Framework(s) and runtime
- Language(s)
- Build tooling
- Test framework

**Integrations:**
- Third-party APIs and SDKs (look for imports, env var names, config keys)
- Authentication providers
- Analytics, monitoring, feature flags
- Payment processors, messaging services, etc.

**Database and data layer:**
- ORM or query library in use
- Database type (Postgres, MySQL, SQLite, MongoDB, etc.)
- Schema files or migration directories
- Connection config (env var names, config files)

**Connectivity and configuration:**
- `.env.example` or similar — what env vars are expected
- API proxy config (e.g. Vite's `server.proxy`, nginx config)
- Port numbers, base URLs, service addresses
- Any hardcoded endpoints or service URLs in source

**Architecture patterns:**
- State management approach
- Routing strategy
- Notable design patterns (e.g. provider pattern, command/event bus, repository pattern)
- Anything non-obvious that would trip up a new developer

## OVERVIEW.md format

Write the file to the project root. Use this structure, but adapt section depth and detail to what's actually present — don't include empty sections:

```markdown
# [App/Project Name] — Overview

> One-sentence description of what this app does and who uses it.

## Purpose

2–4 sentences on the domain, user-facing purpose, and any important context
(e.g. "phase 0 of a migration from Preact to React").

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ... | ... |

## Directory Structure

Brief annotated tree of the top 2–3 levels. Only include directories and files
that are meaningful — skip `node_modules`, lockfiles, build output, etc.

## Architecture

Key architectural patterns, data flow, and anything non-obvious. This section
is where you explain the *how* rather than just listing what exists.

## Integrations

For each external service or API: what it is, what it's used for, and where
in the codebase it appears.

## Database & Data Layer

ORM/library, database type, schema location, migration approach, connection config.
If there's no database, say so (e.g. "Frontend-only — no database layer").

## Connectivity & Configuration

Expected environment variables, API proxy setup, service endpoints, ports.
Use a table or list with variable name + purpose.

## Key Entry Points

The files a new developer should read first to understand how the app boots
and how requests/events flow through it.

## Notes & Gotchas

Anything that would surprise a new developer: non-standard patterns, in-progress
migrations, known tech debt worth knowing about, Preact internals being used, etc.
```

## Quality bar

- Be specific. "Uses Postgres via Drizzle ORM, schema defined in `packages/db/schema.ts`" is better than "uses a database."
- If something is unclear (e.g. you can see a dependency but can't find where it's used), say so briefly rather than omitting it.
- Keep the file readable — a developer should be able to scan it in 5 minutes.
- Don't reproduce large code blocks; reference file paths instead.
- After writing the file, confirm to the user what was created and where.
