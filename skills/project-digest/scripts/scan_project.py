#!/usr/bin/env python3
"""Compact project summary, designed to spend few tokens.

Walks the project skipping dependencies, binaries, lock files, builds and
generated files, and prints (as Markdown) only what helps understand the
project: stack, manifests, README, summarized tree, entry points,
routes/endpoints, data models, tests and environment variables.

Usage:
    python scan_project.py [path] [--depth N] [--max-files N] [--since REF]
                           [--budget-chars N] [--no-tree] [--json]

--since REF   Only considers files changed since REF (git), for example
              HEAD~5 or main. Useful during development.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------- exclusions
IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "bower_components", "vendor",
    "__pycache__", ".venv", "venv", "env", ".env.d", ".tox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".cache", ".parcel-cache", ".turbo",
    ".next", ".nuxt", ".svelte-kit", ".angular", ".expo", ".gradle", ".idea",
    ".vscode", ".vs", "dist", "build", "out", "target", "bin", "obj", "coverage",
    ".nyc_output", "htmlcov", "site-packages", "Pods", "DerivedData",
    ".terraform", ".serverless", "storybook-static", "tmp", "temp", "logs",
    "__snapshots__", "migrations_old", ".dart_tool", ".pub-cache", "android/app/build",
}
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock",
    "composer.lock", "Gemfile.lock", "Cargo.lock", "poetry.lock", "Pipfile.lock",
    "uv.lock", "go.sum", "pubspec.lock", "mix.lock", "Podfile.lock",
    "gradle.lockfile", "flake.lock", ".DS_Store", "Thumbs.db",
}
IGNORE_SUFFIXES = (
    ".lock", ".min.js", ".min.css", ".map", ".log", ".pyc", ".class", ".o", ".a",
    ".so", ".dll", ".exe", ".dylib", ".jar", ".war", ".zip", ".tar", ".gz",
    ".tgz", ".rar", ".7z", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".svg", ".bmp", ".tiff", ".psd", ".ai", ".mp3", ".mp4", ".mov", ".avi",
    ".wav", ".ogg", ".webm", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt",
    ".pptx", ".ttf", ".otf", ".woff", ".woff2", ".eot", ".sqlite", ".sqlite3",
    ".db", ".parquet", ".pkl", ".bin", ".dat", ".onnx", ".pt", ".h5", ".csv",
    ".snap", ".pb", ".wasm",
)
MAX_FILE_BYTES = 200_000  # larger files are usually generated/data

LANGS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (React)",
    ".ts": "TypeScript", ".tsx": "TypeScript (React)", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".vue": "Vue", ".svelte": "Svelte", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".swift": "Swift",
    ".php": "PHP", ".rb": "Ruby", ".cs": "C#", ".cpp": "C++", ".c": "C",
    ".h": "C/C++ header", ".dart": "Dart", ".scala": "Scala", ".ex": "Elixir",
    ".sql": "SQL", ".sh": "Shell", ".html": "HTML", ".css": "CSS",
    ".scss": "SCSS", ".prisma": "Prisma", ".graphql": "GraphQL",
    ".proto": "Protobuf", ".tf": "Terraform", ".yml": "YAML", ".yaml": "YAML",
}
CODE_EXTS = set(LANGS) - {".yml", ".yaml", ".css", ".scss", ".html"}

MANIFESTS = [
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts",
    "composer.json", "Gemfile", "pubspec.yaml", "mix.exs", "Package.swift",
    "deno.json", "tsconfig.json",
]
INFRA_FILES = [
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yaml",
    "Makefile", "vercel.json", "netlify.toml", "fly.toml", "render.yaml",
    "serverless.yml", "railway.json", "Procfile", ".github/workflows",
    ".gitlab-ci.yml", "nginx.conf", "prisma/schema.prisma", "schema.prisma",
    "openapi.yaml", "openapi.json", "swagger.json",
]
DOC_FILES = ["README.md", "README", "README.rst", "README.txt", "readme.md",
             "CLAUDE.md", "AGENTS.md", "ARCHITECTURE.md", "docs/README.md"]
ENTRY_NAMES = {
    "main.py", "app.py", "__main__.py", "manage.py", "wsgi.py", "asgi.py",
    "server.py", "cli.py", "index.js", "index.ts", "main.js", "main.ts",
    "server.js", "server.ts", "app.js", "app.ts", "index.tsx", "main.tsx",
    "App.tsx", "App.jsx", "App.vue", "main.go", "main.rs", "lib.rs",
    "Main.java", "Program.cs", "main.dart", "index.php", "artisan",
}
ROUTE_PATTERNS = [
    re.compile(r"@(?:app|router|bp|api)\.(get|post|put|patch|delete|route)\(\s*['\"]([^'\"]+)"),
    re.compile(r"\b(?:app|router|server|api)\.(get|post|put|patch|delete|use)\(\s*['\"`]([^'\"`]+)"),
    re.compile(r"@(Get|Post|Put|Patch|Delete|RequestMapping|GetMapping|PostMapping)\(\s*['\"]?([^'\")]*)"),
    re.compile(r"Route::(get|post|put|patch|delete|resource)\(\s*['\"]([^'\"]+)"),
    re.compile(r"\b(?:path|re_path)\(\s*['\"]([^'\"]*)['\"]"),
]
MODEL_PATTERNS = [
    re.compile(r"^\s*class\s+(\w+)\((?:[\w.]*Model|[\w.]*Base|db\.Model|models\.Model|SQLModel|BaseModel)\b"),
    re.compile(r"^\s*model\s+(\w+)\s*\{"),  # prisma
    re.compile(r"\b(?:sequelize\.)?define\(\s*['\"](\w+)"),
    re.compile(r"\bmongoose\.model\(\s*['\"](\w+)"),
    re.compile(r"^\s*(?:@Entity|@Table)\b.*$"),
    re.compile(r"CREATE TABLE(?: IF NOT EXISTS)?\s+[`\"]?(\w+)", re.I),
    re.compile(r"\bpgTable\(\s*['\"](\w+)"),
]
ENV_PATTERNS = [
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]+)"),
    re.compile(r"import\.meta\.env\.([A-Z][A-Z0-9_]+)"),
    re.compile(r"os\.(?:environ(?:\.get)?|getenv)\(?\[?\s*['\"]([A-Z][A-Z0-9_]+)"),
    re.compile(r"\bgetenv\(\s*['\"]([A-Z][A-Z0-9_]+)"),
    re.compile(r"\benv\(\s*['\"]([A-Z][A-Z0-9_]+)"),
]
TEST_HINTS = ("test", "tests", "spec", "__tests__", "e2e", "cypress")

# frameworks detected by dependency name
FRAMEWORK_HINTS = {
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt",
    "svelte": "Svelte", "@angular/core": "Angular", "express": "Express",
    "fastify": "Fastify", "@nestjs/core": "NestJS", "koa": "Koa",
    "hono": "Hono", "vite": "Vite", "tailwindcss": "Tailwind CSS",
    "prisma": "Prisma", "@prisma/client": "Prisma", "drizzle-orm": "Drizzle",
    "mongoose": "MongoDB (mongoose)", "typeorm": "TypeORM", "sequelize": "Sequelize",
    "jest": "Jest", "vitest": "Vitest", "playwright": "Playwright",
    "electron": "Electron", "react-native": "React Native", "expo": "Expo",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic", "celery": "Celery", "pytest": "pytest",
    "pandas": "pandas", "numpy": "NumPy", "torch": "PyTorch", "tensorflow": "TensorFlow",
    "scikit-learn": "scikit-learn", "streamlit": "Streamlit", "langchain": "LangChain",
    "anthropic": "Anthropic SDK", "openai": "OpenAI SDK", "stripe": "Stripe",
    "firebase": "Firebase", "supabase": "Supabase", "@supabase/supabase-js": "Supabase",
    "socket.io": "Socket.IO", "graphql": "GraphQL", "trpc": "tRPC",
    "laravel/framework": "Laravel", "rails": "Rails", "gin-gonic/gin": "Gin",
    "actix-web": "Actix", "axum": "Axum", "tokio": "Tokio",
}


def run_git(root, *args):
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                             text=True, timeout=20)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""


def is_ignored_file(path: Path) -> bool:
    name = path.name
    if name in IGNORE_FILES:
        return True
    low = name.lower()
    if low.endswith(IGNORE_SUFFIXES):
        return True
    if low.endswith((".d.ts", ".generated.ts", ".pb.go", "_pb2.py", ".g.dart")):
        return True
    return False


def looks_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)
    except OSError:
        return True


def walk(root: Path):
    """Yield relevant files, pruning ignored directories."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in IGNORE_DIRS and not d.startswith(".cache"))
        rel_dir = Path(dirpath).relative_to(root)
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            if is_ignored_file(p):
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield p, rel_dir / fn


