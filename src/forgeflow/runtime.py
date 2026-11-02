"""Content-addressed, executable project baselines using only the stdlib.

The installed ``current`` pointer is a distribution choice, never an implicit
instruction to migrate active work. A project snapshot includes code, specs and
templates so a pinned task remains executable after a global installation moves.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ._version import __version__


class RuntimeBaselineError(ValueError):
    """A baseline is unsafe, damaged, or different from the executing package."""


def _package_files(package_dir: Path):
    if package_dir.is_symlink() or not package_dir.is_dir():
        raise RuntimeBaselineError("Runtime package must be a real directory")
    for path in sorted(package_dir.rglob("*")):
        relative = path.relative_to(package_dir)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"} or path.name == ".DS_Store":
            continue
        if path.is_symlink():
            raise RuntimeBaselineError(f"Runtime package contains a symbolic link: {relative}")
        if path.is_file():
            yield path, relative
        elif not path.is_dir():
            raise RuntimeBaselineError(f"Runtime package contains a special file: {relative}")


def package_identity(package_dir: Path | str | None = None) -> str:
    """Hash actual distributable bytes and script permissions, excluding caches."""
    package = Path(package_dir) if package_dir is not None else Path(__file__).parent
    digest = hashlib.sha256()
    for path, relative in _package_files(package):
        name = relative.as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update((path.stat().st_mode & 0o111).to_bytes(2, "big"))
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def safe_project_path(root: Path, relative: str) -> Path:
    """Resolve a project-owned path without traversing symbolic links."""
    if not isinstance(relative, str) or any(ord(char) < 32 for char in relative):
        raise RuntimeBaselineError("Runtime path contains invalid characters")
    candidate = Path(relative)
    if candidate.is_absolute() or not candidate.parts or any(p in {"..", "."} for p in candidate.parts):
        raise RuntimeBaselineError("Runtime path must be relative and contained")
    current = root
    if current.is_symlink() or not current.is_dir():
        raise RuntimeBaselineError("Project root must be a real directory")
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeBaselineError(f"Symbolic link in runtime path: {current}")
        if current.exists() and current != root / candidate and not current.is_dir():
            raise RuntimeBaselineError(f"Runtime parent is not a directory: {current}")
    return root / candidate


def _write_atomic(path: Path, content: str) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".forgeflow-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


_LAUNCHER = '''"""Run this project's checked ForgeFlow snapshot."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

root = Path(__file__).absolute().parent.parent
if root.is_symlink() or not root.is_dir():
    raise SystemExit("ForgeFlow project root must be a real directory")
def checked(relative):
    path = root
    for part in Path(relative).parts:
        if part in ("..", "."):
            raise SystemExit("Unsafe ForgeFlow runtime path")
        path = path / part
        if path.is_symlink():
            raise SystemExit("ForgeFlow runtime path cannot be a symbolic link")
    return path
if len(sys.argv) > 2 and sys.argv[1] == "--runtime-identity":
    identity = sys.argv[2]
    del sys.argv[1:3]
else:
    baseline = json.loads(checked(".forgeflow/runtime.json").read_text(encoding="utf-8"))
    identity = baseline["identity"]
if len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
    raise SystemExit("Invalid ForgeFlow runtime identity")
package = checked(".forgeflow/runtime/" + identity + "/forgeflow")
digest = hashlib.sha256()
for path in sorted(package.rglob("*")):
    relative = path.relative_to(package)
    if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo") or path.name == ".DS_Store":
        continue
    if path.is_symlink():
        raise SystemExit("ForgeFlow snapshot contains a symbolic link")
    if path.is_dir():
        continue
    if not stat.S_ISREG(path.stat().st_mode):
        raise SystemExit("ForgeFlow snapshot contains a special file")
    name = relative.as_posix().encode("utf-8")
    content = path.read_bytes()
    digest.update(len(name).to_bytes(8, "big"))
    digest.update(name)
    digest.update((path.stat().st_mode & 0o111).to_bytes(2, "big"))
    digest.update(len(content).to_bytes(8, "big"))
    digest.update(content)
if digest.hexdigest() != identity:
    raise SystemExit("ForgeFlow runtime snapshot changed; restore the recorded baseline")
