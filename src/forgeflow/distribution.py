"""Installation target resolution and post-install verification."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

KNOWN_REQUIRED_SKILLS = ("setup-forgeflow", "update-forgeflow", "forgeflow", "forgeflow-graphify")


def _real(path: Path) -> Path:
    try:
        return path.resolve(strict=True)
    except OSError:
        return path.absolute()


def resolve_installation_target() -> Dict[str, Any]:
    """Resolve the same default/custom target the installer will use.

    Explicit environment variables win. When invoked through an installed
    launcher, the prefix is derived from that real entrypoint so an upgrade
    never verifies a different default installation.
    """
    env = os.environ
    prefix = env.get("FORGEFLOW_INSTALL_DIR")
    bin_dir = env.get("FORGEFLOW_BIN_DIR")
    skills_dir = env.get("FORGEFLOW_SKILLS_DIR")

    # Executing from an installed package gives the authoritative prefix:
    # <prefix>/packages/<key>/lib/forgeflow/distribution.py
    if not prefix:
        package_path = Path(__file__).resolve()
        parents = package_path.parents
        for index, parent in enumerate(parents):
            if parent.name == "packages" and index + 1 < len(parents):
                candidate = parents[index + 1]
                if (candidate / "current").exists() or (candidate / "packages").exists():
                    prefix = str(candidate)
                    break
    if not prefix and sys.argv and sys.argv[0]:
        entry = Path(sys.argv[0])
        if entry.exists():
            resolved = _real(entry)
            if resolved.name == "forgeflow" and resolved.parent.name == "bin":
                candidate = resolved.parent.parent
                if (candidate / "packages").exists():
                    prefix = str(candidate)
    prefix = prefix or str(Path.home() / ".local" / "share" / "forgeflow")
    metadata = read_package_metadata(prefix)
    bin_dir = bin_dir or metadata.get("bin_dir")
    skills_dir = skills_dir or metadata.get("skills_dir")
    bin_dir = bin_dir or str(Path.home() / ".local" / "bin")
    skills_dir = skills_dir or str(Path.home() / ".agents" / "skills")
    return {
        "prefix": str(Path(prefix).expanduser().absolute()),
        "bin_dir": str(Path(bin_dir).expanduser().absolute()),
        "skills_dir": str(Path(skills_dir).expanduser().absolute()),
    }


def read_package_metadata(prefix: str | Path) -> Dict[str, Any]:
    metadata = Path(prefix) / "current" / "package.json"
    if not metadata.is_file() or metadata.is_symlink():
        return {}
    try:
        payload = json.loads(metadata.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def derive_clone_url(repo_url: str) -> Optional[str]:
    """Derive the Git repository for a raw GitHub source URL."""
    match = re.fullmatch(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/(?:.+)", repo_url.rstrip("/"))
    if match:
        return f"https://github.com/{match.group(1)}/{match.group(2)}"
    configured = os.environ.get("FORGEFLOW_REPO", "").strip()
    if configured and not configured.startswith("-") and "\n" not in configured and "\r" not in configured:
        return configured
    return None


def resolve_revision(clone_url: Optional[str], ref: str) -> str:
    """Resolve a mutable ref to an immutable commit when Git can do so."""
    if not clone_url or not ref:
        return ref
    for candidate in (ref, f"refs/heads/{ref}", f"refs/tags/{ref}"):
        try:
            result = subprocess.run(
                ["git", "ls-remote", clone_url, candidate],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except Exception:
            continue
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.splitlines()[0].split()
            if line and re.fullmatch(r"[0-9a-f]{40}", line[0]):
                return line[0]
    return ref


def _run_entrypoint(executable: Path, args: list[str], timeout: int = 20) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            [str(executable), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def verify_installed_distribution(
    target: Dict[str, Any],
    *,
    expected_version: str,
    expected_source_identity: str,
    expected_revision: str,
) -> Dict[str, Any]:
    """Observe the actually installed package, entrypoint, spec, and skills."""
    prefix = Path(target["prefix"])
    bin_dir = Path(target["bin_dir"])
    skills_dir = Path(target["skills_dir"])
    errors: list[str] = []
    observed: Dict[str, Any] = {}

    metadata = read_package_metadata(prefix)
    observed["package_metadata"] = metadata
    if not metadata:
        errors.append(f"Missing or unreadable package metadata: {prefix / 'current' / 'package.json'}")
    else:
        if metadata.get("version") != expected_version:
            errors.append(
                f"Installed package version {metadata.get('version')!r} does not match expected {expected_version!r}."
            )
        if not metadata.get("content_identity"):
            errors.append("Installed package metadata has no content_identity.")
        recorded_source = metadata.get("source_identity")
        observed["source_identity"] = recorded_source
        if recorded_source != expected_source_identity:
            errors.append(
                "Installed package source_identity does not match the fetched distribution "
                f"({recorded_source!r} != {expected_source_identity!r})."
            )
        if metadata.get("source_revision") not in {None, "", expected_revision}:
            errors.append(
                f"Installed source_revision {metadata.get('source_revision')!r} does not match {expected_revision!r}."
            )

    current = prefix / "current"
    if not current.is_symlink() and not current.exists():
        errors.append(f"Active installation pointer is missing: {current}")
    else:
        resolved_current = _real(current)
        if not (resolved_current / "lib" / "forgeflow" / "_version.py").is_file():
            errors.append(f"Active package has no forgeflow runtime: {resolved_current}")
        if not (resolved_current / "lib" / "forgeflow" / "spec" / "README.md").is_file():
            errors.append(f"Active package has no spec entrypoint: {resolved_current}")

    executable = bin_dir / "forgeflow"
    observed["entrypoint"] = str(executable)
    if not executable.is_file():
        errors.append(f"Installed entrypoint is missing: {executable}")
    else:
        try:
            executable.resolve(strict=True).relative_to(prefix.resolve(strict=True))
        except Exception:
            errors.append(
                f"Entrypoint {executable} does not resolve inside the selected prefix {prefix}; "
                "refusing to verify a different installation."
            )
        version_probe = _run_entrypoint(executable, ["version"])
        observed["version_probe"] = version_probe
        if not version_probe.get("ok"):
            errors.append(f"Installed entrypoint version probe failed: {version_probe}")
        else:
            match = re.search(r"ForgeFlow v([0-9]+(?:\.[0-9]+)+(?:-[0-9A-Za-z.]+)?)", version_probe.get("stdout", ""))
            if not match or match.group(1) != expected_version:
                errors.append(
                    f"Installed entrypoint reports {match.group(1) if match else 'unknown'!r}, "
                    f"expected {expected_version!r}."
                )
            else:
                observed["installed_version"] = match.group(1)
        workflow_probe = _run_entrypoint(executable, ["workflow", "--help"])
        observed["workflow_probe"] = workflow_probe
        if not workflow_probe.get("ok"):
            errors.append(f"Installed workflow entrypoint probe failed: {workflow_probe}")

    missing_skills = [
        name for name in KNOWN_REQUIRED_SKILLS
        if not (skills_dir / name / "SKILL.md").is_file()
    ]
    observed["skills_dir"] = str(skills_dir)
    if missing_skills:
        errors.append(f"Installed skills are incomplete: {', '.join(missing_skills)}")

    return {
        "ok": not errors,
        "errors": errors,
        "observed": observed,
        "target": target,
    }