def read_head(path: Path, max_chars=1500) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def parse_manifest(root: Path, name: str):
    p = root / name
    if not p.exists():
        return None
    info = {}
    if name == "package.json":
        try:
            data = json.loads(read_text(p))
        except Exception:
            return None
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        info = {
            "name": data.get("name"), "description": data.get("description"),
            "scripts": list((data.get("scripts") or {}).keys())[:12],
            "main": data.get("main"), "workspaces": data.get("workspaces"),
            "dependencies": len(deps),
            "frameworks": sorted({FRAMEWORK_HINTS[d] for d in deps if d in FRAMEWORK_HINTS}),
        }
    elif name in ("requirements.txt",):
        pkgs = [re.split(r"[=<>~\[; ]", l.strip(), 1)[0].lower()
                for l in read_text(p).splitlines() if l.strip() and not l.startswith("#")]
        info = {"dependencies": len(pkgs),
                "frameworks": sorted({FRAMEWORK_HINTS[d] for d in pkgs if d in FRAMEWORK_HINTS})}
    elif name == "pyproject.toml":
        txt = read_text(p)
        nm = re.search(r'^name\s*=\s*"([^"]+)"', txt, re.M)
        ds = re.search(r'^description\s*=\s*"([^"]+)"', txt, re.M)
        low = txt.lower()
        info = {"name": nm.group(1) if nm else None, "description": ds.group(1) if ds else None,
                "frameworks": sorted({v for k, v in FRAMEWORK_HINTS.items() if re.search(rf'["\'\s]{re.escape(k)}[\s"\'=<>~\[]', low)})}
    elif name in ("Cargo.toml", "go.mod", "composer.json", "pubspec.yaml", "pom.xml"):
        txt = read_text(p)
        info = {"frameworks": sorted({v for k, v in FRAMEWORK_HINTS.items() if k in txt})}
        nm = re.search(r'^(?:name|module)\s*[=\s]\s*"?([^"\s]+)', txt, re.M)
        if nm:
            info["name"] = nm.group(1)
    else:
        return {}
    return {k: v for k, v in info.items() if v}


