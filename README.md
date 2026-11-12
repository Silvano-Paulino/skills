# Skills Collection

A curated collection of modular skills ready for use with AI coding assistants and autonomous agents (such as Google Antigravity, Gemini CLI, Claude Code, and others).

Each skill is a self-contained package containing instructions (`SKILL.md`), helper scripts, and bundled resources that teach specialized workflows to your agent.

---

## Table of Contents

- [Skills Catalog](#skills-catalog)
- [How to Download and Install](#how-to-download-and-install)
  - [Option 1: Download a Specific Skill via `degit` (Recommended)](#option-1-download-a-specific-skill-via-degit-recommended)
  - [Option 2: Clone the Full Repository](#option-2-clone-the-full-repository)
  - [Option 3: Download Using Git Sparse Checkout](#option-3-download-using-git-sparse-checkout)
  - [Option 4: Add as a Git Submodule](#option-4-add-as-a-git-submodule)
- [Where to Place Skills](#where-to-place-skills)
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

## How to Download and Install

You can install a single skill or the entire repository depending on your needs.

### Option 1: Download a Specific Skill via `degit` (Recommended)

[`degit`](https://github.com/Rich-Harris/degit) allows you to download only the directory of the desired skill without cloning Git history:

#### To install in your current project (Workspace):
```bash
# Create the agent skills directory (if it does not exist)
mkdir -p .agents/skills

# Download the desired skill (example: project-digest)
npx degit Silvano-Paulino/skills/skills/project-digest .agents/skills/project-digest
```

#### To install globally on your machine (available across all projects):
```bash
# For Google Antigravity / Gemini CLI:
mkdir -p ~/.gemini/skills
npx degit Silvano-Paulino/skills/skills/project-digest ~/.gemini/skills/project-digest

# For Claude Code:
mkdir -p ~/.claude/skills
npx degit Silvano-Paulino/skills/skills/project-digest ~/.claude/skills/project-digest
```

---

### Option 2: Clone the Full Repository

To gain access to all available skills:

```bash
# 1. Clone the repository
git clone https://github.com/Silvano-Paulino/skills.git

# 2. Copy a specific skill to your project:
mkdir -p .agents/skills
cp -r skills/skills/project-digest .agents/skills/

# Or copy ALL skills at once:
cp -r skills/skills/* .agents/skills/
```

---

### Option 3: Download Using Git Sparse Checkout

If you prefer to use standard Git without third-party tools (`npx`) and without downloading the entire repository history:

```bash
# 1. Clone the repository in sparse mode
git clone --depth 1 --filter=blob:none --sparse https://github.com/Silvano-Paulino/skills.git /tmp/skills-temp

# 2. Enable sparse checkout for the specific skill directory
cd /tmp/skills-temp
git sparse-checkout set skills/project-digest

# 3. Copy to your project or global directory
mkdir -p /path/to/your-project/.agents/skills
cp -r skills/project-digest /path/to/your-project/.agents/skills/

# 4. Clean up temporary files
cd - && rm -rf /tmp/skills-temp
```

---

### Option 4: Add as a Git Submodule

To keep skills version-controlled and synchronized within your project:

```bash
git submodule add https://github.com/Silvano-Paulino/skills.git .agents/vendor/skills
```

---

## Where to Place Skills

AI agents automatically locate skills by checking designated directories:

| Agent / Tool | Project Scope (Local) | Global Scope (User Machine) |
| :--- | :--- | :--- |
| **Google Antigravity / Gemini CLI** | `.agents/skills/<skill-name>/` | `~/.gemini/skills/<skill-name>/` |
| **Claude Code** | `.claude/skills/<skill-name>/` or `.agents/skills/` | `~/.claude/skills/<skill-name>/` |
| **Cursor / Codex / Others** | `.agents/skills/<skill-name>/` | Check tool documentation |

---

## How to Use

Once installed in the appropriate directory, the skill is **immediately ready to use**:

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
