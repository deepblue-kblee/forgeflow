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

from .validator import TierRules
from ._version import __version__
from .legacy_templates import LEGACY_TEMPLATES


class TemplateScaffolder:
    """Loads templates from package resources and scaffolds release documents."""

    BOOT_ANCHOR_START = "<!-- forgeflow:boot-anchor:start -->"
    BOOT_ANCHOR_END = "<!-- forgeflow:boot-anchor:end -->"
    BOOT_ANCHOR_TEMPLATE = (
        "<!-- forgeflow:boot-anchor:start -->\n"
        "## 🌊 ForgeFlow Session Boot Sequence (Harness Governance)\n\n"
        "모든 작업 시작 전, AI 에이전트는 다음 규칙과 사양을 반드시 확인하고 준수해야 합니다:\n"
        "1. **헌법 및 3대 메커니즘**: `.specify/memory/constitution.md` 및 `docs/spec/SPECKIT_HOOKS_AND_NORMS.md` 확인\n"
        "2. **공식 사양서 참조**: `forgeflow doc list` 또는 `~/.local/forgeflow/current/lib/forgeflow/templates/spec/`의 7대 공식 사양서(`FLOW_SPEC.md` 등) 참조\n"
        "3. **게이트 통제**: `tasks/in-progress/<id>/GATE1_REVIEW.md` 승인 전 소스 코드 작성/수정 절대 금지 (No Code Before Gate 1 Pass)\n"
        "4. **원자적 루프 및 멈춤**: 단순 테스트 실패 시 자가 치유(Loop 2) 자율 완주, 5회 연속 실패 시 진짜 멈춤(True Stop)\n"
        "<!-- forgeflow:boot-anchor:end -->"
    )

    GOVERNANCE_PATH = Path("docs/forgeflow/GOVERNANCE.md")
    ROOT_GUIDES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")
    BINDING_START = "<!-- forgeflow-governance-binding:start -->"
    BINDING_END = "<!-- forgeflow-governance-binding:end -->"
    JOURNAL_PATH = Path(".forgeflow-init-journal.json")
    JOURNAL_VERSION = 1
    TASKS_GUARD_CONTENT = (
        "# ⚠️ Tasks Workspace (Non-Guidance Boundary)\n\n"
        "이 디렉터리는 순수 작업 진행 및 산출물 보관소입니다.\n"
        "거버넌스 및 행동 지침 규칙이 일절 포함되어 있지 않으므로, AI 에이전트는 규칙/지침 판단을 위해 이 디렉터리를 참조해서는 안 됩니다.\n"
        "모든 규칙의 단일 진실 공급원(SSOT)은 `docs/spec/`, `docs/forgeflow/GOVERNANCE.md`, 또는 `AGENTS.md`입니다.\n"
    )
    BUNDLE_FILES = {
        Path("docs/forgeflow/spec/CHANGELOG.md"): "spec/CHANGELOG.md",
        Path("docs/forgeflow/spec/FLOW_SPEC.md"): "spec/FLOW_SPEC.md",
        Path("docs/forgeflow/spec/GATES_AND_LOOPS.md"): "spec/GATES_AND_LOOPS.md",
        Path("docs/forgeflow/spec/SPECKIT_HOOKS_AND_NORMS.md"): "spec/SPECKIT_HOOKS_AND_NORMS.md",
        Path("docs/forgeflow/spec/ANTI_PATTERNS.md"): "spec/ANTI_PATTERNS.md",
        Path("docs/forgeflow/templates/COMPLETION_REPORT.md"): "COMPLETION_REPORT.md",
        Path("docs/forgeflow/templates/QA_SIGNOFF.md"): "QA_SIGNOFF.md",
        Path("docs/forgeflow/templates/RELEASE_SIGNOFF.md"): "RELEASE_SIGNOFF.md",
    }
    LEGACY_BINDING = (
        "### ForgeFlow 거버넌스 및 라이프사이클 준수 규범 (ForgeFlow Governance Binding)\n"
        "모든 신규 기능 추가, 인프라 연동, 릴리즈 작업은 docs/framework/flow/ (또는 관련 spec 경로)의 \n"
        "ForgeFlow 프레임워크 규격(FLOW_SPEC, GATES_AND_LOOPS)을 100% 강제 준수하여 수행한다.\n"
        "1. 사전 검증 게이트(Gate 1) 완수 전 구현 착수 금지 (No Code Before Gate 1 Pass): 위험도 판정(Tier 1/2/3)에 따른 사전 심사(Tier 3: 3인 독립 패널 심사) 통과 및 DESIGN_REVIEW.md 승인 전에는 구현 코드를 작성할 수 없다.\n"
        "2. 5단계 폐루프 임의 축약 금지: Stage 1(기획/설계) ➔ Stage 2(Gate 1 사전 심사) ➔ Stage 3~4(격리 구현 및 회귀 테스트) ➔ Stage 5(Gate 2 QA 승인 & 승격) 수명주기를 절대 건너뛰지 않는다."
    )
    LEGACY_BINDING_HEADING = "### ForgeFlow 거버넌스 및 라이프사이클 준수 규범 (ForgeFlow Governance Binding)"

    @classmethod
    def governance_binding(cls) -> str:
        return (
            "\n\n" + cls.BINDING_START + "\n"
            "## ForgeFlow Governance\n\n"
            "At the start of every session, always read `docs/forgeflow/GOVERNANCE.md` and comply with its rules.\n"
            + cls.BINDING_END + "\n"
        )

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

    @classmethod
    def _ensure_safe_directory(
        cls, path: Path, root: Path, created_directories: Optional[List[Path]] = None
    ) -> None:
        current = root
        for part in path.relative_to(root).parts:
            current = current / part
            if not current.exists():
                current.mkdir()
                if created_directories is not None:
                    created_directories.append(current)
            cls._assert_safe_directory(current, root)

    @classmethod
    def _stage_write(cls, path: Path, content: str, root: Path) -> Path:
        cls._assert_safe_file(path, root, allow_missing=True)
        descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.forgeflow-", dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
            return temporary
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    @classmethod
    def _journal_target(cls, root: Path, target: str) -> Path:
        allowed = {
            str(cls.GOVERNANCE_PATH),
            ".forgeflow.json",
            *cls.ROOT_GUIDES,
            *(str(path) for path in cls.BUNDLE_FILES),
        }
        target_path = Path(target)
        backup_prefix = cls.GOVERNANCE_PATH.name + ".bak"
        is_governance_backup = (
            target_path.parent == cls.GOVERNANCE_PATH.parent
            and (
                target_path.name == backup_prefix
                or (
                    target_path.name.startswith(backup_prefix + ".")
                    and target_path.name[len(backup_prefix) + 1 :].isdigit()
                )
            )
        )
        if target not in allowed and not is_governance_backup:
            raise ValueError(f"Invalid governance transaction target: {target}")
        return root / target_path

    @classmethod
    def _write_journal(cls, root: Path, journal: Dict[str, Any]) -> None:
        journal_path = root / cls.JOURNAL_PATH
        cls._assert_safe_file(journal_path, root, allow_missing=True)
        temporary = cls._stage_write(
            journal_path, json.dumps(journal, ensure_ascii=False, sort_keys=True), root
        )
        try:
            cls._assert_safe_file(journal_path, root, allow_missing=True)
            os.replace(temporary, journal_path)
        finally:
            temporary.unlink(missing_ok=True)

    @classmethod
    def _recover_governance_transaction(cls, root: Path) -> None:
        """Recover only a strictly validated, fixed-schema interrupted transaction."""
        journal_path = root / cls.JOURNAL_PATH
        if not journal_path.exists() and not journal_path.is_symlink():
            return
        cls._assert_safe_file(journal_path, root)
        try:
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
            txid = uuid.UUID(journal["transaction_id"])
            entries = journal["entries"]
            if (
                set(journal) != {"version", "transaction_id", "entries"}
                or journal["version"] != cls.JOURNAL_VERSION
                or not isinstance(entries, list)
            ):
                raise ValueError("invalid journal schema")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid ForgeFlow governance transaction journal") from exc

        validated = []
        for index, entry in enumerate(entries):
            if set(entry) != {"target", "operation", "backup"}:
                raise ValueError("Invalid ForgeFlow governance transaction journal")
            target = cls._journal_target(root, entry["target"])
            operation, backup_name = entry["operation"], entry["backup"]
            if operation not in {"created", "replaced"}:
                raise ValueError("Invalid ForgeFlow governance transaction journal")
            expected_backup = f".forgeflow-init-{txid}-{index}.bak"
            if operation == "created":
                if backup_name is not None:
                    raise ValueError("Invalid ForgeFlow governance transaction journal")
                backup = None
            elif backup_name != expected_backup:
                raise ValueError("Invalid ForgeFlow governance transaction journal")
            else:
                backup = root / backup_name
                cls._assert_safe_file(backup, root)
            cls._assert_safe_file(target, root, allow_missing=True)
            validated.append((target, operation, backup))

        for target, operation, backup in reversed(validated):
            if operation == "created":
                target.unlink(missing_ok=True)
            else:
                original = backup.read_text(encoding="utf-8")
                temporary = cls._stage_write(target, original, root)
                try:
                    os.replace(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)
        journal_path.unlink()
        for _, _, backup in validated:
            if backup is not None:
                backup.unlink(missing_ok=True)

    @classmethod
    def _apply_governance_transaction(cls, root: Path, desired: Dict[Path, str]) -> None:
        """Stage all changes, then restore prior contents if any replacement fails."""
        originals: Dict[Path, Optional[str]] = {}
        staged: Dict[Path, Path] = {}
        replaced: List[Path] = []
        backups: Dict[Path, Path] = {}
        journal_path = root / cls.JOURNAL_PATH
        transaction_id = uuid.uuid4()
        try:
            for path, content in desired.items():
                cls._assert_safe_file(path, root, allow_missing=True)
                originals[path] = path.read_text(encoding="utf-8") if path.exists() else None
                staged[path] = cls._stage_write(path, content, root)
            entries = []
            for index, path in enumerate(desired):
                target = str(path.relative_to(root))
                # Recovery is intentionally constrained to the fixed governance targets.
                cls._journal_target(root, target)
                if originals[path] is None:
                    entries.append({"target": target, "operation": "created", "backup": None})
                    continue
                backup = root / f".forgeflow-init-{transaction_id}-{index}.bak"
                cls._assert_safe_file(backup, root, allow_missing=True)
                temporary = cls._stage_write(backup, originals[path], root)
                os.replace(temporary, backup)
                backups[path] = backup
                entries.append({"target": target, "operation": "replaced", "backup": backup.name})
            cls._write_journal(
                root,
                {"version": cls.JOURNAL_VERSION, "transaction_id": str(transaction_id), "entries": entries},
            )
            for path in desired:
                cls._assert_safe_file(path, root, allow_missing=True)
                os.replace(staged[path], path)
                replaced.append(path)
        except Exception:
            rollback_error = None
            for path in reversed(replaced):
                try:
                    cls._assert_safe_file(path, root, allow_missing=True)
                    original = originals[path]
                    if original is None:
                        path.unlink(missing_ok=True)
                    else:
                        temporary = cls._stage_write(path, original, root)
                        os.replace(temporary, path)
                except Exception as exc:
                    rollback_error = exc
            if rollback_error is not None:
                raise RuntimeError("Governance transaction rollback failed") from rollback_error
            for backup in backups.values():
                backup.unlink(missing_ok=True)
            journal_path.unlink(missing_ok=True)
            raise
        else:
            # Keep the recovery evidence until the committed transaction is no
            # longer advertised.  If journal cleanup fails, the backups remain
            # available for the next invocation to recover safely.
            journal_path.unlink()
            for backup in backups.values():
                backup.unlink(missing_ok=True)
        finally:
            for temporary in staged.values():
                temporary.unlink(missing_ok=True)

    @classmethod
    def scaffold_governance_binding(
        cls,
        project_root: Path,
        refresh: bool = False,
        force: bool = False,
        bind_root_guides: bool = True,
        migrate_legacy: bool = False,
        additional_files: Optional[Dict[Path, str]] = None,
        created_directories: Optional[List[Path]] = None,
    ) -> Dict[str, List[str]]:
        """Create the central guide and idempotently bind supported root guides."""
        root = project_root.absolute()
        if root.is_symlink() or not root.is_dir():
            raise ValueError(f"Unsafe project root: {project_root}")
        root = root.resolve(strict=True)
        cls._recover_governance_transaction(root)
        central = root / cls.GOVERNANCE_PATH
        cls._ensure_safe_directory(central.parent, root, created_directories)
        for bundled_path in cls.BUNDLE_FILES:
            cls._ensure_safe_directory((root / bundled_path).parent, root, created_directories)
        cls._assert_safe_file(central, root, allow_missing=True)
        result = {"created": [], "updated": [], "skipped": []}
        desired: Dict[Path, str] = {}
        if additional_files:
            for path, content in additional_files.items():
                absolute_path = path if path.is_absolute() else root / path
                if absolute_path != root / ".forgeflow.json":
                    raise ValueError(f"Invalid additional governance target: {path}")
                cls._assert_safe_file(absolute_path, root, allow_missing=True)
                desired[absolute_path] = content
        if not central.exists():
            desired[central] = cls.get_template_content("GOVERNANCE.md")
            (result["updated"] if force else result["created"]).append(str(cls.GOVERNANCE_PATH))
        elif refresh:
            backup = central.with_name(central.name + ".bak")
            index = 1
            while backup.exists():
                backup = central.with_name(central.name + f".bak.{index}")
                index += 1
            cls._assert_safe_file(backup, root, allow_missing=True)
            desired[backup] = central.read_text(encoding="utf-8")
            desired[central] = cls.get_template_content("GOVERNANCE.md")
            result["updated"].append(str(cls.GOVERNANCE_PATH))
        elif force:
            desired[central] = cls.get_template_content("GOVERNANCE.md")
            result["updated"].append(str(cls.GOVERNANCE_PATH))
        else:
            result["skipped"].append(str(cls.GOVERNANCE_PATH))
        for bundled_path, resource_name in cls.BUNDLE_FILES.items():
            destination = root / bundled_path
            cls._assert_safe_file(destination, root, allow_missing=True)
            if destination.exists() and not force:
                result["skipped"].append(str(bundled_path))
            else:
                desired[destination] = cls.get_template_content(resource_name)
                (result["updated"] if force else result["created"]).append(str(bundled_path))
        if not bind_root_guides:
            cls._apply_governance_transaction(root, desired)
            return result
        expected = cls.governance_binding().strip()
        processed_guides = set()
        for name in cls.ROOT_GUIDES:
            guide = root / name
            if guide.is_symlink():
                try:
                    target = guide.resolve(strict=True)
                    target.relative_to(root)
                    if target.parent != root or target.name not in cls.ROOT_GUIDES or target.is_symlink() or not target.is_file():
                        raise ValueError
                    guide = target
                except (OSError, ValueError):
                    result["skipped"].append(f"{name} (symbolic link outside project or unsafe; not modified)")
                    continue
            if guide in processed_guides:
                result["skipped"].append(f"{name} (symbolic link; target already bound)")
                continue
            processed_guides.add(guide)
            cls._assert_safe_file(guide, root, allow_missing=True)
            content = guide.read_text(encoding="utf-8") if guide.exists() else ""
            starts, ends = content.count(cls.BINDING_START), content.count(cls.BINDING_END)
            if starts == ends == 0:
                if migrate_legacy and cls.LEGACY_BINDING_HEADING in content:
                    if content.count(cls.LEGACY_BINDING_HEADING) != 1 or cls.LEGACY_BINDING not in content:
                        raise ValueError(
                            f"Unrecognized legacy ForgeFlow governance binding: {guide}; migrate it manually"
                        )
                    content = content.replace(cls.LEGACY_BINDING, cls.governance_binding().strip(), 1)
                    desired[guide] = content
                    result["updated"].append(name)
                    continue
                desired[guide] = content.rstrip() + cls.governance_binding()
                result["created" if not content else "updated"].append(name)
            elif starts == ends == 1:
                start, end = content.find(cls.BINDING_START), content.find(cls.BINDING_END)
                block = content[start:end + len(cls.BINDING_END)].strip() if start <= end else ""
                if block != expected:
                    raise ValueError(f"Invalid ForgeFlow governance binding markers: {guide}")
                result["skipped"].append(name)
            else:
                raise ValueError(f"Invalid ForgeFlow governance binding markers: {guide}")
        if desired:
            cls._apply_governance_transaction(root, desired)
        return result

    @staticmethod
    def get_template_content(template_name: str, custom_template_dir: Optional[Path] = None) -> str:
        """Load template string from custom directory, package resources, or fallback."""
        if custom_template_dir:
            custom_path = Path(custom_template_dir) / template_name
            if custom_path.exists():
                return custom_path.read_text(encoding="utf-8")

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

        # Fallback for deprecated legacy templates preserved for backwards compatibility
        if template_name in LEGACY_TEMPLATES:
            return LEGACY_TEMPLATES[template_name]

        raise FileNotFoundError(f"Template '{template_name}' not found in package resources.")

    @staticmethod
    def render_template(content: str, variables: Dict[str, str]) -> str:
        for k, v in variables.items():
            content = content.replace(f"{{{{{k}}}}}", str(v))
        return content

    @classmethod
    def resolve_release_dir(cls, repo_root: Path, release_id: str, stage: str = "in-progress") -> Path:
        """Resolve destination directory for a release, favoring tasks/<stage>/<id> or legacy docs/releases/<id>."""
        from .scanner import ReleaseScanner
        existing = ReleaseScanner.find_release_path(repo_root, release_id)
        if existing:
            return existing

        tasks_dir = ReleaseScanner._read_configured_tasks_dir(repo_root)
        if tasks_dir:
            return repo_root / tasks_dir / stage / release_id

        if (repo_root / "tasks").exists() and (repo_root / "tasks").is_dir():
            return repo_root / "tasks" / stage / release_id
        if (repo_root / "ff-tasks").exists() and (repo_root / "ff-tasks").is_dir():
            return repo_root / "ff-tasks" / stage / release_id
        if (repo_root / "docs" / "releases").exists():
            return repo_root / "docs" / "releases" / release_id

        return repo_root / "tasks" / stage / release_id

    @classmethod
    def create_release_scaffold(
        cls,
        target_dir: Path,
        release_id: str,
        tier: int = 2,
        variables: Optional[Dict[str, str]] = None,
        force: bool = False,
        custom_template_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """Create the core governance files in target_dir."""
        target_dir.mkdir(parents=True, exist_ok=True)

        # Ensure tasks/README.md guard if created inside tasks or ff-tasks
        for p in [target_dir, *target_dir.parents]:
            if p.name in ("tasks", "ff-tasks") and p != target_dir:
                guard = p / "README.md"
                if not guard.exists():
                    guard.write_text(cls.TASKS_GUARD_CONTENT, encoding="utf-8")
                break

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        tier_name = TierRules.get_tier_name(tier)

        base_vars = {
            "RELEASE_ID": release_id,
            "TIER": str(tier),
            "TIER_NAME": tier_name,
            "DATE": today,
            "BACKGROUND_SUMMARY": "프로젝트 요구사항 및 배경 요약",
            "OBJECTIVE_1": "핵심 구현 목표 1",
            "OBJECTIVE_2": "핵심 구현 목표 2",
            "FEATURE_TITLE_1": "기능 1 명세",
            "FEATURE_SPEC_1": "기능 1의 상세 동작 및 제약 조건",
            "FEATURE_TITLE_2": "기능 2 명세",
            "FEATURE_SPEC_2": "기능 2의 상세 동작 및 제약 조건",
            "NON_FUNC_TITLE_1": "성능 및 안전성",
            "NON_FUNC_SPEC_1": "비기능적 성능/보안 기준",
            "NON_FUNC_TITLE_2": "테스트 커버리지",
            "NON_FUNC_SPEC_2": "회귀 테스트 100% 통과 의무화",
            "CRITERIA_1": "기능 1 동작 검증 완료",
            "CRITERIA_2": "기능 2 단위 테스트 통과",
            "PREVIOUS_FORGEFLOW_VERSION_OR_NA": "N/A",
            "TARGET_FORGEFLOW_VERSION_OR_NA": "N/A",
            "FORGEFLOW_VERSION_BUMP_TYPE_OR_NA": "N/A",
            "FORGEFLOW_VERSION_CHANGE_REASON_OR_NA": "N/A",
            "ARCHITECTURE_OVERVIEW": "아키텍처 구조 및 데이터 플로우 설명",
            "COMPONENT_STRUCTURE": "컴포넌트 구성 요소 및 역할",
            "IO_SPEC": "I/O 프로토콜 및 인터페이스 명세",
            "MODULE_1": "core_module",
            "MODULE_2": "sub_module",
            "MODULE_3": "resilience_module",
            "MODULE_4": "test_suite",
            "TEST_1": "test_core_feature",
            "TEST_2": "test_sub_feature",
            "TEST_3": "test_resilience",
            "TEST_4": "test_regression",
            "TOTAL_TESTS": "10",
            "PASSED_TESTS": "10",
            "REQ_F01_TITLE": "기능 1 검증",
            "REQ_F02_TITLE": "기능 2 검증",
            "RELEASE_SUMMARY": f"릴리즈 {release_id} 작업이 성공적으로 완료되었습니다.",
            "ACHIEVEMENT_1": "핵심 기능 구현 및 단위 테스트 통과",
            "ACHIEVEMENT_2": "하네스 거버넌스 게이트 100% 통과",
            "IMPROVEMENT_1": "향후 개선 과제 1",
            "IMPROVEMENT_2": "향후 개선 과제 2",
            "EXTERNAL_CLAIM_SCOPE_OR_NA": "N/A",
            "OBSERVED_FAILURE_CLASS_OR_NA": "N/A",
            "SAFETY_BOUNDARY_OR_NA": "N/A",
            "SUCCESS_AND_FAILURE_ORACLES_OR_NA": "N/A",
            "PROPERTY_ID": "01",
            "FIXTURE_ID": "SAMPLE",
            "ORACLE_ID": "ORACLE-SAMPLE",
            "REQ_ID": "REQ-F01",
            "PROPERTY_OR_FEATURE": "N/A",
            "FIXTURE_PATH_OR_REASON": "N/A",
            "FIXTURE_STRATEGY_OR_NA": "N/A",
            "PUBLIC_ENTRYPOINT": "bin/entrypoint",
            "PROBE_COMMAND": "entrypoint --help",
            "WAIVER_PROTOCOL_OR_NA": "N/A",
            "DELIVERY_TARGET_OR_NA": "N/A",
            "ARTIFACT_IDENTITY_OR_NA": "N/A",
            "ARTIFACT_SHA256_OR_NA": "N/A",
            "EXPECTED_PUBLIC_ENTRYPOINT_OR_NA": "N/A",
            "PROBE_COMMAND_OR_NA": "N/A",
            "PROBE_EXIT_CODE_OR_NA": "0",
            "PROBE_RESULT_OR_NA": "N/A",
            "WAIVER_RATIONALE_OR_NA": "N/A",
        }
        if variables:
            base_vars.update(variables)

        created_files = {}
        if tier == 1:
            change_note = target_dir / "CHANGE_NOTE.md"
            if force or not change_note.exists():
                change_note.write_text(
                    f"# Change Note: {release_id}\n\n- Tier: 1\n\n## Scope\n\nPending implementation details.\n\n## Gate 1 Self-Review\n\nPENDING\n\n## Gate 2 Evidence\n\nPENDING\n",
                    encoding="utf-8",
                )
                created_files["CHANGE_NOTE.md"] = change_note
            release_notes = target_dir / "RELEASE_NOTES.md"
            if force or not release_notes.exists():
                raw_content = TemplateScaffolder.get_template_content(
                    "RELEASE_NOTES.md", custom_template_dir=custom_template_dir
                )
                release_notes.write_text(
                    TemplateScaffolder.render_template(raw_content, base_vars), encoding="utf-8"
                )
                created_files["RELEASE_NOTES.md"] = release_notes
            return created_files

        template_files = ["PRD.md", "DESIGN.md", "ROADMAP.md", "QA_SIGNOFF.md", "RELEASE_SIGNOFF.md", "COMPLETION_REPORT.md", "RELEASE_NOTES.md"]

        for tmpl in template_files:
            raw_content = TemplateScaffolder.get_template_content(tmpl, custom_template_dir=custom_template_dir)
            rendered = TemplateScaffolder.render_template(raw_content, base_vars)
            dest_file = target_dir / tmpl
            if not dest_file.exists() or force:
                dest_file.write_text(rendered, encoding="utf-8")
                created_files[tmpl] = dest_file

        return created_files

    @staticmethod
    def init_project_governance(
        project_root: Path,
        project_name: Optional[str] = None,
        force: bool = False,
        refresh_governance: bool = False,
        migrate_governance_binding: bool = False,
        continuation_policy: str = "interactive",
        migrate_continuation_policy: bool = False,
    ) -> Dict[str, Any]:
        """Initialize docs/releases, standard directories, and .forgeflow.json configuration."""
        root_candidate = project_root.absolute()
        TemplateScaffolder._assert_no_symlink_creation_parent(root_candidate)
        if root_candidate.exists() and (root_candidate.is_symlink() or not root_candidate.is_dir()):
            raise ValueError(f"Unsafe project root: {project_root}")
        root_created = not root_candidate.exists()
        project_root.mkdir(parents=True, exist_ok=True)
        root = project_root.resolve(strict=True)
        created_directory_paths: List[Path] = []
        created_dirs: List[str] = []
        try:
            # If tasks exists as a file, fallback to ff-tasks
            tasks_dir_name = "tasks"
            if (root / "tasks").exists() and not (root / "tasks").is_dir():
                tasks_dir_name = "ff-tasks"

            standard_dirs = [
                "docs",
                tasks_dir_name,
                f"{tasks_dir_name}/backlog",
                f"{tasks_dir_name}/in-progress",
                f"{tasks_dir_name}/completed",
                "src",
                "tests",
            ]
            for d in standard_dirs:
                dir_path = root / d
                if dir_path.exists() or dir_path.is_symlink():
                    TemplateScaffolder._assert_safe_directory(dir_path, root)

            for d in standard_dirs:
                dir_path = root / d
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_directory_paths.append(dir_path)
                TemplateScaffolder._assert_safe_directory(dir_path, root)
                if d != "docs":
                    created_dirs.append(d)

            # Ensure tasks guard
            guard_file = root / tasks_dir_name / "README.md"
            if not guard_file.exists():
                guard_file.write_text(TemplateScaffolder.TASKS_GUARD_CONTENT, encoding="utf-8")

            name = project_name or root.name or "my-project"
            slug = name.lower().replace(" ", "-").replace("_", "-")

            if continuation_policy not in {"interactive", "autonomous"}:
                raise ValueError("Invalid continuation policy")
            config_data = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "version": "0.1.0",
            "forgeflow_version": __version__,
            "project": {
                "name": name,
                "slug": slug,
                "root": ".",
            },
            "governance": {
                "default_tier": 2,
                "continuation_policy": continuation_policy,
                "tasks_dir": tasks_dir_name,
                "strict_mode": True,
                "required_documents": [
                    "PRD.md",
                    "DESIGN.md",
                    "QA_SIGNOFF.md",
                    "COMPLETION_REPORT.md",
                ],
            },
            "runtime": {
                "test_runner": "unittest",
                "test_command": "python3 -m unittest discover -s tests",
                "auto_heal": {
                    "enabled": True,
                    "max_retries": 5,
                },
            },
            "paths": {
                "releases": tasks_dir_name,
                "source": "src",
                "tests": "tests",
            },
            }

            config_file = root / ".forgeflow.json"
            config_existed = config_file.exists()
            config_should_write = not config_existed or force
            if config_existed and migrate_continuation_policy and not force:
                TemplateScaffolder._assert_safe_file(config_file, root)
                try:
                    existing_config = json.loads(config_file.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    raise ValueError("Invalid existing ForgeFlow configuration") from exc
                if not isinstance(existing_config, dict) or not isinstance(existing_config.get("governance"), dict):
                    raise ValueError("Invalid existing ForgeFlow configuration")
                existing_policy = existing_config["governance"].get("continuation_policy")
                if existing_policy is None:
                    existing_config["governance"]["continuation_policy"] = continuation_policy
                    config_data = existing_config
                    config_should_write = True
                elif existing_policy not in {"interactive", "autonomous"}:
                    raise ValueError("Invalid existing continuation policy")
                elif existing_policy != continuation_policy:
                    raise ValueError("Existing continuation policy differs; refuse replacement")
            additional_files = (
                {config_file: json.dumps(config_data, indent=2, ensure_ascii=False) + "\n"}
                if config_should_write
                else None
            )
            governance = TemplateScaffolder.scaffold_governance_binding(
                root,
                refresh=refresh_governance,
                force=force,
                bind_root_guides=not force,
                migrate_legacy=migrate_governance_binding,
                additional_files=additional_files,
                created_directories=created_directory_paths,
            )
        except Exception:
            # Files are restored by the journal transaction.  Remove only
            # directories this invocation created, and only when still empty.
            for directory in reversed(created_directory_paths):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            if root_created:
                try:
                    root.rmdir()
                except OSError:
                    pass
            raise

        created_files: List[str] = []
        updated_files: List[str] = []
        skipped_files: List[str] = []
        if config_should_write:
            (updated_files if force or config_existed else created_files).append(".forgeflow.json")
        else:
            skipped_files.append(".forgeflow.json")
        created_files.extend(governance["created"])
        updated_files.extend(governance["updated"])
        skipped_files.extend(governance["skipped"])

        return {
            "project_name": name,
            "project_root": str(root),
            "created_dirs": created_dirs,
            "created_files": created_files,
            "updated_files": updated_files,
            "skipped_files": skipped_files,
        }

    @classmethod
    def migrate_to_tasks(cls, repo_root: Path, target_dir_name: str = "tasks") -> Dict[str, Any]:
        """Migrate legacy docs/releases/ to root tasks/completed/ directory."""
        legacy_dir = repo_root / "docs" / "releases"
        if not legacy_dir.exists() or not legacy_dir.is_dir():
            return {"migrated": [], "status": "skipped", "reason": "no legacy docs/releases found"}

        tasks_root = repo_root / target_dir_name
        if tasks_root.exists() and not tasks_root.is_dir():
            target_dir_name = "ff-tasks"
            tasks_root = repo_root / target_dir_name

        completed_dir = tasks_root / "completed"
        in_progress_dir = tasks_root / "in-progress"
        backlog_dir = tasks_root / "backlog"

        completed_dir.mkdir(parents=True, exist_ok=True)
        in_progress_dir.mkdir(parents=True, exist_ok=True)
        backlog_dir.mkdir(parents=True, exist_ok=True)

        guard = tasks_root / "README.md"
        if not guard.exists():
            guard.write_text(cls.TASKS_GUARD_CONTENT, encoding="utf-8")

        migrated: List[str] = []
        import shutil
        for child in sorted(legacy_dir.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                dest = completed_dir / child.name
                if not dest.exists():
                    shutil.move(str(child), str(dest))
                    migrated.append(child.name)

        config_path = repo_root / ".forgeflow.json"
        if config_path.exists() and config_path.is_file():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data.setdefault("governance", {})["tasks_dir"] = target_dir_name
                    data.setdefault("paths", {})["releases"] = target_dir_name
                    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            except Exception:
                pass

        return {
            "status": "success",
            "target_dir": target_dir_name,
            "migrated": migrated,
            "count": len(migrated),
        }

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
        """Scaffold lightweight GitHub Spec Kit and ForgeFlow hybrid governance environment."""
        root = root.resolve()
        created_dirs: List[str] = []
        created_files: List[str] = []
        updated_files: List[str] = []

        config_file = root / ".forgeflow.json"
        custom_tasks_name = "tasks"
        if config_file.is_file():
            try:
                raw_cfg = json.loads(config_file.read_text(encoding="utf-8"))
                if isinstance(raw_cfg, dict):
                    custom_tasks_name = raw_cfg.get("governance", {}).get("tasks_dir", "tasks")
            except Exception:
                pass

        # 1. Tasks directories
        tasks_dir = root / custom_tasks_name
        in_progress_dir = tasks_dir / "in-progress"
        completed_dir = tasks_dir / "completed"
        for d in (tasks_dir, in_progress_dir, completed_dir):
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(d.relative_to(root)))

        guard_file = tasks_dir / "README.md"
        if not guard_file.exists() or force:
            guard_file.write_text(cls.TASKS_GUARD_CONTENT, encoding="utf-8")
            (updated_files if guard_file.exists() and force else created_files).append(f"{custom_tasks_name}/README.md")

        # 2. .forgeflow.json (with Date-Based Amnesia enforcement and user config preservation)
        if not skip_config:
            default_config = {
                "forgeflow_version": "0.1.0",
                "governance": {
                    "tasks_dir": custom_tasks_name,
                    "strict_mode": True,
                    "max_loop_budget": 5,
                    "auto_create_branch": False,
                },
                "paths": {
                    "in_progress": f"{custom_tasks_name}/in-progress",
                    "completed": f"{custom_tasks_name}/completed",
                },
            }
            config_data = copy.deepcopy(default_config)
            needs_write = False
            if not config_file.exists():
                needs_write = True
                created_files.append(".forgeflow.json")
            else:
                try:
                    existing = json.loads(config_file.read_text(encoding="utf-8"))
                    # Date-Based Amnesia: If not matching standard v0.1.0 or contains legacy fields, overwrite
                    if (
                        "required_documents" in existing.get("governance", {})
                        or "default_tier" in existing.get("governance", {})
                    ):
                        needs_write = True
                        updated_files.append(".forgeflow.json")
                    elif force:
                        # Deep merge defaults into existing, strictly preserving all user modifications
                        merged = cls.deep_merge_config(existing, default_config)
                        current_ver = existing.get("forgeflow_version", "0.1.0")
                        merged["forgeflow_version"] = current_ver
                        config_data = merged
                        if existing != merged:
                            needs_write = True
                            updated_files.append(".forgeflow.json")
                except Exception:
                    needs_write = True
                    updated_files.append(".forgeflow.json")

            if needs_write:
                config_file.write_text(json.dumps(config_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        # 3. .specify/memory/constitution.md
        specify_mem_dir = root / ".specify" / "memory"
        specify_mem_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(".specify/memory")

        constitution_file = specify_mem_dir / "constitution.md"
        constitution_content = (
            "# Project Constitution: Hybrid Governance Rules\n\n"
            "## 제1조 (무승인 구현 금지 - No Code Before Gate 1)\n"
            "어떠한 에이전트도 `tasks/in-progress/<id>/GATE1_REVIEW.md`의 공식 승인(APPROVED) 증적이 존재하지 않는 상태에서 "
            "`src/**` 경로에 신규 소스 코드를 생성하거나 기존 코드를 수정할 수 없다. `/speckit.implement`가 호출되더라도 "
            "이 원칙이 최우선하며, 위반 시 즉시 실행을 중단하고 사용자에게 보고해야 한다.\n\n"
            "## 제2조 (가짜 멈춤 금지 - No False Stopping)\n"
            "구현 중 발생하는 단순 단위 테스트 실패, 린트 오류, 사소한 컴파일 에러는 사용자에게 턴을 넘기거나 작업을 종료할 수 있는 사유가 아니다. "
            "에이전트는 결함 원인을 스스로 분석하고 코드를 수정하는 내부 자가 치유 루프(Loop 2)를 자율적으로 완주해야 한다.\n\n"
            "## 제3조 (원자적 루프 정의 - Atomic Remediation Unit)\n"
            "자가 치유의 1회 루프는 반드시 `결함 원인 식별 → 코드/테스트 1개 수정 → 테스트 재실행`의 "
            "전 과정을 포괄해야 한다. 코드를 수정하지 않고 테스트 명령어만 반복 실행하는 행위는 루프로 인정하지 않으며, "
            "모든 테스트가 통과된 최종 시점에만 원자적 구현 커밋 1개를 생성한다.\n\n"
            "## 제4조 (루프 예산 및 진짜 멈춤 - Loop Budget & True Stop)\n"
            "동일한 에러 핑거프린트로 5회 연속 코드 수정 및 테스트 통과에 실패한 경우에만 작업을 즉시 중지하고 사용자에게 에스컬레이션(진짜 멈춤)한다.\n\n"
            "## 제5조 (스펙 무단 하향 금지 - No Spec Downgrade)\n"
            "구현의 어려움을 이유로 사용자 승인 없이 `spec.md`의 요구사항이나 Acceptance Criteria를 축소·삭제·완화할 수 없다. "
            "스펙 수정이 필요한 경우 반드시 공식 스펙 회귀(Loop 3) 절차를 거쳐 Gate 1 재승인을 획득해야 한다.\n\n"
            "## 제6조 (기획 시 안티패턴 및 ADR 필수 준수 - Anti-Patterns & Architecture Decisions)\n"
            "에이전트는 과거에 합의된 설계 결정을 망각하고 동일한 실수를 반복해서는 안 된다. "
            "새 기능 기획 및 명세서 작성 착수 시(`speckit.specify` 단계) 반드시 `docs/spec/ANTI_PATTERNS.md`를 필독하여 "
            "금지된 안티패턴(Git SHA 결합, 스펙 해시 바인딩 등)을 확인하고, 주요 구조적 변경 시 `docs/adr/`의 아키텍처 결정 레코드를 검토해야 한다.\n\n"
            "## 프레임워크 공식 사양서 참조 경로 (Framework Specifications)\n"
            "에이전트는 세부 규범과 아키텍처 판단이 필요할 때 다음 공식 사양서(단일 진실 공급원)를 참조해야 한다:\n"
            "- 참조 인터페이스: `forgeflow doc list` 또는 `forgeflow doc show <spec-name>` CLI\n"
            "- 전역 템플릿 경로: `~/.local/forgeflow/current/lib/forgeflow/templates/spec/`\n"
            "- 7대 공식 사양서: FLOW_SPEC.md, GATES_AND_LOOPS.md, SPECKIT_HOOKS_AND_NORMS.md, "
            "DISTRIBUTION_SPEC.md, PHILOSOPHY_AND_COMPASS.md, REFACTORING_GUIDE.md, CHANGELOG.md\n"
            "- 안티패턴 및 ADR: docs/spec/ANTI_PATTERNS.md, docs/adr/\n"
        )
        if not constitution_file.exists() or force:
            constitution_file.write_text(constitution_content, encoding="utf-8")
            (updated_files if constitution_file.exists() and force else created_files).append(".specify/memory/constitution.md")

        # 4. .specify/extensions.yml
        specify_dir = root / ".specify"
        extensions_file = specify_dir / "extensions.yml"
        extensions_content = (
            'version: "1.0"\n'
            "hooks:\n"
            "  before_implement:\n"
            "    - extension: forgeflow-gatekeeper\n"
            "      command: forgeflow check --stage 2 --quiet\n"
            "      optional: false\n"
            '      prompt: "ForgeFlow Gate 1 승인 증적(GATE1_REVIEW.md)의 유효성을 검증한다. 미승인 시 즉시 중단한다."\n'
        )
        if not extensions_file.exists() or force:
            extensions_file.write_text(extensions_content, encoding="utf-8")
            (updated_files if extensions_file.exists() and force else created_files).append(".specify/extensions.yml")

        # 5. .specify/templates/commands/implement.md
        cmd_dir = specify_dir / "templates" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(".specify/templates/commands")

        implement_cmd_file = cmd_dir / "implement.md"
        implement_cmd_content = (
            "---\n"
            "description: Execute task implementation with Gate 1 enforcement and autonomous healing loop\n"
            "---\n\n"
            "## Pre-Execution Checks\n"
            "1. Gate 1 Approval: Verify `tasks/in-progress/<release-id>/GATE1_REVIEW.md` exists with status `APPROVED`.\n"
            "2. Workspace Isolation: Verify work is being conducted on branch `feat/<release-id>`.\n\n"
            "## Implementation Directives\n"
            "- Follow `tasks.md` sequentially in TDD fashion.\n"
            "- Inner Loop (Loop 2): Autonomously analyze, fix, and re-test without stopping on failures (budget: 5 attempts).\n"
            "- Checkpoint Commits: Create a clean git commit each time a discrete task (`- [ ] Task N.N`) and its tests 100% pass.\n"
            "- Rollback: If code becomes corrupted during remediation, revert to the last clean task checkpoint.\n"
        )
        if not implement_cmd_file.exists() or force:
            implement_cmd_file.write_text(implement_cmd_content, encoding="utf-8")
            (updated_files if implement_cmd_file.exists() and force else created_files).append(".specify/templates/commands/implement.md")

        # 6. Spec Kit bash scripts (6 scripts with 0o755 executable permissions)
        scripts_dir = specify_dir / "scripts" / "bash"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(".specify/scripts/bash")

        speckit_scripts = [
            "check-prerequisites.sh",
            "common.sh",
            "create-new-feature.sh",
            "resolve-template.sh",
            "setup-plan.sh",
            "setup-tasks.sh",
        ]
        for script_name in speckit_scripts:
            script_path = scripts_dir / script_name
            content = cls.get_template_content(f"speckit/scripts/bash/{script_name}")
            existed = script_path.exists()
            if not existed or force:
                script_path.write_text(content, encoding="utf-8")
                os.chmod(script_path, 0o755)
                (updated_files if existed else created_files).append(f".specify/scripts/bash/{script_name}")

        # 7. Spec Kit templates (4 templates)
        templates_dir = specify_dir / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        speckit_templates = [
            "spec-template.md",
            "plan-template.md",
            "tasks-template.md",
            "checklist-template.md",
        ]
        for tmpl_name in speckit_templates:
            tmpl_path = templates_dir / tmpl_name
            content = cls.get_template_content(f"speckit/templates/{tmpl_name}")
            existed = tmpl_path.exists()
            if not existed or force:
                tmpl_path.write_text(content, encoding="utf-8")
                (updated_files if existed else created_files).append(f".specify/templates/{tmpl_name}")

        # 8. Knowledge architecture (ANTI_PATTERNS.md & ADRs)
        spec_dir = root / "docs" / "spec"
        spec_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append("docs/spec")

        anti_patterns_file = spec_dir / "ANTI_PATTERNS.md"
        anti_patterns_content = cls.get_template_content("spec/ANTI_PATTERNS.md")
        existed = anti_patterns_file.exists()
        if not existed or force:
            anti_patterns_file.write_text(anti_patterns_content, encoding="utf-8")
            (updated_files if existed else created_files).append("docs/spec/ANTI_PATTERNS.md")

        adr_dir = root / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append("docs/adr")

        adr_templates = [
            "template.md",
            "001-eliminate-git-sha-and-commit-range-bindings.md",
            "002-remove-spec-body-hash-binding.md",
        ]
        for adr_name in adr_templates:
            adr_path = adr_dir / adr_name
            content = cls.get_template_content(f"adr/{adr_name}")
            existed = adr_path.exists()
            if not existed or force:
                adr_path.write_text(content, encoding="utf-8")
                (updated_files if existed else created_files).append(f"docs/adr/{adr_name}")

        # 9. .gitignore lock entries
        gitignore_file = root / ".gitignore"
        lock_entry = ".forgeflow/lifecycle/.*.lock\n"
        if gitignore_file.exists():
            existing_gi = gitignore_file.read_text(encoding="utf-8")
            if ".forgeflow/lifecycle/" not in existing_gi:
                gitignore_file.write_text(existing_gi.rstrip() + "\n" + lock_entry, encoding="utf-8")
                updated_files.append(".gitignore")
        else:
            gitignore_file.write_text(lock_entry, encoding="utf-8")
            created_files.append(".gitignore")

        # 10. Non-destructive Session Boot Anchor in root guides (AGENTS.md / CLAUDE.md)
        anchor_results = cls.bind_boot_anchor(root)
        for fname, action in anchor_results.items():
            if action == "created":
                created_files.append(fname)
            elif action == "updated":
                updated_files.append(fname)

        return {
            "status": "success",
            "created_dirs": sorted(list(set(created_dirs))),
            "created_files": created_files,
            "updated_files": updated_files,
        }

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
            if not target_file.is_file():
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
    def update_repo_governance(cls, root: Path) -> Dict[str, Any]:
        """Update local repository governance specifications and Spec Kit assets to the current version.

        Preserves all task packages in tasks/in-progress and tasks/completed while refreshing
        .specify/ scripts (with 0o755 permission), templates, and .forgeflow.json version.
        """
        from ._version import __version__
        root = root.resolve()
        config_file = root / ".forgeflow.json"
        if not config_file.exists() or not config_file.is_file():
            raise ValueError(f"Target directory '{root}' is not a valid ForgeFlow repository (.forgeflow.json missing).")

        try:
            config_data = json.loads(config_file.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse .forgeflow.json: {e}")

        previous_version = config_data.get("forgeflow_version", "unknown")

        tasks_dir_name = config_data.get("governance", {}).get("tasks_dir", "tasks")
        default_config = {
            "forgeflow_version": __version__,
            "governance": {
                "tasks_dir": tasks_dir_name,
                "strict_mode": True,
                "max_loop_budget": 5,
            },
            "paths": {
                "in_progress": f"{tasks_dir_name}/in-progress",
                "completed": f"{tasks_dir_name}/completed",
            },
        }

        # Deep merge default schema into existing config, strictly preserving any user-customized keys/values
        merged_config = cls.deep_merge_config(config_data, default_config)
        merged_config["forgeflow_version"] = __version__

        # Re-run hybrid scaffolding with force=True, skipping config write to prevent double-write / custom key loss
        scaffold_res = cls.scaffold_speckit_hybrid(root, force=True, skip_config=True)

        # Check if .forgeflow.json actually modified compared to original on-disk content
        is_config_changed = (merged_config != config_data)
        if is_config_changed:
            config_file.write_text(json.dumps(merged_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        updated_files = [f for f in scaffold_res.get("updated_files", []) if f != ".forgeflow.json"]
        if is_config_changed:
            updated_files.insert(0, ".forgeflow.json")

        changelog_summary = cls.extract_changelog_range(previous_version, __version__, changelog_file=cls.find_changelog_file(root))

        return {
            "status": "success",
            "previous_version": previous_version,
            "current_version": __version__,
            "target_dir": str(root),
            "updated_files": sorted(list(set(updated_files))),
            "changelog_summary": changelog_summary,
        }

    @classmethod
    def find_changelog_file(cls, root: Optional[Path] = None) -> Optional[Path]:
        """Locate CHANGELOG.md from installed package or source tree."""
        candidates = []
        if root:
            candidates.append(root / "docs" / "spec" / "CHANGELOG.md")
            candidates.append(root / "src" / "forgeflow" / "templates" / "spec" / "CHANGELOG.md")

        # 1. Directly packaged with current python module
        candidates.append(Path(__file__).parent / "templates" / "spec" / "CHANGELOG.md")

        # 2. Local workspace repository
        try:
            repo_root = HierarchicalRootScanner.find_root()
            candidates.append(repo_root / "docs" / "spec" / "CHANGELOG.md")
            candidates.append(repo_root / "src" / "forgeflow" / "templates" / "spec" / "CHANGELOG.md")
        except Exception:
            pass

        # 3. Global installed packages
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
    """Resolve auto_create_branch configuration from .forgeflow.json.

    Returns:
        bool: False by default if omitted or file missing.
              True or False if explicitly specified as a boolean.
    Raises:
        ValueError: If .forgeflow.json contains an invalid non-boolean auto_create_branch.
    """
    root = Path(repo_root).resolve()
    config_file = root / ".forgeflow.json"
    if not config_file.exists() or not config_file.is_file():
        return False

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse .forgeflow.json: {exc}") from exc

    if not isinstance(data, dict):
        return False

    gov = data.get("governance")
    if not isinstance(gov, dict):
        return False

    if "auto_create_branch" not in gov:
        return False

    val = gov["auto_create_branch"]
    if not isinstance(val, bool):
        raise ValueError(
            f"Invalid auto_create_branch in .forgeflow.json: expected boolean, got {type(val).__name__} ({val!r})"
        )

    return val


TemplateScaffolder.resolve_auto_create_branch = staticmethod(resolve_auto_create_branch)

