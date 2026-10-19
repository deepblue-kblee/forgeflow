"""
Scanner for Git Diff, Source Files, Specs, and Standards (Zero-Dependency)
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Set

from .scanner import HierarchicalRootScanner, ReleaseScanner

IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "build", "dist", ".eggs", ".idea", ".vscode"}
SOURCE_EXTENSIONS = {".py", ".sh", ".js", ".ts", ".json", ".toml", ".yaml", ".yml"}


class ReviewScanner:
    """Scans Git changes, repository files, specs, and coding standards."""

    @classmethod
    def get_diff_files(cls, repo_root: Path, base_ref: Optional[str] = None) -> List[Path]:
        """Extract modified and untracked files via git diff / status."""
        files: Set[Path] = set()

        # 1. Check git diff if base_ref provided or default to HEAD
        try:
            if base_ref:
                cmd = ["git", "diff", f"{base_ref}...HEAD", "--name-only"]
            else:
                cmd = ["git", "diff", "HEAD", "--name-only"]

            res = subprocess.run(
                cmd,
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    p = (repo_root / line.strip()).resolve()
                    if p.exists() and p.is_file() and p.suffix in SOURCE_EXTENSIONS:
                        files.add(p)

            # 2. Check untracked files
            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if untracked.returncode == 0:
                for line in untracked.stdout.splitlines():
                    p = (repo_root / line.strip()).resolve()
                    if p.exists() and p.is_file() and p.suffix in SOURCE_EXTENSIONS:
                        files.add(p)

        except Exception:
            pass

        return sorted(list(files))

    @classmethod
    def get_all_source_files(
        cls, repo_root: Path, extensions: Optional[Set[str]] = None
    ) -> List[Path]:
        """Scan all source files in the repository with directory pruning."""
        import os
        target_exts = extensions or {".py"}
        found: List[Path] = []

        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for f in files:
                p = Path(root) / f
                if p.suffix in target_exts:
                    found.append(p.resolve())

        return sorted(found)

    @classmethod
    def find_spec_source(cls, repo_root: Path, explicit_spec: Optional[str] = None) -> Optional[Path]:
        """Hierarchically resolve the specification source."""
        # 1. Explicit spec
        if explicit_spec:
            spec_path = Path(explicit_spec)
            if not spec_path.is_absolute():
                spec_path = (repo_root / spec_path).resolve()
            if spec_path.exists():
                return spec_path

        # 2. Active release PRD.md / DESIGN.md
        latest_rel = ReleaseScanner.get_latest_release(repo_root)
        if latest_rel:
            prd = latest_rel / "PRD.md"
            if prd.exists():
                return prd
            design = latest_rel / "DESIGN.md"
            if design.exists():
                return design

        # 3. Project root specs
        candidates = ["SPEC.md", "PRD.md", "README.md"]
        for c in candidates:
            cand_p = repo_root / c
            if cand_p.exists():
                return cand_p

        return None

    @classmethod
    def find_standards_sources(cls, repo_root: Path) -> List[Path]:
        """Find coding standards documentation files in repo."""
        standards = []
        candidates = [
            "CODING_STANDARDS.md",
            "GEMINI.md",
            "CONTRIBUTING.md",
            "docs/policy/LOCAL_ACCOUNT_POLICY.md",
            "docs/methodology/HarnessEngineering.md",
        ]
        for c in candidates:
            p = repo_root / c
            if p.exists():
                standards.append(p.resolve())
        return standards
