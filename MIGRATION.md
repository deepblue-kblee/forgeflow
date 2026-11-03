# ForgeFlow 0.1.x → 0.2.x user-project migration

This document belongs to the `archive/forgeflow-migrate` branch, not the 0.2.x core distribution.

## What it does

- Creates `archive/pre-forgeflow-0.2.1` on the project's current HEAD.
- Removes the old `tasks/`, `docs/releases/`, and `docs/forgeflow/` trees from the working tree.
- Removes known 0.1.x strict files: legacy constitution, gatekeeper hook, implement override, old spec/ADR copies, `.forgeflow.json`, `.forgeflow/lifecycle`.
- Writes a 0.2.x `.forgeflow/config.json` while preserving user keys and project checks.
- Rewrites the managed boot anchor in `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`.
- Leaves all old bytes recoverable from the archive tag.

## Usage

```bash
# Inspect first
python3 forgeflow-migrate.py --path ../my-project --dry-run --json

# Apply after review
python3 forgeflow-migrate.py --path ../my-project --apply

# Also create the 0.2.x runtime/config through the installed CLI
python3 forgeflow-migrate.py --path ../my-project --apply --init
```

The target must be a Git repository. The tool does not commit, push, merge, or delete branches. Review and commit the resulting cleanup in the project.

## After migration

```bash
forgeflow init --path . --speckit   # if Spec Kit support is wanted
forgeflow update --dry-run --json
```

Old project artifacts remain available with `git show archive/pre-forgeflow-0.2.1:tasks/...` or a temporary worktree.
