"""
Scaffolding Engine for Initializing Projects and Creating Release Boilerplates
"""

import copy
import datetime
import json
import os
import re
import stat
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import importlib.resources as pkg_resources

from ._version import __version__


class TemplateScaffolder:
    """Loads templates from package resources and scaffolds release documents."""

    BOOT_ANCHOR_START = "<!-- forgeflow:boot-anchor:start -->"
    BOOT_ANCHOR_END = "<!-- forgeflow:boot-anchor:end -->"
    BOOT_ANCHOR_TEMPLATE = (
        "<!-- forgeflow:boot-anchor:start -->\n"
        "## ForgeFlow Session Boot Sequence\n\n"
        "작업 상태와 `docs/session-state/next-actions.md`가 있으면 먼저 확인.\n"
        "프로젝트 설정: `.forgeflow/config.json`; 새 작업의 기본 사양서 색인: `.forgeflow/spec/README.md`와 `.forgeflow/spec/VERSION`.\n"
        "Active task 재개는 state의 `baseline.command`로 실행하고 `doc show` 또는 `baseline.path/spec`로 해당 기준 확인.\n"
        "여러 task의 runtime identity가 다르면 project 기본 spec 링크나 identity 없는 launcher로 대체하지 않음.\n"
        "범위·완료 조건·필수 검증을 정한 뒤 구현. 통합·정리는 기록된 권한과 Git/host 소유 도구로 수행.\n"
        "설계 검토가 필요하면 `workflow start --hitl design`으로 design checkpoint를 사용.\n"
        "workflow는 사용자가 ForgeFlow를 명시 요청했거나 이 skill을 실제 사용한 경우에만 시작; 설정 존재만으로 시작하지 않음.\n"
        "<!-- forgeflow:boot-anchor:end -->"
    )

    CONFIG_REL_PATH = Path(".forgeflow") / "config.json"
    LEGACY_CONFIG_REL_PATH = Path(".forgeflow.json")
    ROOT_GUIDES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")

    @staticmethod
    def _assert_safe_directory(path: Path, root: Path) -> None:
        """Require a real directory contained by the real project root."""
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError as exc:
            raise ValueError(f"Missing required directory: {path}") from exc
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ValueError(f"Unsafe directory: {path}")
        try:
            path.resolve(strict=True).relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Directory outside project root: {path}") from exc

    @staticmethod
    def _assert_no_symlink_creation_parent(path: Path) -> None:
        """Reject creation below a symbolic-link parent before ``mkdir``.

        Only the nearest extant path component matters for a path that does
        not yet exist.  Checking every filesystem ancestor would reject
        platform-provided aliases such as macOS ``/var -> /private/var``.
        """
        candidate = path
        while True:
            try:
                mode = candidate.lstat().st_mode
            except FileNotFoundError:
                if candidate == candidate.parent:
                    return
                candidate = candidate.parent
                continue
            if stat.S_ISLNK(mode):
                raise ValueError(f"Unsafe project path contains symlink: {candidate}")
            return

    @classmethod
    def _assert_safe_file(cls, path: Path, root: Path, allow_missing: bool = False) -> None:
        cls._assert_safe_directory(path.parent, root)
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            if allow_missing:
                return
            raise
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise ValueError(f"Unsafe file: {path}")
        try:
            path.resolve(strict=True).relative_to(root)
        except ValueError as exc:
            raise ValueError(f"File outside project root: {path}") from exc

    @staticmethod
    def get_template_content(template_name: str, custom_template_dir: Optional[Path] = None) -> str:
        """Load template string from custom directory, package resources, or fallback."""
        if custom_template_dir:
            custom_path = Path(custom_template_dir) / template_name
            if custom_path.exists():
                return custom_path.read_text(encoding="utf-8")

        if template_name.startswith("spec/"):
            sub_spec = template_name[5:]
            try:
                files_ref = pkg_resources.files("forgeflow.spec")
                spec_file = files_ref.joinpath(sub_spec)
                if spec_file.is_file():
                    return spec_file.read_text(encoding="utf-8")
            except Exception:
                pass
            local_spec_fallback = Path(__file__).resolve().parent / "spec" / sub_spec
            if local_spec_fallback.is_file():
                return local_spec_fallback.read_text(encoding="utf-8")

        if template_name in ("CHANGELOG.md", "spec/CHANGELOG.md"):
            for cand in [
                Path(__file__).resolve().parent / "CHANGELOG.md",
                Path(__file__).resolve().parent.parent.parent / "docs" / "CHANGELOG.md",
            ]:
                if cand.is_file():
                    return cand.read_text(encoding="utf-8")

        try:
            # Modern Python 3.9+ files() API
            files_ref = pkg_resources.files("forgeflow.templates")
            template_file = files_ref.joinpath(template_name)
            if template_file.is_file():
                return template_file.read_text(encoding="utf-8")
        except Exception:
            pass

        # Fallback to local path if running uninstalled from source tree
        local_fallback = Path(__file__).resolve().parent / "templates" / template_name
        if local_fallback.is_file():
            return local_fallback.read_text(encoding="utf-8")

        raise FileNotFoundError(f"Template '{template_name}' not found in package resources.")

    @staticmethod
    def render_template(content: str, variables: Dict[str, str]) -> str:
        for k, v in variables.items():
            content = content.replace(f"{{{{{k}}}}}", str(v))
        return content

    @classmethod
    def deep_merge_config(cls, existing: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Deeply merge default configuration into existing user configuration.

        Preserves all existing user-defined keys and values with highest precedence,
        while populating any missing keys from defaults.
        """
        merged = copy.deepcopy(existing)
        for key, val in defaults.items():
            if key not in merged:
                merged[key] = copy.deepcopy(val)
            elif isinstance(merged[key], dict) and isinstance(val, dict):
                merged[key] = cls.deep_merge_config(merged[key], val)
        return merged

    @classmethod
    def scaffold_speckit_hybrid(cls, root: Path, force: bool = False, skip_config: bool = False) -> Dict[str, Any]:
        """Add optional Spec Kit assets while preserving all existing user files."""
        return cls._scaffold_lean(root, speckit=True, skip_config=skip_config)

    @classmethod
    def scaffold_lean_project(cls, root: Path, force: bool = False) -> Dict[str, Any]:
        """Create the lean project entrypoint without Spec Kit support."""
        return cls._scaffold_lean(root, speckit=False)

    @classmethod
    def _active_work(cls, root: Path, config: Dict[str, Any]) -> List[str]:
        """Find unfinished task state before changing any project baseline."""
        from .runtime import safe_project_path
        active: List[str] = []
        state_dir = safe_project_path(root, ".forgeflow/workflows")
        if state_dir.exists():
            for state_file in sorted(state_dir.glob("*.json")):
                cls._assert_safe_file(state_file, root)
                state = json.loads(state_file.read_text(encoding="utf-8"))
                if not isinstance(state, dict):
                    raise ValueError(f"Invalid workflow state: {state_file.name}")
                if state.get("finalization_complete") is not True and state.get("status") not in {"cleaned", "completed", "cancelled"}:
                    active.append(state_file.stem)
        legacy_state_dir = safe_project_path(root, ".forgeflow/lifecycle")
        if legacy_state_dir.exists():
            for state_file in sorted(legacy_state_dir.glob("*.json")):
                cls._assert_safe_file(state_file, root)
                state = json.loads(state_file.read_text(encoding="utf-8"))
                if not isinstance(state, dict):
                    raise ValueError(f"Invalid lifecycle state: {state_file.name}")
                status = state.get("status", state.get("progress", {}).get("status"))
                if status != "COMPLETE":
                    active.append(state_file.stem)
        governance = config.get("governance", {})
        if not isinstance(governance, dict):
            raise ValueError("governance configuration must be an object")
        tasks_name = governance.get("tasks_dir", "tasks")
        if not isinstance(tasks_name, str):
            raise ValueError("governance.tasks_dir must be a relative directory")
        if "tasks_dir" not in governance and (root / "tasks").exists() and not (root / "tasks").is_dir():
            tasks_name = "ff-tasks"
        in_progress = safe_project_path(root, str(Path(tasks_name) / "in-progress"))
        if in_progress.exists():
            for package in in_progress.iterdir():
                if package.is_symlink():
                    raise ValueError(f"Unsafe in-progress task path: {package.name}")
                if package.is_dir() and not package.name.startswith("."):
                    active.append(package.name)
        return sorted(set(active))

    @classmethod
    def lean_asset_specs(
        cls,
        root: Path,
        config: Dict[str, Any],
        *,
        speckit: bool,
        skip_config: bool = False,
        continuation_policy: str = "interactive",
    ) -> Dict[str, Any]:
        """Build desired lean assets without writing anything.

        This is the single desired-state builder shared by ``init`` and
        ``update``. Callers own active-work checks, baseline pinning, and
        filesystem transactions.
        """
        from .runtime import safe_project_path

        governance = config.get("governance", {})
        if not isinstance(governance, dict):
            raise ValueError("governance configuration must be an object")
        tasks_name = governance.get("tasks_dir", "tasks")
        if not isinstance(tasks_name, str):
            raise ValueError("governance.tasks_dir must be a relative directory")
        if "tasks_dir" not in governance and (root / "tasks").exists() and not (root / "tasks").is_dir():
            tasks_name = "ff-tasks"
        defaults = {
            "forgeflow_version": __version__,
            "workflow": {"mode": "lean", "checks": [], "owner": "standalone"},
            "governance": {"tasks_dir": tasks_name, "max_loop_budget": 5,
                           "auto_create_branch": False, "continuation_policy": continuation_policy},
        }
        desired_config = cls.deep_merge_config(config, defaults)
        config_file = safe_project_path(root, ".forgeflow/config.json")
        desired: Dict[Path, tuple[str, bool]] = {}
        if not skip_config:
            desired[config_file] = (
                json.dumps(desired_config, indent=2, ensure_ascii=False) + "\n",
                False,
            )
        if speckit:
            for name in ("check-prerequisites.sh", "common.sh", "create-new-feature.sh", "resolve-template.sh", "setup-plan.sh", "setup-tasks.sh"):
                path = safe_project_path(root, f".specify/scripts/bash/{name}")
                desired[path] = (cls.get_template_content(f"speckit/scripts/bash/{name}"), True)
            for name in ("spec-template.md", "plan-template.md", "tasks-template.md", "checklist-template.md"):
                path = safe_project_path(root, f".specify/templates/{name}")
                desired[path] = (cls.get_template_content(f"speckit/templates/{name}"), False)
        return {
            "desired": desired,
            "desired_config": desired_config,
            "tasks_name": tasks_name,
        }

    @classmethod
    def _scaffold_lean(cls, root: Path, *, speckit: bool, skip_config: bool = False,
                       continuation_policy: str = "interactive") -> Dict[str, Any]:
        from .runtime import assert_runtime, package_identity, pin_runtime, safe_project_path
        root = Path(root).absolute()
        cls._assert_no_symlink_creation_parent(root)
        if root.exists() and (root.is_symlink() or not root.is_dir()):
            raise ValueError(f"Unsafe project root: {root}")
        root.mkdir(parents=True, exist_ok=True)
        root = root.resolve(strict=True)
        config_file = safe_project_path(root, ".forgeflow/config.json")
        legacy_file = safe_project_path(root, ".forgeflow.json")
        source_file = config_file if config_file.exists() else legacy_file
        config: Dict[str, Any] = {}
        if source_file.exists():
            cls._assert_safe_file(source_file, root)
            config = json.loads(source_file.read_text(encoding="utf-8"))
            if not isinstance(config, dict):
                raise ValueError("ForgeFlow configuration must be an object")
        active = cls._active_work(root, config)
        baseline_file = safe_project_path(root, ".forgeflow/runtime.json")
        baseline = None
        if baseline_file.exists():
            baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
            if not isinstance(baseline, dict):
                raise ValueError("Invalid project runtime baseline")
        if active:
            if baseline is None:
                raise ValueError("Active work has no pinned baseline; preserve its installed runtime and explicitly migrate after reviewing impact: " + ", ".join(active))
            if baseline.get("identity") != package_identity():
                raise ValueError("Active work keeps its recorded rules; use the pinned command or workflow adopt with an impact reason: " + ", ".join(active))
            assert_runtime(root, baseline)
        spec = cls.lean_asset_specs(
            root,
            config,
            speckit=speckit,
            skip_config=skip_config,
            continuation_policy=continuation_policy,
        )
        tasks_name = spec["tasks_name"]
        created_dirs: List[str] = []
        created_files: List[str] = []
        updated_files: List[str] = []
        skipped_files: List[str] = []
        desired: Dict[Path, tuple[str, bool]] = spec["desired"]
        for path in desired:
            safe_project_path(root, path.relative_to(root).as_posix())
            if path.exists():
                cls._assert_safe_file(path, root)
        gitignore = safe_project_path(root, ".gitignore")
        if gitignore.exists():
            cls._assert_safe_file(gitignore, root)
        # Validate the snapshot before writing user-visible setup files.
        selected = pin_runtime(root) if baseline is None or not active else baseline
        for path, (content, executable) in desired.items():
            relative = path.relative_to(root).as_posix()
            if path.exists():
                skipped_files.append(relative)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            if executable:
                path.chmod(0o755)
            created_files.append(relative)
        required_entries = [".forgeflow/runtime/", ".forgeflow/runtime.json", ".forgeflow/run.py", ".forgeflow/spec", ".forgeflow/workflows/.*.lock"]
        existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        missing = [entry for entry in required_entries if entry not in existing.splitlines()]
        if missing:
            existed = gitignore.exists()
            gitignore.write_text(existing.rstrip() + "\n" + "\n".join(missing) + "\n", encoding="utf-8")
            (updated_files if existed else created_files).append(".gitignore")
        anchor_result = cls.bind_boot_anchor(root)
        for name, action in anchor_result.items():
            if action == "created":
                created_files.append(name)
            elif action == "updated":
                updated_files.append(name)
        return {"status": "success", "target_dir": str(root), "created_dirs": created_dirs,
                "created_files": created_files, "updated_files": updated_files,
                "skipped_files": skipped_files, "baseline": selected}

    @classmethod
    def bind_boot_anchor(
        cls, root: Path, target_names: Optional[Sequence[str]] = None
    ) -> Dict[str, str]:
        """In-place, non-destructive, idempotent boot anchor injector for root guides (AGENTS.md / CLAUDE.md).

        Deletes any pre-existing boot anchor comments anywhere in the file,
        preserves 100% of existing user-defined content, and appends the latest boot anchor
        block at the very end of the file.
        Returns a dict mapping relative filename to operation ('created', 'updated', 'unchanged', 'skipped').
        """
        root = root.resolve()
        candidates = list(target_names) if target_names else ["AGENTS.md", "CLAUDE.md"]
        # Find which target files exist
        extant_targets = [name for name in candidates if (root / name).is_file()]
        # If none exist, default to creating AGENTS.md
        targets_to_process = extant_targets if extant_targets else ["AGENTS.md"]

        results: Dict[str, str] = {}
        anchor_block = cls.BOOT_ANCHOR_TEMPLATE.strip()
        anchor_pattern = re.compile(
            rf"\n*{re.escape(cls.BOOT_ANCHOR_START)}.*?{re.escape(cls.BOOT_ANCHOR_END)}\n*",
            re.DOTALL,
        )

        for filename in targets_to_process:
            target_file = root / filename
            if target_file.is_symlink():
                results[filename] = "skipped (symbolic link; not modified)"
                continue
            if not target_file.exists():
                target_file.write_text(anchor_block + "\n", encoding="utf-8")
                results[filename] = "created"
                continue

            content = target_file.read_text(encoding="utf-8")
            start_count = content.count(cls.BOOT_ANCHOR_START)
            end_count = content.count(cls.BOOT_ANCHOR_END)

            if start_count != end_count:
                results[filename] = "skipped (duplicate or mismatched markers)"
                continue

            # Strip any pre-existing anchor blocks cleanly
            clean_content = anchor_pattern.sub("\n\n", content).strip()

            if clean_content:
                desired_content = clean_content + "\n\n" + anchor_block + "\n"
            else:
                desired_content = anchor_block + "\n"

            if content == desired_content:
                results[filename] = "unchanged"
            else:
                target_file.write_text(desired_content, encoding="utf-8")
                results[filename] = "updated"

        return results

    @classmethod
    def unbind_boot_anchor(
        cls, root: Path, target_names: Optional[Sequence[str]] = None
    ) -> Dict[str, str]:
        """Clean removal of the boot anchor block, restoring original content."""
        root = root.resolve()
        candidates = list(target_names) if target_names else ["AGENTS.md", "CLAUDE.md"]
        results: Dict[str, str] = {}
        anchor_pattern = re.compile(
            rf"\n*{re.escape(cls.BOOT_ANCHOR_START)}.*?{re.escape(cls.BOOT_ANCHOR_END)}\n*",
            re.DOTALL,
        )

        for filename in candidates:
            target_file = root / filename
            if target_file.is_symlink() or not target_file.is_file():
                continue

            content = target_file.read_text(encoding="utf-8")
            start_count = content.count(cls.BOOT_ANCHOR_START)
            end_count = content.count(cls.BOOT_ANCHOR_END)

            if start_count == 0 and end_count == 0:
                results[filename] = "skipped"
                continue

            if start_count != end_count:
                results[filename] = "skipped"
                continue

            clean_content = anchor_pattern.sub("\n\n", content).strip()
            restored = (clean_content + "\n") if clean_content else ""
            target_file.write_text(restored, encoding="utf-8")
            results[filename] = "unbound"

        return results

    @classmethod
    def update_repo_governance(
        cls,
        root: Path,
        *,
        dry_run: bool = False,
        accept_paths: Sequence[str] = (),
    ) -> Dict[str, Any]:
        """Refresh a current 0.2.x project without migrating 0.1.x layouts."""
        from .runtime import safe_project_path

        root = Path(root).absolute()
        if root.is_symlink() or not root.is_dir():
            raise ValueError("Project root must be a real directory")
        root = root.resolve(strict=True)
        modern = safe_project_path(root, ".forgeflow/config.json")
        legacy = safe_project_path(root, ".forgeflow.json")
        if not modern.exists():
            if legacy.exists():
                return {
                    "status": "needs-action",
                    "target_dir": str(root),
                    "complete": False,
                    "blockers": [{
                        "kind": "legacy-project",
                        "reason": "Legacy .forgeflow.json layout is not supported by forgeflow 0.2.0 update.",
                        "next_action": "Run the separate forgeflow-migrate tool from archive/forgeflow-migrate, then rerun update.",
                    }],
                    "next_actions": ["Run forgeflow-migrate before updating this project."],
                }
            raise ValueError(f"Target directory '{root}' is not a ForgeFlow project (.forgeflow/config.json missing).")
        legacy_markers = [root / "tasks", root / ".forgeflow/lifecycle"]
        if any(marker.exists() for marker in legacy_markers):
            return {
                "status": "needs-action",
                "target_dir": str(root),
                "complete": False,
                "blockers": [{
                    "kind": "legacy-project",
                    "reason": "Legacy tasks/lifecycle artifacts require the separate migration tool.",
                    "next_action": "Run forgeflow-migrate from archive/forgeflow-migrate, then rerun update.",
                }],
                "next_actions": ["Run forgeflow-migrate before updating this project."],
            }
        try:
            config = json.loads(modern.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"Failed to parse .forgeflow/config.json: {exc}") from exc
        if not isinstance(config, dict):
            raise ValueError("ForgeFlow configuration must be an object")
        active = cls._active_work(root, config)
        if active:
            return {
                "status": "needs-action",
                "target_dir": str(root),
                "complete": False,
                "blockers": [{
                    "kind": "active-work",
                    "task": task,
                    "reason": "Active work keeps its recorded runtime and rules.",
                    "next_action": "Finish the workflow or resume it with its pinned command before updating.",
                } for task in active],
                "next_actions": ["Finish or resume active workflows before updating."],
            }
        previous_version = config.get("forgeflow_version", "unknown")
        defaults = {
            "forgeflow_version": __version__,
            "workflow": {"mode": "lean", "owner": "standalone", "checks": []},
            "governance": {"max_loop_budget": 5},
        }
        desired = cls.deep_merge_config(config, defaults)
        desired["forgeflow_version"] = __version__
        desired.get("workflow", {}).pop("continuation", None)
        desired_text = json.dumps(desired, indent=2, ensure_ascii=False) + "\n"
        config_changed = desired_text != modern.read_text(encoding="utf-8")
        if dry_run:
            return {
                "status": "planned",
                "target_dir": str(root),
                "dry_run": True,
                "complete": False,
                "previous_version": previous_version,
                "current_version": __version__,
                "updated_files": [".forgeflow/config.json"] if config_changed else [],
                "created_files": [],
                "next_actions": [],
            }
        scaffold_res = cls._scaffold_lean(root, speckit=(root / ".specify").is_dir(), skip_config=True)
        created = list(scaffold_res.get("created_files", []))
        updated = list(scaffold_res.get("updated_files", []))
        if config_changed:
            modern.write_text(desired_text, encoding="utf-8")
            updated.insert(0, ".forgeflow/config.json")
        status = "applied" if created or updated else "no-op"
        return {
            "status": status,
            "target_dir": str(root),
            "complete": True,
            "previous_version": previous_version,
            "current_version": __version__,
            "created_files": sorted(set(created)),
            "updated_files": sorted(set(updated)),
            "removed_files": [],
            "preserved_files": [],
            "conflicts": [],
            "blockers": [],
            "warnings": [],
            "next_actions": [],
            "baseline": scaffold_res.get("baseline"),
            "preserved_legacy_config": legacy.exists(),
        }

    @classmethod
    def find_changelog_file(cls, root: Optional[Path] = None) -> Optional[Path]:
        """Locate CHANGELOG.md from installed package or source tree."""
        candidates = []
        if root:
            candidates.append(root / "docs" / "CHANGELOG.md")
            candidates.append(root / "src" / "forgeflow" / "CHANGELOG.md")
            candidates.append(root / "docs" / "spec" / "CHANGELOG.md")

        # 1. Directly packaged with current python module
        candidates.append(Path(__file__).parent / "CHANGELOG.md")
        candidates.append(Path(__file__).parent / "templates" / "spec" / "CHANGELOG.md")

        # 2. Local workspace repository
        try:
            repo_root = HierarchicalRootScanner.find_root()
            candidates.append(repo_root / "docs" / "CHANGELOG.md")
            candidates.append(repo_root / "src" / "forgeflow" / "CHANGELOG.md")
            candidates.append(repo_root / "docs" / "spec" / "CHANGELOG.md")
        except Exception:
            pass

        # 3. Global installed packages
        candidates.append(Path.home() / ".local" / "share" / "forgeflow" / "CHANGELOG.md")
        candidates.append(Path.home() / ".local" / "forgeflow" / "CHANGELOG.md")
        candidates.append(Path.home() / ".local" / "forgeflow" / "current" / "lib" / "forgeflow" / "templates" / "spec" / "CHANGELOG.md")

        for c in candidates:
            if c.is_file():
                return c
        return None

    @classmethod
    def summarize_changelog_section(cls, section: str) -> str:
        """Summarize a single release markdown section into:
        [<version>] - <date>
        - <title or first bullet>
        """
        if not section:
            return ""

        lines = [line.strip() for line in section.strip().splitlines() if line.strip()]
        if not lines:
            return ""

        header = lines[0]
        if header.startswith("## "):
            header = header[3:].strip()

        standard_categories = {
            "added", "changed", "fixed", "removed", "deprecated", "security",
            "added & improved", "improved", "breaking changes"
        }

        summary_line = ""
        # 1. Look for a custom title line under ###
        for line in lines[1:]:
            if line.startswith("### "):
                title_text = line[4:].strip()
                clean_title = re.sub(r"^[^\w\s]+", "", title_text).strip().lower()
                if clean_title not in standard_categories and title_text.lower() not in standard_categories:
                    summary_line = f"- {title_text}"
                    break

        # 2. If no custom title line, find the first bullet point
        if not summary_line:
            for line in lines[1:]:
                if line.startswith("- "):
                    summary_line = line
                    break

        # 3. Fallback to first non-empty line after header
        if not summary_line:
            if len(lines) > 1:
                cand = lines[1].lstrip("#").strip()
                summary_line = f"- {cand}"
            else:
                summary_line = "- (세부 변경 사항 없음)"

        return f"{header}\n{summary_line}"

    @classmethod
    def extract_changelog_section(cls, version: str, changelog_file: Optional[Path] = None, summary: bool = False) -> Optional[str]:
        """Extract a single release section from CHANGELOG.md."""
        target_file = changelog_file or cls.find_changelog_file()
        if not target_file or not target_file.is_file():
            return None

        clean_v = version.lstrip("v").strip()
        try:
            text = target_file.read_text(encoding="utf-8")
        except Exception:
            return None

        pattern = re.compile(
            rf"(?ms)^##\s*\[\s*{re.escape(clean_v)}\s*\].*?(?=^##\s*\[|\Z)"
        )
        match = pattern.search(text)
        if match:
            raw = match.group(0).strip()
            return cls.summarize_changelog_section(raw) if summary else raw
        return None

    @classmethod
    def extract_changelog_range(cls, prev_ver: str, curr_ver: str, changelog_file: Optional[Path] = None, summary: bool = True) -> Optional[str]:
        """Extract release sections between previous and current versions."""
        target_file = changelog_file or cls.find_changelog_file()
        if not target_file or not target_file.is_file():
            return None

        try:
            text = target_file.read_text(encoding="utf-8")
        except Exception:
            return None

        from .cli import parse_version_tuple
        prev_tuple = parse_version_tuple(prev_ver)
        curr_tuple = parse_version_tuple(curr_ver)

        section_pattern = re.compile(r"(?ms)^##\s*\[\s*([^\]]+)\s*\].*?(?=^##\s*\[|\Z)")
        matched_sections = []
        for match in section_pattern.finditer(text):
            ver_str = match.group(1).strip()
            v_tuple = parse_version_tuple(ver_str)
            if prev_tuple < v_tuple <= curr_tuple:
                raw_sec = match.group(0).strip()
                matched_sections.append(cls.summarize_changelog_section(raw_sec) if summary else raw_sec)

        if matched_sections:
            return "\n\n".join(matched_sections)
        return cls.extract_changelog_section(curr_ver, changelog_file=target_file, summary=summary)


def resolve_auto_create_branch(repo_root: Path) -> bool:
    """Resolve auto_create_branch configuration from .forgeflow/config.json (or fallback .forgeflow.json).

    Returns:
        bool: False by default if omitted or file missing.
              True or False if explicitly specified as a boolean.
    Raises:
        ValueError: If configuration contains an invalid non-boolean auto_create_branch.
    """
    root = Path(repo_root).resolve()
    modern_cfg = root / ".forgeflow" / "config.json"
    legacy_cfg = root / ".forgeflow.json"
    config_file = modern_cfg if modern_cfg.exists() else legacy_cfg
    if not config_file.exists() or not config_file.is_file():
        return False

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse {config_file.name}: {exc}") from exc

    if not isinstance(data, dict):
        return False

    workflow = data.get("workflow", {})
    if not isinstance(workflow, dict):
        raise ValueError("workflow configuration must be an object")
    owner = workflow.get("owner", "standalone")
    if owner not in {"standalone", "host"}:
        raise ValueError("workflow.owner must be standalone or host")
    if owner == "host":
        return False

    gov = data.get("governance")
    if not isinstance(gov, dict):
        return False

    if "auto_create_branch" not in gov:
        return False

    val = gov["auto_create_branch"]
    if not isinstance(val, bool):
        raise ValueError(
            f"Invalid auto_create_branch in {config_file.name}: expected boolean, got {type(val).__name__} ({val!r})"
        )

    return val


TemplateScaffolder.resolve_auto_create_branch = staticmethod(resolve_auto_create_branch)

