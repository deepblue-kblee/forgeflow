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

    @classmethod
    def verify_git_ref(cls, repo_root: Path, ref: str) -> str:
        """Verify that ref is a valid git commit object and return its 40-char SHA."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                raise ValueError(f"Invalid or non-existent git baseline reference: '{ref}'")
            return res.stdout.strip()
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to verify git reference '{ref}': {e}") from e

    @classmethod
    def get_candidate_sha(cls, repo_root: Path) -> str:
        """Get the current HEAD commit SHA or fallback identifier."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return "HEAD"

    @classmethod
    def get_file_at_ref(cls, repo_root: Path, ref: str, rel_path: str) -> Optional[str]:
        """Read file contents at a given git revision via git show."""
        try:
            res = subprocess.run(
                ["git", "show", f"{ref}:{rel_path}"],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout
            return None
        except Exception:
            return None

    @classmethod
    def get_modified_lines(cls, repo_root: Path, base_ref: str, rel_path: str) -> Set[int]:
        """Extract modified/added line numbers in candidate file compared to base_ref."""
        import re
        modified_lines: Set[int] = set()
        try:
            res = subprocess.run(
                ["git", "diff", "-U0", base_ref, "--", rel_path],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                return modified_lines

            hunk_pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
            for line in res.stdout.splitlines():
                m = hunk_pattern.match(line)
                if m:
                    start = int(m.group(1))
                    count = int(m.group(2)) if m.group(2) is not None else 1
                    if count > 0:
                        for l_num in range(start, start + count):
                            modified_lines.add(l_num)
        except Exception:
            pass
        return modified_lines

    @classmethod
    def get_function_scopes_and_lines(cls, source_code: str) -> List[tuple[int, int, str]]:
        """Extract (start_line, end_line, scope_name) for functions/methods via AST."""
        import ast
        scopes: List[tuple[int, int, str]] = []
        try:
            tree = ast.parse(source_code)
        except Exception:
            return scopes

        class ScopeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.stack: List[str] = []

            def visit_ClassDef(self, node: ast.ClassDef):
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self.stack.append(node.name)
                scope_name = ".".join(self.stack)
                start = node.lineno
                end = getattr(node, "end_lineno", node.lineno)
                scopes.append((start, end, scope_name))
                self.generic_visit(node)
                self.stack.pop()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self.stack.append(node.name)
                scope_name = ".".join(self.stack)
                start = node.lineno
                end = getattr(node, "end_lineno", node.lineno)
                scopes.append((start, end, scope_name))
                self.generic_visit(node)
                self.stack.pop()

        visitor = ScopeVisitor()
        visitor.visit(tree)
        return scopes

    @classmethod
    def get_modified_scopes(cls, source_code: str, modified_lines: Set[int]) -> Set[str]:
        """Return the set of function/method scope names that overlap with modified lines."""
        if not modified_lines:
            return set()
        scope_ranges = cls.get_function_scopes_and_lines(source_code)
        modified_scopes: Set[str] = set()
        for start, end, scope_name in scope_ranges:
            if any(start <= line <= end for line in modified_lines):
                modified_scopes.add(scope_name)
        return modified_scopes
