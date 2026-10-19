"""Fail-closed local governance bundle update service."""

import json
from pathlib import Path
from typing import Any, Dict

from ._version import __version__
from .bundle_catalog import bundle_for, current_bundle
from .scaffold import TemplateScaffolder


UPDATE_PATHS = {".forgeflow.json", str(TemplateScaffolder.GOVERNANCE_PATH), *(str(path) for path in TemplateScaffolder.BUNDLE_FILES)}
UNVERSIONED_LEGACY_VERSIONS = ("0.4.4", "0.4.5")


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _validate_update_journal(root: Path) -> None:
    """Refuse a generic scaffold journal that could mutate root guides."""
    journal = root / TemplateScaffolder.JOURNAL_PATH
    try:
        data = json.loads(journal.read_text(encoding="utf-8"), object_pairs_hook=_strict_pairs)
        entries = data["entries"]
        if not isinstance(entries, list) or any(entry.get("target") not in UPDATE_PATHS for entry in entries):
            raise ValueError("invalid update transaction journal")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid update transaction journal") from exc


def _legacy_version(root: Path) -> str | None:
    """Identify only an exact pre-marker bundle; never infer target content."""
    for version in UNVERSIONED_LEGACY_VERSIONS:
        expected = bundle_for(version)
        if all(
            (path := root / relative).is_file()
            and not path.is_symlink()
            and path.read_text(encoding="utf-8") == content
            for relative, content in expected.items()
        ):
            return version
    return None


def _is_upgradeable(version: str) -> bool:
    try:
        parts = [int(p) for p in version.split(".")]
        return len(parts) == 3 and tuple(parts) >= (0, 4, 4)
    except (ValueError, TypeError, AttributeError):
        return False


def inspect(root: Path) -> Dict[str, Any]:
    """Return a read-only update report; no unknown or edited file is writable."""
    supplied_root = root
    if supplied_root.is_symlink():
        return {"current_version": __version__, "paths": [], "blockers": ["symlink target root"], "status": "unsupported"}
    root = root.resolve()
    config = root / ".forgeflow.json"
    journal = root / TemplateScaffolder.JOURNAL_PATH
    result = {"current_version": __version__, "paths": [], "blockers": []}
    if not root.is_dir() or root.is_symlink() or not config.is_file() or config.is_symlink():
        result.update(status="unsupported", blockers=["unsafe or missing project configuration"])
        return result
    if journal.exists() or journal.is_symlink():
        result.update(status="recovery_required", blockers=["interrupted governance transaction"])
        return result
    try:
        data = json.loads(config.read_text(encoding="utf-8"), object_pairs_hook=_strict_pairs)
        if not isinstance(data, dict):
            raise ValueError("invalid forgeflow_version")
        if "forgeflow_version" in data:
            installed = data["forgeflow_version"]
            if not isinstance(installed, str):
                raise ValueError("invalid forgeflow_version")
        else:
            installed = _legacy_version(root)
            if installed is None:
                raise ValueError("unrecognized unversioned governance bundle")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result.update(status="unsupported", blockers=[str(exc)])
        return result
    result["installed_version"] = installed

    for relative in current_bundle():
        path = root / relative
        if path.is_symlink():
            result["blockers"].append(str(relative))
        result["paths"].append(str(relative))

    if result["blockers"]:
        result["status"] = "unsupported"
    elif installed == __version__:
        result["status"] = "up_to_date"
    elif _is_upgradeable(installed):
        result["status"] = "upgrade_available"
        result["paths"].append(".forgeflow.json")
    else:
        result["status"] = "unsupported"
    return result


def apply(root: Path) -> Dict[str, Any]:
    """Apply only a clean, catalog-recognized update through the journal helper."""
    report = inspect(root)
    if report["status"] == "recovery_required":
        # Recovery is deliberately a separate invocation from upgrade.
        try:
            _validate_update_journal(root.resolve())
            TemplateScaffolder._recover_governance_transaction(root.resolve())
        except Exception as exc:
            return {"status": "recovery_required", "paths": [], "blockers": [str(exc)]}
        return {"status": "recovery_required", "paths": [], "blockers": ["recovery completed; run update again"]}
    if report["status"] != "upgrade_available":
        return report
    root = root.resolve()
    config_path = root / ".forgeflow.json"
    data = json.loads(config_path.read_text(encoding="utf-8"), object_pairs_hook=_strict_pairs)
    data["forgeflow_version"] = __version__
    desired = {root / path: content for path, content in current_bundle().items()}
    desired[config_path] = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    try:
        TemplateScaffolder._apply_governance_transaction(root, desired)
    except Exception as exc:
        return {"status": "recovery_required", "paths": [], "blockers": [str(exc)]}
    verified = inspect(root)
    if verified["status"] != "up_to_date":
        return {"status": "recovery_required", "paths": verified["paths"], "blockers": verified["blockers"] + ["post-apply verification failed"]}
    return {"status": "up_to_date", "installed_version": __version__, "current_version": __version__, "paths": [str(path.relative_to(root)) for path in desired], "blockers": []}
