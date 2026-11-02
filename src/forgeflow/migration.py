"""Inventory, plan, and apply legacy project migrations.

The update contract is intentionally conservative:

* no write happens while an active task, unresolved conflict, or plan drift
  exists;
* framework ownership is proven by exact content hashes or a prior managed
  manifest, never by version strings or mtimes;
* every applied mutation has a backup and an operation record;
* historical evidence and user-owned bytes are never rewritten.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ._version import __version__
from . import legacy_assets
from .runtime import package_identity, pin_runtime, preflight_baseline, safe_project_path
from .scaffold import TemplateScaffolder

SCHEMA_VERSION = 1
CONFIG_REL = ".forgeflow/config.json"
LEGACY_CONFIG_REL = ".forgeflow.json"
MANIFEST_REL = ".forgeflow/managed-assets.json"
MIGRATION_DIR = ".forgeflow/migrations"
BACKUP_DIR = ".forgeflow/migration-backups"

PROTECTED_PREFIXES = (".git", ".forgeflow/runtime", ".forgeflow/migrations", ".forgeflow/migration-backups")

CLASS_MISSING = "missing"
CLASS_MANAGED_UNMODIFIED = "framework-owned-unmodified"
CLASS_USER_MODIFIED = "user-modified-or-unknown"
CLASS_HISTORICAL = "historical-evidence"
CLASS_ACTIVE = "active-baseline-dependent"

ACTION_NONE = "none"
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_REMOVE = "remove"
ACTION_PRESERVE = "preserve"
ACTION_CONFLICT = "conflict"

EXIT_CODES = {
    "applied": 0,
    "no-op": 0,
    "planned": 0,
    "needs-action": 3,
    "failed-rolled-back": 1,
    "partial": 4,
    "error": 1,
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    return legacy_assets.sha256_file(path)


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_protected(relative: str) -> bool:
    return any(relative == prefix or relative.startswith(prefix + "/") for prefix in PROTECTED_PREFIXES)


def _assert_relative_writable(relative: str) -> None:
    if not relative or relative.startswith("/") or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise ValueError(f"Unsafe migration path: {relative}")
    if _is_protected(relative):
        raise ValueError(f"Protected migration path: {relative}")


def _resource_content(resource: str) -> str:
    return TemplateScaffolder.get_template_content(resource)


def _desired_manifest(asset_hashes: Dict[str, str]) -> str:
    payload = {
        "version": SCHEMA_VERSION,
        "distribution_version": __version__,
        "distribution_identity": package_identity(),
        "assets": {path: digest for path, digest in sorted(asset_hashes.items())},
    }
    return json.dumps(payload, indent=2) + "\n"


def load_project_config(root: Path) -> Dict[str, Any]:
    modern = safe_project_path(root, CONFIG_REL)
    legacy = safe_project_path(root, LEGACY_CONFIG_REL)
    if not modern.exists() and not legacy.exists():
        raise ValueError(
            f"Target directory '{root}' is not a valid ForgeFlow repository (.forgeflow/config.json missing)."
        )
    source = modern if modern.exists() else legacy
    TemplateScaffolder._assert_safe_file(source, root)
    try:
        config = json.loads(source.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse {source.name}: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("ForgeFlow configuration must be an object")
    if not isinstance(config.get("governance", {}), dict):
        raise ValueError("governance configuration must be an object")
    return {
        "config": config,
        "source": source,
        "modern_exists": modern.exists(),
        "legacy_exists": legacy.exists(),
        "modern": modern,
        "legacy": legacy,
    }


def _workflow_states(root: Path) -> Iterable[Tuple[str, Dict[str, Any]]]:
    state_dir = safe_project_path(root, ".forgeflow/workflows")
    if not state_dir.exists():
        return []
    results: List[Tuple[str, Dict[str, Any]]] = []
    for state_file in sorted(state_dir.glob("*.json")):
        TemplateScaffolder._assert_safe_file(state_file, root)
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state = {"status": "unreadable"}
        if isinstance(state, dict):
            results.append((state_file.stem, state))
    return results


def active_work_details(root: Path, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    details: List[Dict[str, Any]] = []
    for task_id, state in _workflow_states(root):
        if state.get("finalization_complete") is True:
            continue
        if state.get("status") in {"cleaned", "completed", "cancelled"}:
            continue
        baseline = state.get("baseline") if isinstance(state.get("baseline"), dict) else {}
        details.append({
            "task": task_id,
            "kind": "workflow",
            "status": state.get("status"),
            "baseline_identity": baseline.get("identity"),
            "baseline_version": baseline.get("version"),
            "resume_command": baseline.get("command"),
        })

    lifecycle_dir = safe_project_path(root, ".forgeflow/lifecycle")
    if lifecycle_dir.exists():
        for state_file in sorted(lifecycle_dir.glob("*.json")):
            TemplateScaffolder._assert_safe_file(state_file, root)
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except Exception:
                state = {}
            status = state.get("status", state.get("progress", {}).get("status"))
            if status != "COMPLETE":
                details.append({
                    "task": state_file.stem,
                    "kind": "strict-lifecycle",
                    "status": status,
                    "baseline_identity": None,
                    "baseline_version": None,
                    "resume_command": None,
                })

    governance = config.get("governance", {})
    tasks_name = governance.get("tasks_dir", "tasks") if isinstance(governance, dict) else "tasks"
    in_progress = safe_project_path(root, str(Path(tasks_name) / "in-progress"))
    scan_dirs = [in_progress]
    paths = config.get("paths", {})
    if isinstance(paths, dict) and isinstance(paths.get("in_progress"), str):
        configured = safe_project_path(root, paths["in_progress"])
        if configured != in_progress:
            scan_dirs.append(configured)
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for package in sorted(scan_dir.iterdir()):
            if package.is_symlink():
                details.append({
                    "task": package.name,
                    "kind": "unsafe-symlink",
                    "status": "unsafe",
                    "baseline_identity": None,
                    "baseline_version": None,
                    "resume_command": None,
                })
                continue
            if package.is_dir() and not package.name.startswith("."):
                details.append({
                    "task": package.name,
                    "kind": "task-package",
                    "status": "in-progress",
                    "baseline_identity": None,
                    "baseline_version": None,
                    "resume_command": None,
                })
    return details


def _load_manifest(root: Path) -> Dict[str, str]:
    path = safe_project_path(root, MANIFEST_REL)
    if not path.exists():
        return {}
    TemplateScaffolder._assert_safe_file(path, root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    assets = payload.get("assets")
    if not isinstance(assets, dict):
        return {}
    return {str(k): str(v) for k, v in assets.items()}


def _pending_migration(root: Path) -> Optional[Dict[str, Any]]:
    directory = safe_project_path(root, MIGRATION_DIR)
    if not directory.exists():
        return None
    for journal in sorted(directory.glob("*.json")):
        TemplateScaffolder._assert_safe_file(journal, root)
        try:
            payload = json.loads(journal.read_text(encoding="utf-8"))
        except Exception:
            return {
                "id": journal.stem,
                "path": _rel(root, journal),
                "status": "unreadable",
            }
        if not isinstance(payload, dict):
            return {"id": journal.stem, "path": _rel(root, journal), "status": "invalid"}
        if payload.get("status") not in {"applied", "recovered"}:
            return {"id": payload.get("id", journal.stem), "path": _rel(root, journal), "status": payload.get("status")}
    return None


def _git_blockers(root: Path, targets: Iterable[str]) -> List[Dict[str, Any]]:
    blockers: List[Dict[str, Any]] = []
    git_dir = root / ".git"
    if not git_dir.exists():
        return blockers
    for marker, operation in (
        ("MERGE_HEAD", "merge"),
        ("CHERRY_PICK_HEAD", "cherry-pick"),
        ("REVERT_HEAD", "revert"),
        ("BISECT_LOG", "bisect"),
    ):
        if (git_dir / marker).exists():
            blockers.append({
                "kind": "git-operation-in-progress",
                "operation": operation,
                "reason": f"Git {operation} is in progress; update will not change files.",
                "next_action": f"Finish or abort the {operation}, then rerun forgeflow update.",
            })
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        blockers.append({
            "kind": "git-operation-in-progress",
            "operation": "rebase",
            "reason": "Git rebase is in progress; update will not change files.",
            "next_action": "Finish or abort the rebase, then rerun forgeflow update.",
        })
    target_set = set(targets)
    if target_set:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "diff", "--cached", "--name-only", "-z"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            return blockers
        if result.returncode == 0:
            staged = {name for name in result.stdout.split("\0") if name}
            overlap = sorted(staged & target_set)
            if overlap:
                blockers.append({
                    "kind": "staged-target-changes",
                    "paths": overlap,
                    "reason": "Target files have staged changes; applying update would mix index and worktree state.",
                    "next_action": "Unstage or commit the target paths, then rerun forgeflow update.",
                })
    return blockers


def _root_guide_binding_action(root: Path, relative: str) -> Dict[str, Any]:
    path = safe_project_path(root, relative)
    if not path.exists():
        return {"action": ACTION_NONE}
    TemplateScaffolder._assert_safe_file(path, root)
    content = path.read_text(encoding="utf-8")
    start, end = TemplateScaffolder.BINDING_START, TemplateScaffolder.BINDING_END
    starts, ends = content.count(start), content.count(end)
    expected = TemplateScaffolder.governance_binding().strip()
    if starts == ends == 0:
        if TemplateScaffolder.LEGACY_BINDING_HEADING in content:
            if content.count(TemplateScaffolder.LEGACY_BINDING_HEADING) == 1 and TemplateScaffolder.LEGACY_BINDING in content:
                updated = content.replace(
                    TemplateScaffolder.LEGACY_BINDING,
                    TemplateScaffolder.governance_binding().strip(),
                    1,
                )
                return {
                    "action": ACTION_UPDATE,
                    "content": updated,
                    "classification": CLASS_MANAGED_UNMODIFIED,
                    "reason": "Replace the known legacy governance binding with the current lean reference.",
                }
            return {
                "action": ACTION_CONFLICT,
                "classification": CLASS_USER_MODIFIED,
                "reason": "Unrecognized legacy governance binding markers; preserve user content and resolve explicitly.",
            }
        return {"action": ACTION_NONE}
    if starts != ends:
        return {
            "action": ACTION_CONFLICT,
            "classification": CLASS_USER_MODIFIED,
            "reason": "Mismatched ForgeFlow governance binding markers.",
        }
    if starts != 1:
        return {
            "action": ACTION_CONFLICT,
            "classification": CLASS_USER_MODIFIED,
            "reason": "Duplicate ForgeFlow governance binding blocks.",
        }
    start_index, end_index = content.find(start), content.find(end)
    block = content[start_index:end_index + len(end)].strip() if start_index <= end_index else ""
    if block == expected:
        return {"action": ACTION_NONE}
    return {
        "action": ACTION_CONFLICT,
        "classification": CLASS_USER_MODIFIED,
        "reason": "ForgeFlow governance binding block was modified; preserve it and resolve explicitly.",
    }


def _boot_anchor_decision(root: Path, relative: str, base_content: Optional[str] = None) -> Dict[str, Any]:
    path = root / relative
    if path.is_symlink():
        return {"action": ACTION_CONFLICT, "reason": "Root guide is a symbolic link; not modified."}
    if not path.is_file():
        return {"action": ACTION_NONE}
    path = safe_project_path(root, relative)
    content = path.read_text(encoding="utf-8") if base_content is None else base_content
    start, end = TemplateScaffolder.BOOT_ANCHOR_START, TemplateScaffolder.BOOT_ANCHOR_END
    if content.count(start) != content.count(end) or content.count(start) > 1:
        return {
            "action": ACTION_CONFLICT,
            "reason": "Duplicate or mismatched ForgeFlow boot-anchor markers.",
        }
    pattern = re.compile(
        rf"\n*{re.escape(start)}.*?{re.escape(end)}\n*",
        re.DOTALL,
    )
    match = re.search(rf"{re.escape(start)}.*?{re.escape(end)}", content, re.DOTALL)
    if match:
        existing_block = match.group(0).strip()
        known = {
            TemplateScaffolder.BOOT_ANCHOR_TEMPLATE.strip(),
            legacy_assets.LEGACY_BOOT_ANCHOR.strip(),
        }
        if existing_block not in known:
            return {
                "action": ACTION_CONFLICT,
                "reason": "Boot-anchor block contains user modifications; preserve it and resolve explicitly.",
            }
    clean = pattern.sub("\n\n", content).strip()
    anchor = TemplateScaffolder.BOOT_ANCHOR_TEMPLATE.strip()
    desired = (clean + "\n\n" + anchor + "\n") if clean else anchor + "\n"
    if desired == content:
        return {"action": ACTION_NONE}
    return {"action": ACTION_UPDATE, "content": desired, "reason": "Refresh the managed boot-anchor block."}


def _classify_existing(relative: str, current: Optional[str], desired: Optional[str],
                       manifest: Dict[str, str]) -> Tuple[str, str]:
    if current is None:
        return CLASS_MISSING, "Required framework asset is missing."
    if desired is not None and current == desired:
        return CLASS_MANAGED_UNMODIFIED, "Already matches the executing distribution."
    if legacy_assets.is_known_legacy(relative, current):
        return CLASS_MANAGED_UNMODIFIED, f"Exact v0.1.24 generated asset ({legacy_assets.V0_1_24_COMMIT})."
    if manifest.get(relative) == current:
        return CLASS_MANAGED_UNMODIFIED, "Matches the recorded managed-asset manifest."
    return CLASS_USER_MODIFIED, "Bytes are not a known framework asset; preserve user content."


def _asset(
    relative: str,
    *,
    action: str,
    classification: str,
    reason: str,
    current: Optional[str] = None,
    desired: Optional[str] = None,
    executable: bool = False,
    accepted: bool = False,
) -> Dict[str, Any]:
    return {
        "path": relative,
        "action": action,
        "classification": classification,
        "reason": reason,
        "current_sha256": current,
        "desired_sha256": desired,
        "executable": executable,
        "accepted": accepted,
    }


def build_update_plan(root: Path, *, accept_paths: Iterable[str] = ()) -> Dict[str, Any]:
    """Build a write-free migration plan for a project."""
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Project root must be a real directory")
    root = root.resolve(strict=True)
    accepted_paths = {path.replace("\\", "/") for path in accept_paths}
    state = load_project_config(root)
    config = state["config"]
    governance = config.get("governance", {})
    tasks_name = governance.get("tasks_dir", "tasks")
    if not isinstance(tasks_name, str):
        raise ValueError("governance.tasks_dir must be a relative directory")
    if "tasks_dir" not in governance and (root / "tasks").exists() and not (root / "tasks").is_dir():
        tasks_name = "ff-tasks"
    workflow_mode = config.get("workflow", {}).get("mode") if isinstance(config.get("workflow"), dict) else None
    explicit_strict = workflow_mode == "strict"
    manifest = _load_manifest(root)
    running_identity = package_identity()

    blockers: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    warnings: List[str] = []
    assets: List[Dict[str, Any]] = []
    desired_by_path: Dict[str, str] = {}
    managed_hashes: Dict[str, str] = {}

    # Active work is always a write barrier, even when it already uses this build.
    active = active_work_details(root, config)
    if active:
        for item in active:
            next_action = (
                f"Resume with: {item['resume_command']}"
                if item.get("resume_command")
                else "Preserve the previous installation and obtain a pinned runtime before upgrading; "
                     "do not delete state to bypass the barrier."
            )
            blockers.append({
                "kind": "active-work",
                "task": item["task"],
                "task_kind": item["kind"],
                "status": item.get("status"),
                "baseline_identity": item.get("baseline_identity"),
                "baseline_version": item.get("baseline_version"),
                "resume_command": item.get("resume_command"),
                "reason": "Active work keeps its recorded runtime/spec baseline.",
                "next_action": next_action,
            })
    pending = _pending_migration(root)
    if pending:
        blockers.append({
            "kind": "pending-migration",
            "migration": pending["id"],
            "path": pending["path"],
            "reason": "A previous migration did not reach a terminal state.",
            "next_action": f"Run 'forgeflow update --recover {pending['id']}' after reviewing the journal.",
        })

    # Config migration. Legacy strict_mode is preserved; explicit workflow.mode=strict
    # prevents automatic lean conversion of legacy instructions.
    spec = TemplateScaffolder.lean_asset_specs(
        root,
        config,
        speckit=(root / ".specify").is_dir(),
        skip_config=True,
    )
    desired_config = spec["desired_config"]
    desired_config["forgeflow_version"] = __version__
    if explicit_strict:
        desired_config.setdefault("workflow", {})["mode"] = "strict"
    elif workflow_mode is None and governance.get("strict_mode") is True:
        warnings.append(
            "Legacy governance.strict_mode was preserved, but the new workflow.mode was set to lean because "
            "v0.1.24 used strict_mode as a framework default. Use workflow.mode=strict to keep strict assets."
        )
    if state["legacy_exists"] and state["modern_exists"]:
        try:
            legacy_data = json.loads(state["legacy"].read_text(encoding="utf-8"))
        except Exception:
            legacy_data = None
        if isinstance(legacy_data, dict) and legacy_data != config:
            warnings.append(
                ".forgeflow.json and .forgeflow/config.json both exist; the modern path is authoritative and "
                "the legacy file is preserved as recovery evidence."
            )
    config_rel = _rel(root, state["modern"]) if state["modern_exists"] else CONFIG_REL
    current_config_text = state["source"].read_text(encoding="utf-8")
    desired_config_text = json.dumps(desired_config, indent=2, ensure_ascii=False) + "\n"
    desired_config_hash = legacy_assets.sha256_text(desired_config_text)
    managed_hashes[config_rel] = desired_config_hash
    if desired_config_text != current_config_text:
        assets.append(_asset(
            config_rel,
            action=ACTION_UPDATE if state["modern_exists"] else ACTION_CREATE,
            classification=CLASS_MANAGED_UNMODIFIED if state["modern_exists"] else CLASS_MISSING,
            reason="Preserve user keys, add missing lean schema, and record the current distribution version.",
            current=_sha256(state["modern"]) if state["modern_exists"] else None,
            desired=desired_config_hash,
        ))
        desired_by_path[config_rel] = desired_config_text
    else:
        assets.append(_asset(
            config_rel,
            action=ACTION_NONE,
            classification=CLASS_MANAGED_UNMODIFIED,
            reason="Configuration already matches the executing distribution schema.",
            current=_sha256(state["modern"]),
            desired=desired_config_hash,
        ))
    if state["legacy_exists"]:
        assets.append(_asset(
            LEGACY_CONFIG_REL,
            action=ACTION_PRESERVE,
            classification=CLASS_MANAGED_UNMODIFIED,
            reason="Legacy config is recovery evidence; it is never deleted or silently merged.",
            current=_sha256(state["legacy"]),
        ))

    # Shared lean assets.
    for path, (content, executable) in spec["desired"].items():
        relative = _rel(root, path)
        _assert_relative_writable(relative)
        current = _sha256(path)
        if explicit_strict and relative.startswith(".specify/") and current is not None:
            assets.append(_asset(relative, action=ACTION_PRESERVE, classification=CLASS_MANAGED_UNMODIFIED,
                                 reason="Explicit workflow.mode=strict keeps Spec Kit support assets.", current=current))
            continue
        desired_by_path[relative] = content
        desired_hash = legacy_assets.sha256_text(content)
        managed_hashes[relative] = desired_hash
        classification, reason = _classify_existing(relative, current, desired_hash, manifest)
        if classification == CLASS_USER_MODIFIED:
            conflicts.append({
                "path": relative,
                "reason": reason,
                "current_sha256": current,
                "next_action": f"Review the file, then rerun with --accept {relative} to replace it with the framework version.",
            })
            assets.append(_asset(relative, action=ACTION_CONFLICT, classification=classification,
                                 reason=reason, current=current, desired=desired_hash))
        elif current is None:
            assets.append(_asset(relative, action=ACTION_CREATE, classification=CLASS_MISSING,
                                 reason=reason, desired=desired_hash, executable=executable))
        elif current != desired_hash:
            assets.append(_asset(relative, action=ACTION_UPDATE, classification=classification,
                                 reason=reason, current=current, desired=desired_hash,
                                 executable=executable))
        else:
            assets.append(_asset(relative, action=ACTION_NONE, classification=CLASS_MANAGED_UNMODIFIED,
                                 reason=reason, current=current, desired=desired_hash,
                                 executable=executable))

    # Legacy Spec Kit and generated documentation assets.
    for relative, legacy_hash in legacy_assets.LEGACY_FILE_SHA256.items():
        path = safe_project_path(root, relative)
        if not path.exists():
            continue
        TemplateScaffolder._assert_safe_file(path, root)
        current = _sha256(path)
        resource = legacy_assets.RESOURCE_REPLACEMENTS.get(relative)
        if explicit_strict:
            assets.append(_asset(relative, action=ACTION_PRESERVE, classification=CLASS_MANAGED_UNMODIFIED,
                                 reason="Explicit workflow.mode=strict keeps legacy assets.", current=current))
            continue
        if resource is None:
            continue
        desired = _resource_content(resource)
        desired_hash = legacy_assets.sha256_text(desired)
        managed_hashes[relative] = desired_hash
        if current == desired_hash:
            assets.append(_asset(relative, action=ACTION_NONE, classification=CLASS_MANAGED_UNMODIFIED,
                                 reason="Already matches the executing distribution.", current=current))
            continue
        if current == legacy_hash:
            classification = CLASS_MANAGED_UNMODIFIED
            reason = f"Exact v0.1.24 generated asset ({legacy_assets.V0_1_24_COMMIT}); replace with the current framework asset."
        elif manifest.get(relative) == current:
            classification = CLASS_MANAGED_UNMODIFIED
            reason = "Matches the recorded managed-asset manifest."
        else:
            classification = CLASS_USER_MODIFIED
            reason = "Bytes differ from the known v0.1.24 asset; preserve user content."
        if classification == CLASS_USER_MODIFIED:
            conflicts.append({
                "path": relative,
                "reason": reason,
                "current_sha256": current,
                "next_action": f"Review the file, then rerun with --accept {relative} to replace it with the framework version.",
            })
            assets.append(_asset(relative, action=ACTION_CONFLICT, classification=classification,
                                 reason=reason, current=current, desired=desired_hash))
        else:
            assets.append(_asset(relative, action=ACTION_UPDATE, classification=classification,
                                 reason=reason, current=current, desired=desired_hash,
                                 executable=relative.startswith(".specify/scripts/")))
            desired_by_path[relative] = desired

    for relative, replacement in legacy_assets.LEAN_FILE_REPLACEMENTS.items():
        path = safe_project_path(root, relative)
        if not path.exists():
            continue
        TemplateScaffolder._assert_safe_file(path, root)
        current = _sha256(path)
        desired_hash = legacy_assets.sha256_text(replacement)
        managed_hashes[relative] = desired_hash
        if explicit_strict:
            assets.append(_asset(relative, action=ACTION_PRESERVE, classification=CLASS_MANAGED_UNMODIFIED,
                                 reason="Explicit workflow.mode=strict keeps legacy instructions.", current=current))
            continue
        if current == desired_hash:
            assets.append(_asset(relative, action=ACTION_NONE, classification=CLASS_MANAGED_UNMODIFIED,
                                 reason="Already matches the lean replacement.", current=current))
            continue
        if current == legacy_assets.LEGACY_INLINE_SHA256.get(relative) or manifest.get(relative) == current:
            assets.append(_asset(relative, action=ACTION_UPDATE,
                                 classification=CLASS_MANAGED_UNMODIFIED,
                                 reason="Replace the known legacy strict instruction with the lean contract.",
                                 current=current, desired=desired_hash))
            desired_by_path[relative] = replacement
        else:
            conflicts.append({
                "path": relative,
                "reason": "Legacy instruction was modified by the user; preserve it and resolve explicitly.",
                "current_sha256": current,
                "next_action": f"Review the file, then rerun with --accept {relative} to replace it with the lean version.",
            })
            assets.append(_asset(relative, action=ACTION_CONFLICT, classification=CLASS_USER_MODIFIED,
                                 reason="User-modified legacy instruction.", current=current,
                                 desired=desired_hash))

    # Root guide binding block.
    for guide in TemplateScaffolder.ROOT_GUIDES:
        guide_path = root / guide
        if guide_path.is_symlink():
            assets.append(_asset(guide, action=ACTION_CONFLICT, classification=CLASS_USER_MODIFIED,
                                 reason="Root guide is a symbolic link; not modified.", current=None))
            conflicts.append({
                "path": guide,
                "reason": "Root guide is a symbolic link; not modified.",
                "current_sha256": None,
                "next_action": "Replace the symlink with a regular file or update its target manually.",
            })
            continue
        if not guide_path.is_file():
            continue
        decision = _root_guide_binding_action(root, guide)
        if decision["action"] == ACTION_NONE:
            continue
        assets.append(_asset(
            guide,
            action=decision["action"],
            classification=decision.get("classification", CLASS_USER_MODIFIED),
            reason=decision["reason"],
            current=_sha256(safe_project_path(root, guide)),
            desired=legacy_assets.sha256_text(decision["content"]) if decision.get("content") else None,
        ))
        if decision["action"] == ACTION_CONFLICT:
            conflicts.append({
                "path": guide,
                "reason": decision["reason"],
                "current_sha256": _sha256(safe_project_path(root, guide)),
                "next_action": f"Repair or remove the block manually; --accept does not overwrite root guide bodies.",
            })
        else:
            desired_by_path[guide] = decision["content"]

    # Managed boot anchors keep user bodies while refreshing the framework block.
    for guide in TemplateScaffolder.ROOT_GUIDES:
        guide_path = root / guide
        if guide_path.is_symlink() or not guide_path.exists():
            continue
        decision = _boot_anchor_decision(root, guide, desired_by_path.get(guide))
        if decision["action"] == ACTION_NONE:
            continue
        assets.append(_asset(
            guide,
            action=decision["action"],
            classification=CLASS_MANAGED_UNMODIFIED if decision["action"] == ACTION_UPDATE else CLASS_USER_MODIFIED,
            reason=decision["reason"],
            current=_sha256(safe_project_path(root, guide)),
            desired=legacy_assets.sha256_text(decision["content"]) if decision.get("content") else None,
        ))
        if decision["action"] == ACTION_CONFLICT:
            conflicts.append({
                "path": guide,
                "reason": decision["reason"],
                "current_sha256": _sha256(safe_project_path(root, guide)),
                "next_action": "Repair the anchor markers manually; --accept does not overwrite root guide bodies.",
            })
        else:
            desired_by_path[guide] = decision["content"]

    if not any((root / guide).exists() or (root / guide).is_symlink() for guide in TemplateScaffolder.ROOT_GUIDES):
        anchor = TemplateScaffolder.BOOT_ANCHOR_TEMPLATE.strip() + "\n"
        assets.append(_asset(
            "AGENTS.md",
            action=ACTION_CREATE,
            classification=CLASS_MISSING,
            reason="Create the default root guide and managed boot anchor.",
            desired=legacy_assets.sha256_text(anchor),
        ))
        desired_by_path["AGENTS.md"] = anchor

    # Managed manifest is generated from the stable set of framework-generated assets.
    manifest_text = _desired_manifest(managed_hashes)
    manifest_relative = MANIFEST_REL
    manifest_path = safe_project_path(root, manifest_relative)
    manifest_current = _sha256(manifest_path)
    manifest_desired = legacy_assets.sha256_text(manifest_text)
    if manifest_current != manifest_desired:
        assets.append(_asset(
            manifest_relative,
            action=ACTION_CREATE if manifest_current is None else ACTION_UPDATE,
            classification=CLASS_MISSING if manifest_current is None else CLASS_MANAGED_UNMODIFIED,
            reason="Record framework-owned paths and applied content identities for future updates.",
            current=manifest_current,
            desired=manifest_desired,
        ))
        desired_by_path[manifest_relative] = manifest_text

    # .gitignore managed entries.
    gitignore = safe_project_path(root, ".gitignore")
    required_entries = [
        ".forgeflow/runtime/",
        ".forgeflow/runtime.json",
        ".forgeflow/run.py",
        ".forgeflow/spec",
        ".forgeflow/workflows/.*.lock",
        ".forgeflow/lifecycle/.*.lock",
        ".forgeflow/migrations/",
        ".forgeflow/migration-backups/",
    ]
    existing_gitignore = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    missing_entries = [entry for entry in required_entries if entry not in existing_gitignore.splitlines()]
    if missing_entries:
        desired_gitignore = existing_gitignore.rstrip() + ("\n" if existing_gitignore.strip() else "") + "\n".join(missing_entries) + "\n"
        assets.append(_asset(
            ".gitignore",
            action=ACTION_UPDATE if gitignore.exists() else ACTION_CREATE,
            classification=CLASS_MANAGED_UNMODIFIED if gitignore.exists() else CLASS_MISSING,
            reason="Ignore runtime snapshots and migration records; existing user lines are preserved.",
            current=_sha256(gitignore),
            desired=legacy_assets.sha256_text(desired_gitignore),
        ))
        desired_by_path[".gitignore"] = desired_gitignore

    # Tasks structure must match config.
    _assert_relative_writable(tasks_name)
    configured_paths = config.get("paths", {})
    if isinstance(configured_paths, dict):
        configured_in_progress = configured_paths.get("in_progress")
        expected_in_progress = f"{tasks_name}/in-progress"
        if isinstance(configured_in_progress, str) and configured_in_progress != expected_in_progress:
            warnings.append(
                f"config.paths.in_progress ({configured_in_progress}) differs from governance.tasks_dir; "
                "both paths were inspected and will be preserved."
            )
    tasks_dir = safe_project_path(root, tasks_name)
    if tasks_dir.exists() and not tasks_dir.is_dir():
        blockers.append({
            "kind": "tasks-path-not-directory",
            "path": tasks_name,
            "reason": "Configured tasks_dir exists but is not a directory.",
            "next_action": "Move the file or correct governance.tasks_dir, then rerun update.",
        })
    for directory in (tasks_name, f"{tasks_name}/in-progress", f"{tasks_name}/completed"):
        path = safe_project_path(root, directory)
        if not path.exists():
            assets.append(_asset(directory, action=ACTION_CREATE, classification=CLASS_MISSING,
                                 reason="Required task directory for the configured tasks_dir."))

    # Historical evidence is never scanned or rewritten.
    for prefix in ("tasks/completed", "docs/releases"):
        path = root / prefix
        if path.exists():
            assets.append(_asset(prefix, action=ACTION_PRESERVE, classification=CLASS_HISTORICAL,
                                 reason="Historical evidence is immutable for update."))

    # Apply explicit conflict resolution.
    accepted: List[str] = []
    for relative in sorted(accepted_paths):
        _assert_relative_writable(relative)
        match = next((item for item in conflicts if item["path"] == relative), None)
        if match is None:
            raise ValueError(f"--accept path is not a known unresolved conflict: {relative}")
        if relative in {guide for guide in TemplateScaffolder.ROOT_GUIDES}:
            raise ValueError(f"--accept cannot overwrite a root guide body: {relative}")
        target = safe_project_path(root, relative)
        current = _sha256(target)
        if current != match["current_sha256"]:
            raise ValueError(f"Accepted path changed after planning: {relative}")
        decision = next(item for item in assets if item["path"] == relative)
        decision["action"] = ACTION_UPDATE
        decision["accepted"] = True
        conflicts = [item for item in conflicts if item["path"] != relative]
        accepted.append(relative)
        if decision["desired_sha256"] is not None:
            # Content is rebuilt below from the caller's canonical source.
            pass

    # Resolve accepted content from the canonical builders.
    for relative in accepted:
        content = _canonical_content_for(root, relative, spec, desired_config)
        if content is None:
            raise ValueError(f"No canonical replacement is available for accepted path: {relative}")
        desired_by_path[relative] = content
        decision = next(item for item in assets if item["path"] == relative)
        decision["desired_sha256"] = legacy_assets.sha256_text(content)

    # Plan drift and Git safety.
    write_targets = [item["path"] for item in assets if item["action"] in {ACTION_CREATE, ACTION_UPDATE}]
    blockers.extend(_git_blockers(root, write_targets))
    if conflicts:
        blockers.extend({
            "kind": "unresolved-conflict",
            "path": item["path"],
            "reason": item["reason"],
            "next_action": item["next_action"],
        } for item in conflicts)

    deduped: Dict[str, Dict[str, Any]] = {}
    for item in assets:
        deduped[item["path"]] = item
    assets = list(deduped.values())

    baseline_file = safe_project_path(root, ".forgeflow/runtime.json")
    previous_baseline: Dict[str, Any] = {}
    if baseline_file.exists():
        try:
            previous_baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
        except Exception:
            previous_baseline = {}
    baseline_update = not active and previous_baseline.get("identity") != running_identity
    if baseline_update:
        try:
            preflight_baseline(root)
        except Exception as exc:
            blockers.append({
                "kind": "unsafe-baseline-target",
                "reason": str(exc),
                "next_action": "Preserve the reported user file/link, choose a separate baseline, then rerun update.",
            })
            baseline_update = False

    status = "needs-action" if blockers else "planned"
    if not blockers and not write_targets and not baseline_update:
        status = "no-op"

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "complete": status == "no-op",
        "target_dir": str(root),
        "dry_run": True,
        "previous_version": config.get("forgeflow_version", "unknown"),
        "current_version": __version__,
        "distribution": {"version": __version__, "identity": running_identity},
        "project_runtime": {
            "version": previous_baseline.get("version"),
            "identity": previous_baseline.get("identity"),
            "next_identity": running_identity if baseline_update else previous_baseline.get("identity"),
        },
        "baseline_update": baseline_update,
        "assets": assets,
        "desired": desired_by_path,
        "blockers": blockers,
        "conflicts": conflicts,
        "warnings": warnings,
        "accepted": accepted,
        "created_files": [],
        "updated_files": [],
        "removed_files": [],
        "created_dirs": [],
        "preserved_files": sorted({item["path"] for item in assets if item["action"] in {ACTION_PRESERVE, ACTION_NONE}}),
        "next_actions": [item["next_action"] for item in blockers if item.get("next_action")],
        "config_changed": any(item["path"] == config_rel and item["action"] in {ACTION_CREATE, ACTION_UPDATE} for item in assets),
        "preserved_legacy_config": state["legacy_exists"],
        "_state": state,
        "_spec": spec,
        "_tasks_name": tasks_name,
    }


def _canonical_content_for(root: Path, relative: str, spec: Dict[str, Any],
                           desired_config: Dict[str, Any]) -> Optional[str]:
    if relative in legacy_assets.LEAN_FILE_REPLACEMENTS:
        return legacy_assets.LEAN_FILE_REPLACEMENTS[relative]
    if relative in legacy_assets.RESOURCE_REPLACEMENTS:
        return _resource_content(legacy_assets.RESOURCE_REPLACEMENTS[relative])
    for path, (content, _executable) in spec["desired"].items():
        if _rel(root, path) == relative:
            return content
    if relative == ".forgeflow/config.json":
        return json.dumps(desired_config, indent=2, ensure_ascii=False) + "\n"
    return None


def _backup_path(root: Path, operation_id: str, relative: str) -> Path:
    return safe_project_path(root, f"{BACKUP_DIR}/{operation_id}/{relative}")


def _write_text_atomic(path: Path, content: str, root: Path) -> None:
    import tempfile
    TemplateScaffolder._assert_safe_file(path, root, allow_missing=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.forgeflow-", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _record_journal(root: Path, operation_id: str, payload: Dict[str, Any]) -> None:
    journal = safe_project_path(root, f"{MIGRATION_DIR}/{operation_id}.json")
    journal.parent.mkdir(parents=True, exist_ok=True)
    _write_text_atomic(journal, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", root)


def apply_update_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    root = Path(plan["target_dir"])
    state = plan["_state"]
    spec = plan["_spec"]
    desired = plan["desired"]
    operation_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]

    writes = [
        item for item in plan["assets"]
        if item["action"] in {ACTION_CREATE, ACTION_UPDATE} and item["path"] in desired
    ]
    # Pre-validate every read before the first write.
    for item in writes:
        relative = item["path"]
        _assert_relative_writable(relative)
        path = safe_project_path(root, relative)
        if path.exists():
            try:
                mode = path.lstat().st_mode
            except OSError as exc:
                plan["status"] = "needs-action"
                plan["complete"] = False
                plan["blockers"].append({
                    "kind": "unsafe-target",
                    "path": relative,
                    "reason": f"Cannot inspect target: {exc}",
                    "next_action": "Replace the target with a regular file, then rerun update.",
                })
                return plan
            if not stat.S_ISREG(mode) or path.lstat().st_nlink > 1:
                plan["status"] = "needs-action"
                plan["complete"] = False
                plan["blockers"].append({
                    "kind": "unsafe-target",
                    "path": relative,
                    "reason": "Target is not a regular single-link file.",
                    "next_action": "Replace the target with a regular file, then rerun update.",
                })
                return plan
        current = _sha256(path)
        if current != item["current_sha256"]:
            plan["status"] = "needs-action"
            plan["complete"] = False
            plan["blockers"].append({
                "kind": "plan-drift",
                "path": relative,
                "reason": "The file changed after planning; no files were written.",
                "next_action": "Rerun forgeflow update to review the new content.",
            })
            return plan

    created_dirs: List[str] = []
    created_files: List[str] = []
    updated_files: List[str] = []
    removed_files: List[str] = []
    backup_dir_rel = f"{BACKUP_DIR}/{operation_id}"
    journal_entries: List[Dict[str, Any]] = []

    try:
        for item in writes:
            relative = item["path"]
            path = safe_project_path(root, relative)
            missing_parents: List[Path] = []
            parent = path.parent
            while parent != root and not parent.exists():
                missing_parents.append(parent)
                parent = parent.parent
            for missing in reversed(missing_parents):
                missing.mkdir()
                created_dirs.append(_rel(root, missing))
            if path.exists():
                _assert_relative_writable(relative)
                backup = _backup_path(root, operation_id, relative)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup)
                journal_entries.append({"path": relative, "operation": "replaced", "backup": _rel(root, backup)})
                updated_files.append(relative)
            else:
                journal_entries.append({"path": relative, "operation": "created", "backup": None})
                created_files.append(relative)

        for directory in [item["path"] for item in plan["assets"] if item["action"] == ACTION_CREATE and item["path"] not in desired]:
            path = safe_project_path(root, directory)
            if path.exists():
                continue
            path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(directory)

        _record_journal(root, operation_id, {
            "id": operation_id,
            "status": "applying",
            "started_at": _now(),
            "plan_status": plan["status"],
            "entries": journal_entries,
        })
        entry_by_path = {entry["path"]: entry for entry in journal_entries}
        for item in writes:
            relative = item["path"]
            path = safe_project_path(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            _write_text_atomic(path, desired[relative], root)
            if item.get("executable"):
                path.chmod(stat.S_IMODE(path.stat().st_mode) | 0o111)
            if relative in entry_by_path:
                entry_by_path[relative]["new_sha256"] = _sha256(path)
        if plan["baseline_update"]:
            baseline_paths = (".forgeflow/runtime.json", ".forgeflow/run.py", ".forgeflow/spec")
            existed_before = {rel: (root / rel).exists() for rel in baseline_paths}
            for rel in baseline_paths:
                target = root / rel
                if target.is_symlink():
                    journal_entries.append({
                        "path": rel,
                        "operation": "link",
                        "backup": os.readlink(target),
                    })
                elif target.exists():
                    backup = _backup_path(root, operation_id, rel)
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup)
                    journal_entries.append({"path": rel, "operation": "replaced", "backup": _rel(root, backup)})
                else:
                    journal_entries.append({"path": rel, "operation": "created", "backup": None})
            baseline = pin_runtime(root)
            plan["project_runtime"] = {
                "version": baseline.get("version"),
                "identity": baseline.get("identity"),
                "next_identity": baseline.get("identity"),
            }
            entry_by_path = {entry["path"]: entry for entry in journal_entries}
            for rel in baseline_paths:
                target = root / rel
                entry = entry_by_path.get(rel)
                if entry is None:
                    continue
                if target.is_symlink():
                    entry["new_target"] = os.readlink(target)
                elif target.exists():
                    entry["new_sha256"] = _sha256(target)
            for rel in baseline_paths:
                path = root / rel
                if path.is_symlink() or path.exists():
                    if rel in updated_files or rel in created_files:
                        continue
                    if existed_before[rel]:
                        updated_files.append(rel)
                    else:
                        created_files.append(rel)
            runtime_dir = root / ".forgeflow/runtime" / str(baseline.get("identity"))
            if runtime_dir.exists() and _rel(root, runtime_dir) not in created_dirs:
                created_dirs.append(_rel(root, runtime_dir))
        _record_journal(root, operation_id, {
            "id": operation_id,
            "status": "applied",
            "started_at": _now(),
            "finished_at": _now(),
            "entries": journal_entries,
        })
    except Exception as exc:
        restore_errors: List[str] = []
        # Restore only managed mutations from this operation.
        for entry in reversed(journal_entries):
            target = safe_project_path(root, entry["path"])
            try:
                if entry["operation"] == "created":
                    if target.is_symlink() or target.exists():
                        target.unlink()
                elif entry["operation"] == "link":
                    target.unlink(missing_ok=True)
                    target.symlink_to(entry["backup"], target_is_directory=True)
                else:
                    backup = safe_project_path(root, entry["backup"])
                    if backup.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, target)
                if entry["path"] in created_files:
                    created_files.remove(entry["path"])
                if entry["path"] in updated_files:
                    updated_files.remove(entry["path"])
            except Exception as restore_exc:  # pragma: no cover - defensive
                restore_errors.append(f"{entry['path']}: {restore_exc}")
        for directory in reversed(created_dirs):
            try:
                (root / directory).rmdir()
            except OSError:
                pass
        status = "failed-rolled-back" if not restore_errors else "partial"
        try:
            # Keep the failed record, but mark it terminal so a retry can proceed.
            _record_journal(root, operation_id, {
                "id": operation_id,
                "status": status,
                "started_at": _now(),
                "finished_at": _now(),
                "error": str(exc),
                "restore_errors": restore_errors,
                "entries": journal_entries,
            })
        except Exception:
            pass
        plan.update({
            "status": status,
            "complete": False,
            "error": str(exc),
            "restore_errors": restore_errors,
            "backup_dir": backup_dir_rel,
            "migration_record": f"{MIGRATION_DIR}/{operation_id}.json",
            "created_files": created_files,
            "updated_files": updated_files,
            "created_dirs": created_dirs if restore_errors else [],
            "next_actions": [
                "Review the migration journal and restore any reported path manually."
                if restore_errors else "Rerun forgeflow update after resolving the reported error."
            ],
        })
        return plan

    plan.update({
        "status": "applied",
        "complete": True,
        "dry_run": False,
        "created_files": sorted(set(created_files)),
        "updated_files": sorted(set(updated_files)),
        "removed_files": removed_files,
        "created_dirs": sorted(set(created_dirs)),
        "backup_dir": backup_dir_rel,
        "migration_record": f"{MIGRATION_DIR}/{operation_id}.json",
        "next_actions": [],
    })
    return plan


def _recovery_target(root: Path, relative: str) -> Path:
    """Resolve a journal entry without following its final symlink component."""
    _assert_relative_writable(relative)
    parent_relative = Path(relative).parent.as_posix()
    parent = root if parent_relative == "." else safe_project_path(root, parent_relative)
    return parent / Path(relative).name


def _copy_restore(source: Path, target: Path, root: Path) -> None:
    import tempfile
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.recover-", dir=target.parent)
    os.close(fd)
    temporary_path = Path(temporary)
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)


def recover_migration(root: Path, operation_id: str) -> Dict[str, Any]:
    root = Path(root).absolute().resolve(strict=True)
    if re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}", operation_id) is None:
        raise ValueError("Invalid migration id")
    journal_path = safe_project_path(root, f"{MIGRATION_DIR}/{operation_id}.json")
    if not journal_path.exists():
        raise ValueError(f"Migration record not found: {operation_id}")
    payload = json.loads(journal_path.read_text(encoding="utf-8"))
    if payload.get("status") not in {"planned", "applying", "partial"}:
        raise ValueError(
            f"Migration {operation_id} is already terminal ({payload.get('status')}); recovery is not allowed."
        )
    errors: List[str] = []
    conflicts: List[str] = []
    restored: List[str] = []
    for entry in reversed(payload.get("entries", [])):
        relative = str(entry.get("path", ""))
        try:
            target = _recovery_target(root, relative)
            operation = entry.get("operation")
            if operation == "link":
                current_target = os.readlink(target) if target.is_symlink() else None
                if entry.get("new_target") and current_target not in {None, entry.get("new_target")}:
                    conflicts.append(f"{relative}: link target changed after the migration")
                    continue
                target.unlink(missing_ok=True)
                target.symlink_to(entry["backup"], target_is_directory=True)
                restored.append(relative)
                continue
            current = _sha256(target) if target.is_file() else None
            expected_after = entry.get("new_sha256")
            if operation == "created":
                if current is None:
                    restored.append(relative)
                    continue
                if expected_after and current != expected_after:
                    conflicts.append(f"{relative}: content changed after the migration")
                    continue
                target.unlink()
            else:
                if expected_after and current != expected_after:
                    conflicts.append(f"{relative}: content changed after the migration")
                    continue
                backup = safe_project_path(root, entry["backup"])
                if not backup.exists():
                    raise FileNotFoundError(entry["backup"])
                target.parent.mkdir(parents=True, exist_ok=True)
                _copy_restore(backup, target, root)
            restored.append(relative)
        except Exception as exc:
            errors.append(f"{relative or '<unknown>'}: {exc}")
    status = "recovered" if not errors and not conflicts else "partial"
    payload.update({
        "status": status,
        "recovered_at": _now(),
        "restored_paths": restored,
        "restore_errors": errors,
        "recovery_conflicts": conflicts,
    })
    _write_text_atomic(journal_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", root)
    return {"status": "applied" if status == "recovered" else "partial", "migration": operation_id,
            "restored_paths": restored, "restore_errors": errors, "recovery_conflicts": conflicts}


def update_project(root: Path, *, dry_run: bool = False, accept_paths: Iterable[str] = ()) -> Dict[str, Any]:
    plan = build_update_plan(root, accept_paths=accept_paths)
    if plan["status"] != "planned":
        plan["dry_run"] = dry_run
        return _public_result(plan)
    if dry_run:
        plan["status"] = "planned"
        plan["complete"] = False
        plan["created_files"] = sorted(
            item["path"] for item in plan["assets"]
            if item["action"] == ACTION_CREATE and item["path"] in plan.get("desired", {})
        )
        plan["updated_files"] = sorted(
            item["path"] for item in plan["assets"]
            if item["action"] == ACTION_UPDATE and item["path"] in plan.get("desired", {})
        )
        plan["created_dirs"] = sorted(
            item["path"] for item in plan["assets"]
            if item["action"] == ACTION_CREATE and item["path"] not in plan.get("desired", {})
        )
        return _public_result(plan)
    plan = apply_update_plan(plan)
    return _public_result(plan)


def _public_result(plan: Dict[str, Any]) -> Dict[str, Any]:
    result = {key: value for key, value in plan.items() if not key.startswith("_")}
    result.pop("desired", None)
    result["migration_status"] = result.get("status")
    changelog_summary = None
    try:
        changelog_summary = TemplateScaffolder.extract_changelog_range(
            result.get("previous_version", "unknown"),
            __version__,
            changelog_file=TemplateScaffolder.find_changelog_file(Path(result["target_dir"])),
        )
    except Exception:
        pass
    result["changelog_summary"] = changelog_summary
    return result
