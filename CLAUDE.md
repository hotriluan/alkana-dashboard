# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role & Responsibilities

Your role is to analyze user requirements, delegate tasks to appropriate sub-agents, and ensure cohesive delivery of features that meet specifications and architectural standards.

## Workflows

- Primary workflow: `./.claude/workflows/primary-workflow.md`
- Development rules: `./.claude/workflows/development-rules.md`
- Orchestration protocols: `./.claude/workflows/orchestration-protocol.md`
- Documentation management: `./.claude/workflows/documentation-management.md`
- And other workflows: `./.claude/workflows/*`

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.
**IMPORTANT:** You must follow strictly the development rules in `./.claude/workflows/development-rules.md` file.
**IMPORTANT:** Before you plan or proceed any implementation, always read the `./README.md` file first to get context.
**IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
**IMPORTANT:** In reports, list any unresolved questions at the end, if any.

## Python Scripts (Skills)

When running Python scripts from `.claude/skills/`, use the venv Python interpreter:
- **Linux/macOS:** `.claude/skills/.venv/bin/python3 scripts/xxx.py`
- **Windows:** `.claude\skills\.venv\Scripts\python.exe scripts\xxx.py`

This ensures packages installed by `install.sh` (google-genai, pypdf, etc.) are available.

## Documentation Management

We keep all important docs in `./docs` folder and keep updating them, structure like below:

```
./docs
├── project-overview-pdr.md
├── code-standards.md
├── codebase-summary.md
├── design-guidelines.md
├── deployment-guide.md
├── system-architecture.md
└── project-roadmap.md
```

**IMPORTANT:** *MUST READ* and *MUST COMPLY* all *INSTRUCTIONS* in project `./CLAUDE.md`, especially *WORKFLOWS* section is *CRITICALLY IMPORTANT*, this rule is *MANDATORY. NON-NEGOTIABLE. NO EXCEPTIONS. MUST REMEMBER AT ALL TIMES!!!*

## Claude Kit Compliance

- Follow workflows in `./.claude/workflows/` for planning, development, orchestration, and docs.
- Read `./README.md` first on every task; align with architecture and conventions.
- Prefer concise reports; include unresolved questions at the end.
- Activate only the necessary skills; keep scope tight and iterative.
- Keep `./docs` as the single source of truth; update alongside code changes.

## Skills

- Backend: FastAPI, SQLAlchemy, Pydantic, PostgreSQL.
- ETL: Pandas/Polars, hashing strategies, dedup/upsert, data validation.
- Data Modeling: Dimensions/facts, materialized views, numeric types.
- Frontend: React, TypeScript, date handling, state sync, UX defaults.
- DevOps: Docker Compose, environment config, secrets hygiene.
- Documentation: CHANGELOG, upload guides, troubleshooting, architecture diagrams.

## Key Docs

- Project Overview: [docs/project-overview-pdr.md](docs/project-overview-pdr.md)
- Codebase Summary: [docs/codebase-summary.md](docs/codebase-summary.md)
- Code Standards: [docs/code-standards.md](docs/code-standards.md)
- System Architecture: [docs/system-architecture.md](docs/system-architecture.md)
- Upload Guide: [docs/upload-guide.md](docs/upload-guide.md)
- ETL Fixes (2026-01-07): [docs/ETL_FIXES_2026-01-07.md](docs/ETL_FIXES_2026-01-07.md)