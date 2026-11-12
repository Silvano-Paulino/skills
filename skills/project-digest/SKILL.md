---
name: project-digest
description: Analyzes a code project with the fewest possible tokens and returns the essentials - what it does, its purpose, stack, main features, architecture, how to run it and risks. Uses a script that skips node_modules, binaries, lock files, builds and generated files. ALWAYS use when the user asks to analyze, understand, summarize, explore, document or onboard onto a project, repository or codebase (e.g. "what does this project do?", "analyze the code", "explain the structure", "give me an overview of the codebase"); when opening an unfamiliar code folder or before planning changes in a project not yet read in this session; and during development to see what changed (git) or reassess the project's state. Prefer this skill over reading files one by one, even if the user never mentions tokens.
---

# Project Digest

Goal: understand a project while reading as little as possible. Reading a codebase file by file burns tokens, and most of what gets read (dependencies, lock files, builds, binaries, generated code) says nothing about the project. This skill uses a script that does that triage outside the model's context and returns a compact summary; code reading is reserved for what the summary cannot answer.

## Workflow

### 1. Run the script (always first)

```bash
python <skill-path>/scripts/scan_project.py <project-root>
```

Useful options:

- `--since HEAD~5` (or `main`): only considers files changed since that git reference. Use it during development to see what changed instead of re-analyzing everything.
- `--depth 2`: shorter tree for large projects. `--no-tree` omits it.
- `--budget-chars 15000`: raises the output limit (default ~9000 characters, about 2k tokens) when the project is large and the summary came back truncated.

The output includes: languages, manifests and frameworks, infra/CI, the start of the README, a summarized tree with counts, entry points, routes/endpoints, data models, environment variables, tests, TODOs and recent commits.

If the script cannot run (no Python), follow the "Without the script" section below.

### 2. Decide whether that is enough

If the user only wants an overview, the script's summary plus the README is usually enough. Answer right away. Only go deeper when there is a concrete question the summary cannot answer.

### 3. Go deeper with precision (only if needed)

In order of increasing cost; stop as soon as there is an answer:

1. `Grep` for symbols, routes or names (returns lines, not whole files).
2. `Read` with `offset`/`limit` on the relevant parts of 1 to 3 central files: entry points, routes module, models, configuration.
3. Only as a last resort, open whole files, and never those on the exclusion list.

In monorepos, analyze the root first and then each relevant package with `scan_project.py <package>`, instead of a single pass over everything.

### 4. Write the report

Adapt it to the project and the request; omit sections with no content. Base structure:

- **What it is**: one or two sentences on what the project does and for whom.
- **Purpose**: the problem it solves. If it is not stated explicitly, say it is inferred from the code.
- **Stack**: languages, frameworks, database, infra.
- **Main features**: the 3 to 7 that really define the project, with the file where each lives.
- **Architecture and flow**: how the parts connect (for example, client → API → database), entry points and where to make each kind of change.
- **How to run it**: install, development and test commands, and the environment variables required.
- **State and risks**: test coverage, relevant TODOs, technical debt, exposed secrets, what is unfinished.

Separate what was confirmed in the code from what is inference. A short, correct summary is worth more than a long, speculative one.

## What never to read

The script already excludes these categories; follow the same rule when using `Read`, `Glob` and `Grep` by hand, because opening them costs many tokens and tells you nothing:

- Dependencies and caches: `node_modules`, `vendor`, `.venv`, `__pycache__`, `.cache`, `Pods`.
- Builds and artifacts: `dist`, `build`, `out`, `target`, `.next`, `coverage`.
- Lock files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Cargo.lock`, `go.sum`, `composer.lock`, etc.
- Binaries and media: images, videos, fonts, PDFs, zips, databases, models.
- Generated or minified code: `*.min.js`, `*.map`, `*.d.ts`, `*_pb2.py`, snapshots.
- Large data (`.csv`, `.parquet`) and files over ~200 KB.

With `Grep`, narrow the search with `glob` or `type` and use `head_limit` so you don't get hundreds of lines back.

## Without the script

1. `Glob` with `*` at the root and in the top-level directories (never recursive at the root).
2. Read the manifest (`package.json`, `pyproject.toml`, `go.mod`, ...) and the start of the README.
3. Locate entry points by name (`main.*`, `index.*`, `app.*`, `server.*`) and read only the beginning.
4. `Grep` for routes (`@app.get`, `router.post`, `app.use`) and models (`class .*Model`, `model `, `CREATE TABLE`) with `output_mode: "files_with_matches"` first.

## During development

To keep the context up to date without rereading everything, run `scan_project.py <root> --since <ref>` and compare with what is already known. If the structure changed (new modules, routes, models), update only that part of the understanding.