def tree(root: Path, files, depth: int, max_lines: int):
    """Compact tree: directories up to `depth` with file counts."""
    counts = Counter()
    sample = defaultdict(list)
    for _, rel in files:
        parts = rel.parts
        d = parts[:-1][:depth]
        key = "/".join(d) if d else "."
        counts[key] += 1
        if len(parts) - 1 <= depth and len(sample[key]) < 6:
            sample[key].append(parts[-1])
    lines = []
    for key in sorted(counts):
        indent = "  " * (0 if key == "." else key.count("/") + 1)
        label = "(root)" if key == "." else key.split("/")[-1] + "/"
        extra = ", ".join(sample[key][:6])
        lines.append(f"{indent}{label} [{counts[key]}] {extra}")
        if len(lines) >= max_lines:
            lines.append("  … (tree truncated)")
            break
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--max-files", type=int, default=4000)
    ap.add_argument("--since", help="git ref; only files changed since then")
    ap.add_argument("--budget-chars", type=int, default=9000,
                    help="approximate output limit (≈ 4 chars per token)")
    ap.add_argument("--no-tree", action="store_true")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        sys.exit(f"Invalid path: {root}")

    changed = None
    if args.since:
        out = run_git(root, "diff", "--name-only", args.since)
        out += run_git(root, "ls-files", "--others", "--exclude-standard")
        changed = {l.strip() for l in out.splitlines() if l.strip()}

    all_files = []
    for p, rel in walk(root):
        if len(all_files) >= args.max_files:
            break
        if changed is not None and str(rel).replace(os.sep, "/") not in changed:
            continue
        if looks_binary(p):
            continue
        all_files.append((p, rel))

    out = []
    w = out.append
    w(f"# Project summary: {root.name}")
    w(f"Files analyzed: {len(all_files)}"
      + (f" (changed since {args.since})" if changed is not None else "")
      + " · dependencies, builds, binaries and lock files skipped.\n")

    # languages
    lang_count, lang_lines = Counter(), Counter()
    for p, rel in all_files:
        lang = LANGS.get(p.suffix.lower())
        if lang:
            lang_count[lang] += 1
            if p.suffix.lower() in CODE_EXTS and p.stat().st_size < 120_000:
                lang_lines[lang] += read_text(p).count("\n")
    if lang_count:
        w("## Languages")
        w(", ".join(f"{l} ({n} files, ~{lang_lines[l]} lines)" if lang_lines[l] else f"{l} ({n})"
                    for l, n in lang_count.most_common(8)))
        w("")

    # manifests
    mani_out = []
    for m in MANIFESTS:
        info = parse_manifest(root, m)
        if info is None:
            continue
        mani_out.append(f"- `{m}`" + (": " + "; ".join(f"{k}={v}" for k, v in info.items()) if info else ""))
    if mani_out:
        w("## Manifests and stack")
        out.extend(mani_out)
        w("")

    infra = [f for f in INFRA_FILES if (root / f).exists()]
    if infra:
        w("## Infra / build / CI")
        w(", ".join(f"`{f}`" for f in infra))
        w("")

    # docs
    for d in DOC_FILES:
        p = root / d
        if p.exists():
            w(f"## {d} (start)")
            w(read_head(p, 1500).strip())
            w("")
            break

    # tree
    if not args.no_tree:
        w("## Structure (directory [file count] examples)")
        out.extend(tree(root, all_files, args.depth, 45))
        w("")

    # entry points
    entries = [str(rel) for _, rel in all_files if rel.name in ENTRY_NAMES]
    if entries:
        w("## Likely entry points")
        w(", ".join(f"`{e}`" for e in entries[:12]))
        w("")

    # content analysis
    routes, models, envs, tests = [], [], Counter(), 0
    todo_count = 0
    for p, rel in all_files:
        sfx = p.suffix.lower()
        parts_low = [x.lower() for x in rel.parts]
        is_test = any(h in parts_low[:-1] for h in TEST_HINTS) or re.search(r"(\.|_)(test|spec)\.", rel.name.lower()) or rel.name.lower().startswith("test_")
        if is_test:
            tests += 1
            continue
        if sfx not in CODE_EXTS and sfx not in (".sql", ".prisma"):
            continue
        txt = read_text(p)
        for pat in ROUTE_PATTERNS:
            for m in pat.finditer(txt):
                g = m.groups()
                routes.append(f"{g[0].upper() if len(g) > 1 else 'PATH'} {g[-1]}  ← {rel}")
        for pat in MODEL_PATTERNS:
            for m in pat.finditer(txt):
                if m.groups():
                    models.append(f"{m.group(1)}  ← {rel}")
        for pat in ENV_PATTERNS:
            for m in pat.finditer(txt):
                envs[m.group(1)] += 1
        todo_count += len(re.findall(r"\b(TODO|FIXME|HACK)\b", txt))

    def section(title, items, limit):
        if not items:
            return
        w(f"## {title} ({len(items)})")
        seen = []
        for i in items:
            if i not in seen:
                seen.append(i)
        out.extend(f"- {i}" for i in seen[:limit])
        if len(seen) > limit:
            w(f"- … {len(seen) - limit} more")
        w("")

    section("Routes / endpoints", routes, 25)
    section("Data models", models, 20)
    if envs:
        w("## Environment variables used")
        w(", ".join(f"`{k}`" for k, _ in envs.most_common(20)))
        w("")
    w("## Quality")
    w(f"- Test files: {tests} · TODO/FIXME/HACK: {todo_count}")
    ex = [f for f in (".env.example", ".env.sample", ".env.template") if (root / f).exists()]
    if ex:
        w(f"- Env example: {', '.join(ex)}")
    w("")

    # git
    log = run_git(root, "log", "-n", "8", "--pretty=%as %s")
    if log.strip():
        w("## Recent commits")
        w(log.strip())
        w("")

    w("## Suggested next step")
    w("Read only the entry files and 1–2 central modules above; "
      "use Grep for symbols instead of opening whole files.")

    text = "\n".join(out)
    if len(text) > args.budget_chars:
        text = text[:args.budget_chars].rsplit("\n", 1)[0] + "\n… (output truncated; use --budget-chars to raise the limit)"
    print(text)


if __name__ == "__main__":
    main()
