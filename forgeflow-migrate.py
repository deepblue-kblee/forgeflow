#!/usr/bin/env python3
"""One-time migration from ForgeFlow 0.1.x project layouts to 0.2.x.

The active 0.2.0 distribution intentionally does not contain this tool. Run it
from the archive/forgeflow-migrate branch after installing ForgeFlow 0.2.x.

Examples:
  python3 forgeflow-migrate.py --path ../my-project --dry-run --json
  python3 forgeflow-migrate.py --path ../my-project --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ARCHIVE_REF = "archive/pre-forgeflow-0.2.0"
TARGET_VERSION = "0.2.0"

# Legacy paths removed unconditionally after the archive ref is created. The
# archive ref is the recovery source; this tool never deletes without it.
LEGACY_TREES = ("tasks", "docs/releases", "docs/forgeflow")
LEGACY_FILES = (
    ".forgeflow.json",
    ".specify/memory/constitution.md",
    ".specify/extensions.yml",
    ".specify/templates/commands/implement.md",
    "docs/spec/ANTI_PATTERNS.md",
    "docs/adr/001-eliminate-git-sha-and-commit-range-bindings.md",
    "docs/adr/002-remove-spec-body-hash-binding.md",
    "docs/adr/template.md",
)
LEGACY_DIRS = (".forgeflow/lifecycle",)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check)


def is_git_repo(root: Path) -> bool:
    return git(root, "rev-parse", "--git-dir", check=False).returncode == 0


def build_plan(root: Path) -> Dict[str, Any]:
    remove: List[str] = []
    for relative in LEGACY_TREES:
        if (root / relative).exists():
            remove.append(relative)
    for relative in LEGACY_FILES + LEGACY_DIRS:
        if (root / relative).exists():
            remove.append(relative)
    config_path = root / ".forgeflow/config.json"
    previous: Dict[str, Any] = {}
    if config_path.is_file():
        try:
            loaded = json.loads(config_path.read_text(encoding="utf-8"))
            previous = loaded if isinstance(loaded, dict) else {}
        except Exception:
            previous = {}
    if not previous and (root / ".forgeflow.json").is_file():
        try:
            loaded = json.loads((root / ".forgeflow.json").read_text(encoding="utf-8"))
            previous = loaded if isinstance(loaded, dict) else {}
        except Exception:
            previous = {}
    workflow = previous.get("workflow", {})
    workflow = workflow if isinstance(workflow, dict) else {}
    governance = previous.get("governance", {})
    governance = governance if isinstance(governance, dict) else {}
    desired = {
        "forgeflow_version": TARGET_VERSION,
        "workflow": {
            "mode": "lean",
            "owner": workflow.get("owner", "standalone"),
            "checks": workflow.get("checks", []),
            **({"environment": workflow["environment"]} if "environment" in workflow else {}),
            **({"verification_paths": workflow["verification_paths"]} if "verification_paths" in workflow else {}),
        },
        "governance": {
            "max_loop_budget": governance.get("max_loop_budget", 5),
            "auto_create_branch": False,
            "test_timeout_seconds": governance.get("test_timeout_seconds", 300),
        },
    }
    for key, value in previous.items():
        if key not in {"forgeflow_version", "workflow", "governance", "paths"}:
            desired[key] = value
    for key, value in governance.items():
        if key not in {"tasks_dir", "strict_mode", "continuation_policy", "required_documents", "default_tier",
                       "max_loop_budget", "auto_create_branch", "test_timeout_seconds"}:
            desired["governance"][key] = value
    return {
        "schema_version": 1,
        "target_version": TARGET_VERSION,
        "archive_ref": ARCHIVE_REF,
        "root": str(root),
        "remove": sorted(remove),
        "config": desired,
        "config_path": ".forgeflow/config.json",
        "preserve": [
            path for path in ("AGENTS.md", "CLAUDE.md", "GEMINI.md")
            if (root / path).exists()
        ],
        "next_actions": [
            "Review the plan, then rerun with --apply.",
            "After apply, commit the cleaned project and run forgeflow init --path . if runtime files were removed.",
            "0.1.x artifacts remain recoverable from the archive tag.",
        ],
    }


def create_archive_tag(root: Path, ref: str, force: bool = False) -> None:
    exists = git(root, "rev-parse", "-q", "--verify", f"refs/tags/{ref}", check=False)
    if exists.returncode == 0:
        if not force:
            raise SystemExit(f"Archive tag already exists: {ref}. Use --force to move it after reviewing recovery.")
        git(root, "tag", "-d", ref)
    git(root, "tag", "-a", ref, "-m", "Archive ForgeFlow 0.1.x project before 0.2.0 migration")


def remove_path(root: Path, relative: str) -> None:
    path = root / relative
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def update_root_guides(root: Path) -> List[str]:
    updated: List[str] = []
    start = "<!-- forgeflow:boot-anchor:start -->"
    end = "<!-- forgeflow:boot-anchor:end -->"
    anchor = (
        "<!-- forgeflow:boot-anchor:start -->\n"
        "## ForgeFlow 0.2.x Session Entry\n\n"
        "Read `docs/session-state/next-actions.md` if present, `.forgeflow/config.json`, and `.forgeflow/spec/README.md`.\n"
        "Use `forgeflow workflow` for current work. The optional design review checkpoint is `workflow start --hitl design`.\n"
        "Legacy 0.1.x strict lifecycle/audit and `tasks/` artifacts are not current instructions.\n"
        "<!-- forgeflow:boot-anchor:end -->"
    )
    for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        path = root / name
        if path.is_file() and not path.is_symlink():
            content = path.read_text(encoding="utf-8")
            if start in content and end in content:
                import re
                content = re.sub(rf"\n*{re.escape(start)}.*?{re.escape(end)}\n*", "\n", content, flags=re.S).strip()
            content = (content + "\n\n" if content else "") + anchor + "\n"
            write_text(path, content)
            updated.append(name)
    return updated


def apply_plan(root: Path, plan: Dict[str, Any], use_init: bool = False) -> Dict[str, Any]:
    create_archive_tag(root, plan["archive_ref"])
    removed: List[str] = []
    for relative in plan["remove"]:
        remove_path(root, relative)
        removed.append(relative)
    config_path = root / plan["config_path"]
    write_text(config_path, json.dumps(plan["config"], indent=2, ensure_ascii=False) + "\n")
    updated_guides = update_root_guides(root)
    record = {
        "migrated_to": TARGET_VERSION,
        "archive_ref": plan["archive_ref"],
        "removed": removed,
        "updated_guides": updated_guides,
    }
    write_text(root / ".forgeflow" / "migration-0.2.0.json", json.dumps(record, indent=2) + "\n")
    initialized = None
    if use_init:
        result = subprocess.run(
            ["forgeflow", "init", "--path", str(root), "--json"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        initialized = {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    return {
        "status": "applied",
        "root": str(root),
        "archive_ref": plan["archive_ref"],
        "removed": removed,
        "updated_guides": updated_guides,
        "config": str(config_path),
        "initialized": initialized,
        "next_actions": [] if initialized and initialized["returncode"] == 0 else plan["next_actions"],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--archive-ref", default=ARCHIVE_REF)
    parser.add_argument("--force", action="store_true", help="Move an existing archive tag after review")
    parser.add_argument("--init", action="store_true", help="Run the installed 0.2.x forgeflow init after cleanup")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run are mutually exclusive")
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Project path is not a directory: {root}")
    if not is_git_repo(root):
        raise SystemExit("A Git repository is required so the archive ref can preserve old artifacts.")
    plan = build_plan(root)
    plan["archive_ref"] = args.archive_ref
    if not args.apply:
        output = {**plan, "status": "planned", "dry_run": True}
        print(json.dumps(output, indent=2, ensure_ascii=False) if args.json else _human(output))
        return 0
    result = apply_plan(root, plan, use_init=args.init)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else _human(result))
    return 0


def _human(value: Dict[str, Any]) -> str:
    lines = [f"ForgeFlow migration: {value.get('status')}", f"Root: {value.get('root')}",
             f"Archive ref: {value.get('archive_ref')}"]
    if value.get("remove"):
        lines.append("Removed:")
        lines.extend(f"  - {item}" for item in value["remove"])
    if value.get("removed"):
        lines.append("Removed:")
        lines.extend(f"  - {item}" for item in value["removed"])
    if value.get("next_actions"):
        lines.append("Next:")
        lines.extend(f"  - {item}" for item in value["next_actions"])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