# Ignored caches are not trusted executable input. Prevent writes and select a
# fresh nonexistent cache prefix so imports cannot read a stale/unchecked pyc.
sys.dont_write_bytecode = True
sys.pycache_prefix = str(root / ".forgeflow/runtime" / (".unused-pycache-" + os.urandom(16).hex()))
sys.path.insert(0, str(package.parent))
from forgeflow.cli import main
main()
'''


def preflight_baseline(root: Path | str) -> None:
    """Validate baseline targets without writing anything.

    Migration planning uses this so an unsafe launcher or spec link becomes a
    structured blocker before any project file is changed.
    """
    root = Path(root).absolute()
    safe_project_path(root, ".forgeflow")
    launcher = root / ".forgeflow" / "run.py"
    if launcher.exists():
        if launcher.is_symlink() or not launcher.is_file():
            raise RuntimeBaselineError(".forgeflow/run.py must be a real file")
        existing = launcher.read_text(encoding="utf-8")
        if existing != _LAUNCHER and not existing.startswith('"""Run this project\'s checked ForgeFlow snapshot."""'):
            raise RuntimeBaselineError(".forgeflow/run.py is a user file; preserve it before selecting a baseline")
    spec_link = root / ".forgeflow" / "spec"
    package = Path(__file__).parent
    if spec_link.exists() and not spec_link.is_symlink():
        raise RuntimeBaselineError(".forgeflow/spec is a user directory; preserve it and select a separate baseline")
    if spec_link.is_symlink():
        target = Path(os.readlink(spec_link))
        absolute_target = spec_link.parent / target
        known_global = Path.home() / ".local/share/forgeflow/current/lib/forgeflow/spec"
        known_legacy = Path.home() / ".local/forgeflow/current/lib/forgeflow/templates/spec"
        managed_snapshot = (
            not target.is_absolute()
            and len(target.parts) == 4
            and target.parts[0] == "runtime"
            and re.fullmatch(r"[0-9a-f]{64}", target.parts[1]) is not None
            and target.parts[2:] == ("forgeflow", "spec")
        )
        if not managed_snapshot and absolute_target not in {known_global, known_legacy, package / "spec"}:
            raise RuntimeBaselineError(".forgeflow/spec has an unrecognized user symbolic link")


def pin_runtime(root: Path | str) -> dict[str, Any]:
    """Select a snapshot of the executing package after caller migration checks.

    Repeated pinning of the same package is a no-op. This function intentionally
    does not decide whether an active task may adopt another package.
    """
    root = Path(root).absolute()
    package = Path(__file__).parent
    identity = package_identity(package)
    snapshot = safe_project_path(root, f".forgeflow/runtime/{identity}/forgeflow")
    baseline_file = safe_project_path(root, ".forgeflow/runtime.json")
    launcher = safe_project_path(root, ".forgeflow/run.py")
    if launcher.exists():
        existing_launcher = launcher.read_text(encoding="utf-8")
        if existing_launcher != _LAUNCHER and not existing_launcher.startswith('"""Run this project\'s checked ForgeFlow snapshot."""'):
            raise RuntimeBaselineError(".forgeflow/run.py is a user file; preserve it before selecting a baseline")
    spec_link = root / ".forgeflow" / "spec"
    if spec_link.exists() and not spec_link.is_symlink():
        raise RuntimeBaselineError(".forgeflow/spec is a user directory; preserve it and select a separate baseline")
    if spec_link.is_symlink():
        target = Path(os.readlink(spec_link))
        # An existing framework-managed spec link may point at a prior global
        # current installation. Replace the link itself, never its target.
        absolute_target = spec_link.parent / target
        known_global = Path.home() / ".local/share/forgeflow/current/lib/forgeflow/spec"
        known_legacy = Path.home() / ".local/forgeflow/current/lib/forgeflow/templates/spec"
        managed_snapshot = (
            not target.is_absolute()
            and len(target.parts) == 4
            and target.parts[0] == "runtime"
            and re.fullmatch(r"[0-9a-f]{64}", target.parts[1]) is not None
            and target.parts[2:] == ("forgeflow", "spec")
        )
        if not managed_snapshot and absolute_target not in {known_global, known_legacy, package / "spec"}:
            raise RuntimeBaselineError(".forgeflow/spec has an unrecognized user symbolic link")
    if snapshot.exists():
        if package_identity(snapshot) != identity:
            raise RuntimeBaselineError("Recorded ForgeFlow runtime snapshot is damaged")
    else:
        runtime_dir = safe_project_path(root, ".forgeflow/runtime")
        runtime_dir.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".snapshot-", dir=runtime_dir))
        try:
            staged = temporary / "forgeflow"
            staged.mkdir()
            for source, relative in _package_files(package):
                destination = staged / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            if package_identity(staged) != identity:
                raise RuntimeBaselineError("Runtime changed while snapshotting; retry after edits finish")
            os.replace(temporary, snapshot.parent)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    baseline = {
        "identity": identity,
        "version": __version__,
        "path": str(snapshot),
        "command": f"python3 {shlex.quote(str(launcher))} --runtime-identity {identity}",
    }
    payload = json.dumps(baseline, indent=2) + "\n"
    if not baseline_file.exists() or baseline_file.read_text(encoding="utf-8") != payload:
        _write_atomic(baseline_file, payload)
    if not launcher.exists() or launcher.read_text(encoding="utf-8") != _LAUNCHER:
        _write_atomic(launcher, _LAUNCHER)
    expected_link = Path("runtime") / identity / "forgeflow" / "spec"
    if not spec_link.is_symlink() or Path(os.readlink(spec_link)) != expected_link:
        if spec_link.is_symlink():
            spec_link.unlink()
        spec_link.symlink_to(expected_link, target_is_directory=True)
    return baseline


def assert_runtime(root: Path | str, baseline: dict[str, Any]) -> None:
    """Reject damaged snapshots and silent changes to an active task baseline."""
    root = Path(root).absolute()
    identity = baseline.get("identity", "")
    if not isinstance(identity, str) or re.fullmatch(r"[0-9a-f]{64}", identity) is None:
        raise RuntimeBaselineError("Invalid recorded runtime identity")
    snapshot = safe_project_path(root, f".forgeflow/runtime/{identity}/forgeflow")
    if package_identity(snapshot) != identity:
        raise RuntimeBaselineError("Recorded ForgeFlow runtime snapshot is damaged")
    if package_identity() != identity:
        command = f"python3 {shlex.quote(str(root / '.forgeflow' / 'run.py'))} --runtime-identity {identity}"
        raise RuntimeBaselineError(
            f"Executing runtime differs from this task's rules; use {command} or explicitly adopt reviewed rules"
        )
