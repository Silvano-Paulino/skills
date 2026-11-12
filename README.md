# Skills Collection

A curated collection of modular skills ready for use with AI coding assistants and autonomous agents (such as Google Antigravity, Gemini CLI, Claude Code, Cursor, and others).

Skills follow the [Agent Skills specification](https://agentskills.io/specification) and are intended to be installable through the [skills CLI](https://www.skills.sh/docs/cli) from [skills.sh](https://skills.sh).

Each skill is a self-contained package containing instructions (`SKILL.md`), helper scripts, and bundled resources that teach specialized workflows to your agent.

---

## Table of Contents

- [Skills Catalog](#skills-catalog)
- [Install](#install)
- [How to Use](#how-to-use)
- [Skill Anatomy and Structure](#skill-anatomy-and-structure)
- [How to Contribute](#how-to-contribute)

---

## Skills Catalog

| Skill | Description | Requirements / Scripts |
| :--- | :--- | :--- |
| [`project-digest`](./skills/project-digest/) | Compact project summary designed to spend minimal context tokens, ignoring `node_modules`, builds, and binary files. Extracts stack, endpoints, models, and structure. | Python 3 (`scripts/scan_project.py`) |

> More skills will be continuously added to this repository.

---

## Install

Install all skills from this repository:

```bash
npx skills add Silvano-Paulino/skills
```

Install a specific skill:

```bash
npx skills add Silvano-Paulino/skills --skill project-digest
```

> **Tip:** You can install skills globally across all your projects by adding the `-g` flag:
> ```bash
> npx skills add Silvano-Paulino/skills --skill project-digest -g
> ```

---

## How to Use

Once installed via the `skills` CLI, the skill is **immediately ready to use**:

1. **Automatic Discovery:** The agent reads the frontmatter metadata in `SKILL.md` (`name` and `description`).
2. **Contextual Triggering:** Whenever your prompt or task aligns with the skill's purpose, the agent dynamically loads the full instructions.
3. **Example with `project-digest`:**
   ```text
   User: "Give me an overview of the architecture and existing endpoints in this project."
   Agent: [Activates the project-digest skill, runs scan_project.py, and delivers a compact breakdown]
   ```

---

## Skill Anatomy and Structure

All skills in this repository follow the standard agent skill specification:

```text
skills/<skill-name>/
├── SKILL.md          # Required: YAML frontmatter metadata and step-by-step instructions
├── scripts/          # Optional: Executable helper scripts (Python, Shell, Node, etc.)
├── references/       # Optional: In-depth documentation and manuals
└── resources/        # Optional: Templates, configuration files, or static assets
```

---

## How to Contribute

Contributions of new skills are welcome:

1. Create a new branch from `main`:
   ```bash
   git checkout -b feat/new-skill
   ```
2. Add a directory under `skills/<skill-name>/` following the structure above.
3. Ensure `SKILL.md` includes clear `name` and `description` YAML frontmatter fields defining when and how the skill should be used.
4. Add your new skill to the table in [Skills Catalog](#skills-catalog).
5. Open a Pull Request with a clear description of the workflow.
