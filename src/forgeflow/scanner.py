"""
Hierarchical Project Root and Release Directory Scanner
"""

import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class HierarchicalRootScanner:
    """Discovers target project root using git toplevel and upward marker walk."""

    @staticmethod
    def find_root(start_path: Optional[Path] = None) -> Path:
        current = (start_path or Path.cwd()).resolve()

        # 1. Try git rev-parse --show-toplevel
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(current),
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                git_root = Path(res.stdout.strip()).resolve()
                if git_root.exists():
                    return git_root
        except Exception:
            pass

        # 2. Upward directory walk for markers
        probe = current
        while probe != probe.parent:
            if (probe / ".forgeflow.json").exists():
                return probe
            if (probe / "tasks").exists() and (probe / "tasks").is_dir():
                return probe
            if (probe / "ff-tasks").exists() and (probe / "ff-tasks").is_dir():
                return probe
            if (probe / "docs" / "releases").exists():
                return probe
            if (probe / ".git").exists():
                return probe
            if (probe / "pyproject.toml").exists() or (probe / ".forgeflow.toml").exists():
                return probe
            probe = probe.parent

        # 3. Fallback to current working directory
        return current


class ReleaseScanner:
    """Scans and orders release/task directories under tasks/ or docs/releases/."""

    SUB_CONTAINERS = ("in-progress", "completed", "backlog")

    @staticmethod
    def _read_configured_tasks_dir(repo_root: Path) -> Optional[str]:
        config_path = repo_root / ".forgeflow.json"
        if config_path.exists() and config_path.is_file():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    governance = data.get("governance")
                    if isinstance(governance, dict):
                        tasks_dir = governance.get("tasks_dir")
                        if isinstance(tasks_dir, str) and tasks_dir.strip():
                            return tasks_dir.strip()
            except Exception:
                pass
        return None

    @staticmethod
    def find_releases_dir(repo_root: Path) -> Optional[Path]:
        configured = ReleaseScanner._read_configured_tasks_dir(repo_root)
        if configured:
            cand = repo_root / configured
            if cand.exists() and cand.is_dir():
                return cand

        candidates = [
            repo_root / "tasks",
            repo_root / "ff-tasks",
            repo_root / "docs" / "releases",
            repo_root / "releases",
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                return c
        return None

    @staticmethod
    def find_release_path(repo_root: Path, release_id: str) -> Optional[Path]:
        """Find the exact directory path for a release or task id across all supported layouts."""
        configured = ReleaseScanner._read_configured_tasks_dir(repo_root)
        candidate_roots: List[Path] = []
        if configured:
            candidate_roots.append(repo_root / configured)
        for base in [repo_root / "tasks", repo_root / "ff-tasks", repo_root / "docs" / "releases", repo_root / "releases"]:
            if base not in candidate_roots and base.exists() and base.is_dir():
                candidate_roots.append(base)

        for base_dir in candidate_roots:
            # Check kanban sub-containers first
            for sub in ReleaseScanner.SUB_CONTAINERS:
                cand = base_dir / sub / release_id
                if cand.exists() and cand.is_dir() and any(cand.glob("*.md")):
                    return cand
            # Check flat layout
            cand = base_dir / release_id
            if cand.exists() and cand.is_dir() and any(cand.glob("*.md")):
                return cand

        return None

    @staticmethod
    def _release_sort_key(path: Path) -> Tuple[Tuple[int, int, int], str]:
        m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", path.name)
        if m:
            return (tuple(map(int, m.groups())), path.name)
        return ((0, 0, 0), path.name)

    @staticmethod
    def get_all_releases(repo_root: Path) -> List[Path]:
        configured = ReleaseScanner._read_configured_tasks_dir(repo_root)
        roots_to_check: List[Path] = []
        if configured:
            c_path = repo_root / configured
            if c_path.exists() and c_path.is_dir():
                roots_to_check.append(c_path)

        for default_cand in [repo_root / "tasks", repo_root / "ff-tasks", repo_root / "docs" / "releases", repo_root / "releases"]:
            if default_cand not in roots_to_check and default_cand.exists() and default_cand.is_dir():
                roots_to_check.append(default_cand)

        if not roots_to_check:
            return []

        discovered: dict[str, Path] = {}
        for base_dir in roots_to_check:
            # 1. Kanban sub-containers (in-progress takes precedence over completed)
            for sub in ReleaseScanner.SUB_CONTAINERS:
                sub_dir = base_dir / sub
                if sub_dir.exists() and sub_dir.is_dir():
                    for p in sub_dir.iterdir():
                        if p.is_dir() and not p.name.startswith("."):
                            if any(p.glob("*.md")) and p.name not in discovered:
                                discovered[p.name] = p

            # 2. Flat layout directly under base_dir
            for p in base_dir.iterdir():
                if p.is_dir() and not p.name.startswith(".") and p.name not in ReleaseScanner.SUB_CONTAINERS:
                    if any(p.glob("*.md")) and p.name not in discovered:
                        discovered[p.name] = p

        # Sort natural/version order
        return sorted(discovered.values(), key=ReleaseScanner._release_sort_key)

    @staticmethod
    def get_latest_release(repo_root: Path) -> Optional[Path]:
        all_rels = ReleaseScanner.get_all_releases(repo_root)
        if not all_rels:
            return None
        return all_rels[-1]


find_releases_dir = ReleaseScanner.find_releases_dir
find_release_path = ReleaseScanner.find_release_path
get_all_releases = ReleaseScanner.get_all_releases
get_latest_release = ReleaseScanner.get_latest_release


