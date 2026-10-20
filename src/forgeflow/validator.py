"""
Document Integrity and Tier Governance Validator
"""

import ast
import re
import stat
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SelfGovernanceValidator:
    """Read-only validation for ForgeFlow's repository-local maintenance rules."""

    CORE_PREFIXES = (
        "src/forgeflow/", "tests/", "docs/spec/",
    )
    CORE_FILES = {"AGENTS.md", "README.md", "pyproject.toml", "install.sh"}
    NON_CORE_FILES = {"TODO.md"}
    SPEC_TARGETS = {
        "docs/spec/FLOW_SPEC.md", "docs/spec/GATES_AND_LOOPS.md", "docs/spec/CHANGELOG.md",
    }
    TABLE_HEADERS = (
        "Changed path", "Change classification", "Canonical spec path", "Coverage rationale",
    )
    VERSION_RELEASE_ID = "v0.4.4-version-governance"
    VERSION_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
    VERSION_FIELDS = (
        "Previous ForgeFlow version",
        "Target ForgeFlow version",
        "Version bump type",
        "Version change reason",
    )

    @classmethod
    def _classify_path(cls, path: str) -> Optional[str]:
        if path in cls.CORE_FILES or path.startswith(cls.CORE_PREFIXES):
            return "core"
        if path in cls.NON_CORE_FILES:
            return "repository-state"
        if path.startswith("docs/releases/") or path.startswith("tasks/") or path.startswith("ff-tasks/"):
            return "release-artifact"
        if path.startswith("docs/session-state/"):
            return "session-state"
        if path.startswith(".forgeflow/"):
            return "repository-state"
        return None

    @staticmethod
    def _name_status_paths(output: str) -> List[str]:
        """Return both sides of Git's NUL-delimited name-status records."""
        fields = output.split("\0")
        paths: List[str] = []
        index = 0
        while index < len(fields) and fields[index]:
            status = fields[index]
            index += 1
            if index >= len(fields):
                raise ValueError("malformed git name-status output")
            if status[:1] in {"R", "C"}:
                if index + 1 >= len(fields):
                    raise ValueError("malformed git rename/copy output")
                paths.extend((fields[index], fields[index + 1]))
                index += 2
            else:
                paths.append(fields[index])
                index += 1
        if any(fields[index:]):
            raise ValueError("malformed trailing git name-status output")
        return paths

    @classmethod
    def _coverage_rows(cls, content: str) -> List[Tuple[str, str]]:
        marker = "## Self-Governance Spec Coverage"
        if marker not in content:
            raise ValueError("DESIGN.md lacks Self-Governance Spec Coverage")
        section = content.split(marker, 1)[1]
        section = re.split(r"(?m)^##\s+", section, maxsplit=1)[0]
        lines = section.splitlines()
        start = next((i for i, line in enumerate(lines) if line.strip().startswith("|")), None)
        if start is None:
            raise ValueError("coverage table is missing")

        table_lines = []
        for line in lines[start:]:
            if not line.strip().startswith("|"):
                break
            table_lines.append(line)
        if len(table_lines) < 2:
            raise ValueError("coverage table lacks a header or separator")

        def cells(line: str) -> List[str]:
            stripped = line.strip()
            if not stripped.endswith("|"):
                raise ValueError("coverage table row is malformed")
            values = stripped.split("|")[1:-1]
            if len(values) != 4:
                raise ValueError("coverage table must have exactly four columns")
            return [value.strip().strip("`") for value in values]

        if tuple(cells(table_lines[0])) != cls.TABLE_HEADERS:
            raise ValueError("coverage table headers do not match the required schema")
        separator = cells(table_lines[1])
        if not all(re.fullmatch(r":?-{3,}:?", value) for value in separator):
            raise ValueError("coverage table separator is malformed")

        rows = []
        for line in table_lines[2:]:
            path, classification, spec, rationale = cells(line)
            if not path or not classification or not spec or not rationale:
                raise ValueError("coverage table contains an empty required field")
            rows.append((path, spec))
        return rows

    @staticmethod
    def _structured_field(content: str, label: str, filename: str) -> str:
        matches = re.findall(
            rf"(?m)^\s*-\s*\*\*{re.escape(label)}\*\*:\s*`([^`]+)`\s*$", content
        )
        if len(matches) != 1:
            raise ValueError(f"{filename} must contain exactly one structured {label} field")
        return matches[0]

    @classmethod
    def _parse_version_literal(cls, content: str, filename: str) -> str:
        """Read one static version assignment without importing repository code."""
        try:
            tree = ast.parse(content, filename=filename)
        except SyntaxError as exc:
            raise ValueError(f"invalid version source: {filename}") from exc
        values = []
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "__version__" for target in targets):
                value = node.value
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    raise ValueError(f"{filename} __version__ must be a string literal")
                values.append(value.value)
        if len(values) != 1:
            raise ValueError(f"{filename} must contain exactly one __version__ literal")
        if not cls.VERSION_PATTERN.fullmatch(values[0]):
            raise ValueError(f"{filename} version must use MAJOR.MINOR.PATCH without leading zeroes")
        return values[0]

    @classmethod
    def _base_version(cls, root: Path, base: str, release_id: str, changed_paths: set) -> str:
        def show(path: str) -> Optional[str]:
            result = subprocess.run(
                ["git", "show", f"{base}:{path}"], cwd=root, text=True, capture_output=True
            )
            if result.returncode == 0:
                return result.stdout
            if "does not exist" in result.stderr or "exists on disk" in result.stderr:
                return None
            raise ValueError(result.stderr.strip() or f"unable to read base version source: {path}")

        source = show("src/forgeflow/_version.py")
        if source is not None:
            return cls._parse_version_literal(source, "base:src/forgeflow/_version.py")
        if release_id != cls.VERSION_RELEASE_ID or "src/forgeflow/_version.py" not in changed_paths:
            raise ValueError("legacy base version fallback is not allowlisted for this release")
        legacy = show("src/forgeflow/__init__.py")
        if legacy is None:
            raise ValueError("base checkout lacks a canonical version source")
        return cls._parse_version_literal(legacy, "base:src/forgeflow/__init__.py")

    @classmethod
    def _validate_version_binding(
        cls, root: Path, release_id: str, base: str, changed_paths: set, prd_text: str, design_text: str
    ) -> None:
        version_path = root / "src/forgeflow/_version.py"
        try:
            version_mode = version_path.lstat().st_mode
        except FileNotFoundError:
            if "src/forgeflow/_version.py" in changed_paths:
                raise ValueError("canonical version source is missing")
            return
        if not stat.S_ISREG(version_mode):
            raise ValueError("canonical version source must be a regular file")
        current = cls._parse_version_literal(version_path.read_text(encoding="utf-8"), str(version_path))
        base_version = cls._base_version(root, base, release_id, changed_paths)
        documents = {"PRD.md": prd_text, "DESIGN.md": design_text}
        fields = {
            filename: {label: cls._structured_field(content, label, filename) for label in cls.VERSION_FIELDS}
            for filename, content in documents.items()
        }
        if fields["PRD.md"] != fields["DESIGN.md"]:
            raise ValueError("PRD.md and DESIGN.md version evidence does not match")
        evidence = fields["PRD.md"]
        if evidence["Previous ForgeFlow version"] != base_version:
            raise ValueError("Previous ForgeFlow version does not match the base commit")
        if evidence["Target ForgeFlow version"] != current:
            raise ValueError("Target ForgeFlow version does not match the canonical source")
        if not evidence["Version change reason"].strip():
            raise ValueError("Version change reason must not be empty")
        if not release_id.startswith(f"v{current}-"):
            raise ValueError("release ID must start with the target ForgeFlow version")
        previous_parts = tuple(map(int, base_version.split(".")))
        current_parts = tuple(map(int, current.split(".")))
        bump = evidence["Version bump type"]
        valid_bump = (
            bump == "major" and current_parts[0] > previous_parts[0]
            or bump == "minor" and current_parts[0] == previous_parts[0] and current_parts[1] > previous_parts[1]
            or bump == "patch" and current_parts[:2] == previous_parts[:2] and current_parts[2] > previous_parts[2]
        )
        if not valid_bump:
            raise ValueError("Version bump type does not match the version transition")
        pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
        if not re.search(r'(?m)^dynamic\s*=\s*\["version"\]\s*$', pyproject) or not re.search(
            r'(?m)^version\s*=\s*\{attr\s*=\s*"forgeflow\._version\.__version__"\}\s*$', pyproject
        ):
            raise ValueError("pyproject.toml must dynamically read forgeflow._version.__version__")
        for name in ("PRD.md", "DESIGN.md", "RELEASE_NOTES.md"):
            package_template = root / "src" / "forgeflow" / "templates" / name
            if not package_template.is_file():
                raise ValueError(f"required package template is missing: {name}")

    @classmethod
    def validate(cls, root: Path, release_id: str, base_ref: str) -> Tuple[bool, List[str]]:
        def git(*args: str) -> str:
            result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
            if result.returncode:
                raise ValueError(result.stderr.strip() or "git command failed")
            return result.stdout.strip()
        try:
            if not release_id or not base_ref:
                raise ValueError("--release-id and --base are required")
            if Path(release_id).name != release_id or release_id in {".", ".."}:
                raise ValueError("release-id must be a single path component")

            # Early bailout: check if release is already COMPLETE
            lifecycle_file = root / ".forgeflow" / "lifecycle" / f"{release_id}.json"
            is_completed = False
            if lifecycle_file.exists() and not lifecycle_file.is_symlink():
                try:
                    import json
                    data = json.loads(lifecycle_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        status = data.get("progress", {}).get("status") or data.get("status")
                        if status == "COMPLETE":
                            is_completed = True
                except Exception:
                    pass
            if not is_completed:
                from forgeflow.scanner import find_release_path
                release_dir = find_release_path(root, release_id) or (root / "docs" / "releases" / release_id)
                completion_report = release_dir / "COMPLETION_REPORT.md"
                release_signoff = release_dir / "RELEASE_SIGNOFF.md"
                if completion_report.exists() and release_signoff.exists():
                    try:
                        signoff_text = release_signoff.read_text(encoding="utf-8", errors="ignore")
                        if "Gate-3: APPROVED" in signoff_text and "User-Verdict: GO" in signoff_text:
                            is_completed = True
                    except Exception:
                        pass
            if is_completed:
                return True, [f"release '{release_id}' is already COMPLETE; skipping self-governance validation (early bailout)"]
            if git("status", "--porcelain"):
                raise ValueError("worktree must be clean")
            if git("rev-parse", "--is-shallow-repository") == "true":
                raise ValueError("shallow repository history is not accepted")
            base = git("rev-parse", "--verify", f"{base_ref}^{{commit}}")
            head = git("rev-parse", "HEAD")
            if base == head or subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=root).returncode:
                raise ValueError("base must be a strict ancestor of HEAD")
            branch = git("branch", "--show-current")
            branch_pattern = rf"^(?:feat|fix|docs|refactor|test|chore)/{re.escape(release_id)}$"
            if not re.fullmatch(branch_pattern, branch):
                raise ValueError("current task branch must be an allowlisted type/release-id branch")
            from forgeflow.scanner import find_release_path
            release_dir = find_release_path(root, release_id) or (root / "docs" / "releases" / release_id)
            design = release_dir / "DESIGN.md"
            prd = design.with_name("PRD.md")
            if not design.exists() or not prd.exists():
                raise ValueError("selected release package is incomplete")
            prd_text = prd.read_text(encoding="utf-8")
            design_text = design.read_text(encoding="utf-8")
            for filename, content in (("PRD.md", prd_text), ("DESIGN.md", design_text)):
                recorded_base = cls._structured_field(content, "Base commit", filename)
                recorded_branch = cls._structured_field(content, "Task branch", filename)
                if recorded_base != base:
                    raise ValueError(f"{filename} Base commit does not match the resolved full SHA")
                if recorded_branch != branch:
                    raise ValueError(f"{filename} Task branch does not match the current branch")
            name_status = git(
                "diff", "--name-status", "-z", "--find-renames", "--find-copies", f"{base}..{head}"
            )
            changed_paths = set(cls._name_status_paths(name_status))
            unknown = sorted(path for path in changed_paths if cls._classify_path(path) is None)
            if unknown:
                raise ValueError(f"unknown changed paths: {unknown}")
            core = {path for path in changed_paths if cls._classify_path(path) == "core"}
            if not core:
                return True, ["no ForgeFlow core paths changed; coverage is not required"]
            cls._validate_version_binding(root, release_id, base, changed_paths, prd_text, design_text)
            rows = cls._coverage_rows(design_text)
            row_paths = [path for path, _ in rows]
            duplicates = sorted(path for path, count in Counter(row_paths).items() if count > 1)
            unknown_rows = sorted(path for path in row_paths if path not in core)
            missing = sorted(core - set(row_paths))
            invalid = sorted(path for path, spec in rows if spec not in cls.SPEC_TARGETS)
            unchanged = sorted(spec for _, spec in rows if spec not in changed_paths)
            if duplicates or unknown_rows or missing or invalid or unchanged:
                raise ValueError(
                    "coverage failure: "
                    f"duplicates={duplicates}, unknown_rows={unknown_rows}, missing={missing}, "
                    f"invalid={invalid}, unchanged_specs={unchanged}"
                )
            for name in ("FLOW_SPEC.md", "GATES_AND_LOOPS.md", "CHANGELOG.md"):
                if (root / "docs/spec" / name).read_bytes() != (root / "src/forgeflow/templates/spec" / name).read_bytes():
                    raise ValueError(f"portable spec template differs: {name}")
            return True, [f"self-governance coverage passed against {base}"]
        except (OSError, ValueError) as exc:
            return False, [str(exc)]


@dataclass
class DocumentStatus:
    exists: bool = False
    passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ReleaseCheckResult:
    release_id: str
    path: str
    tier: Optional[int] = None
    passed: bool = False
    documents: Dict[str, Dict] = field(default_factory=dict)
    tests: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    archived: bool = False


class TierRules:
    """Defines requirements based on risk tier."""

    @staticmethod
    def get_tier_name(tier: Optional[int]) -> str:
        if tier == 1:
            return "Tier 1 (Minor / Fast-track)"
        elif tier == 2:
            return "Tier 2 (Standard / Default)"
        elif tier == 3:
            return "Tier 3 (Critical / Multi-party)"
        return "Tier 2 (Default)"

    @staticmethod
    def get_required_docs(tier: Optional[int], is_hybrid: bool = False, is_completed: bool = False) -> List[str]:
        if is_hybrid:
            if is_completed:
                return ["spec.md", "GATE1_REVIEW.md", "plan.md", "tasks.md", "QA_SIGNOFF.md", "RELEASE_SIGNOFF.md"]
            return ["spec.md", "GATE1_REVIEW.md", "plan.md", "tasks.md"]
        if tier == 1:
            return ["CHANGE_NOTE.md"]
        return ["PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md"]


class MarkdownSectionParser:
    """Parses markdown content for ForgeFlow compliance keywords and sections."""

    @staticmethod
    def extract_tier(content: str) -> Optional[int]:
        match = re.search(r"Tier\s*(?::\s*)?([123])", content, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def parse_prd(content: str) -> Dict[str, Any]:
        req_ids = re.findall(r"REQ-(?:F|NF)\d+", content)
        has_acceptance = bool(
            re.search(
                r"(?:인수\s*조건|Acceptance\s*Criteria|인수기준)", content, re.IGNORECASE
            )
        )
        has_reqs = len(req_ids) > 0
        passed = has_reqs and has_acceptance
        return {
            "passed": passed,
            "req_ids": sorted(list(set(req_ids))),
            "has_reqs": has_reqs,
            "has_requirements": has_reqs,
            "has_acceptance": has_acceptance,
            "has_acceptance_criteria": has_acceptance,
        }

    @staticmethod
    def parse_design(content: str) -> Dict[str, Any]:
        has_rtm = bool(
            re.search(
                r"(?:요구사항\s*추적|Requirements\s*Traceability|RTM)",
                content,
                re.IGNORECASE,
            )
        )
        has_architecture = bool(
            re.search(r"(?:아키텍처|컴포넌트|모듈|Component|Architecture)", content, re.IGNORECASE)
        )
        passed = has_rtm and has_architecture
        return {
            "passed": passed,
            "has_rtm": has_rtm,
            "has_architecture": has_architecture,
            "has_component": has_architecture,
        }

    @staticmethod
    def parse_qa_signoff(content: str) -> Dict[str, Any]:
        # Check approved status while ignoring explicit rejection
        is_approved = bool(
            re.search(r"(?:APPROVED|🟢\s*PASS|승인|통과|검증 완료)", content, re.IGNORECASE)
        ) and not bool(re.search(r"(?:Status:\s*REJECTED|판정:\s*REJECTED|최종\s*판정:\s*REJECTED)", content, re.IGNORECASE))
        
        has_test_summary = bool(
            re.search(r"(?:테스트|Test|테스트\s*실행|Passed|Pass)", content, re.IGNORECASE)
        )
        passed = is_approved
        return {
            "passed": passed,
            "is_approved": is_approved,
            "has_approved": is_approved,
            "has_test_summary": has_test_summary,
        }

    @staticmethod
    def parse_completion_report(content: str) -> Dict[str, Any]:
        has_summary = bool(
            re.search(r"(?:개요|성과|Summary|Overview|결과|작업)", content, re.IGNORECASE)
        )
        has_future_work = bool(
            re.search(
                r"(?:미완|개선|향후|남은|Future|Improvements|Limitations|Known\s*Issues)",
                content,
                re.IGNORECASE,
            )
        )
        passed = has_summary and has_future_work
        return {
            "passed": passed,
            "has_summary": has_summary,
            "has_future_work": has_future_work,
            "has_improvements": has_future_work,
        }

    @staticmethod
    def derive_mandatory_oidr_triggers(content: str) -> List[str]:
        """Derive mandatory OIDR trigger reasons from PRD facts, scope, and claims."""
        triggers: List[str] = []
        # Strip comments so template guidance doesn't trigger false positives
        clean_content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        # 1. Incident remediation/fix/recovery signals
        if re.search(r"(?i)\b(?:incident[\s\-_]fix|incident\s+remediation|hotfix|장애\s*복구|장애\s*해결|인시던트\s*(?:해결|대응|수정)|결함\s*수정)\b", clean_content):
            triggers.append("incident-fix")

        # 2. Public surface change signals (CLI commands, public APIs, wrappers, entrypoints)
        if re.search(r"(?i)\b(?:public[\s\-_]surface[\s\-_]change|공용\s*표면\s*변경|공용\s*엔트리포인트|public\s*cli|public\s*entrypoint|public\s*surface)\b", clean_content):
            triggers.append("public-surface-change")

        # 3. Operational claim signals
        if re.search(r"(?i)\b(?:operational[\s\-_]claim|운영\s*해결\s*클레임|운영\s*해결\s*선언|operational\s+resolution)\b", clean_content):
            triggers.append("operational-claim")

        return triggers

    @staticmethod
    def parse_oidr_prd(content: str) -> Dict[str, Any]:
        """Parse and validate conditional OIDR fields in PRD.md."""
        track_match = re.search(r"(?m)^\s*-\s*\*\*OIDR Track\*\*:\s*`?([a-zA-Z0-9_\-]+)`?", content)
        track_val = track_match.group(1).lower() if track_match else "none"
        is_active = (track_val == "active")

        result: Dict[str, Any] = {
            "is_active": is_active,
            "track": track_val,
            "trigger_reason": None,
            "verdict": None,
            "external_claim": None,
            "has_brief": False,
            "fixture_count": 0,
            "fixtures": [],
            "errors": [],
        }

        # Check for mandatory trigger derivation bypass
        mandatory_triggers = MarkdownSectionParser.derive_mandatory_oidr_triggers(content)
        if mandatory_triggers and not is_active:
            result["errors"].append(
                f"릴리즈 스코프 또는 팩트에 OIDR 트리거 조건({', '.join(mandatory_triggers)})이 감지되었으나 "
                f"'OIDR Track'이 '{track_val}'(으)로 선언되었습니다. OIDR Track을 active로 설정해야 합니다."
            )

        if not is_active:
            return result

        # 1. Trigger Reason
        trigger_match = re.search(r"(?m)^\s*-\s*\*\*Trigger Reason\*\*:\s*`?([a-zA-Z0-9_\-/]+)`?", content)
        trigger_val = trigger_match.group(1).lower() if trigger_match else None
        result["trigger_reason"] = trigger_val
        valid_triggers = {"incident-fix", "public-surface-change", "operational-claim"}
        if not trigger_val or trigger_val in {"n/a", "none"} or trigger_val not in valid_triggers:
            result["errors"].append("OIDR Track이 active이지만 Trigger Reason이 명시되지 않았습니다 (incident-fix | public-surface-change | operational-claim).")

        # 2. Applicability Verdict
        verdict_match = re.search(r"(?m)^\s*-\s*\*\*Applicability Verdict\*\*:\s*`?([a-zA-Z0-9_\-/]+)`?", content)
        verdict_val = verdict_match.group(1).lower() if verdict_match else None
        result["verdict"] = verdict_val
        valid_verdicts = {"supported", "explicitly-excluded", "discovery-only"}
        if verdict_val not in valid_verdicts:
            result["errors"].append(f"유효하지 않은 Applicability Verdict: '{verdict_val}' (supported | explicitly-excluded | discovery-only 중 하나여야 함)")

        # 3. Incident Brief fields
        has_failure_class = bool(re.search(r"(?m)^\s*-\s*Observed Failure Class\s*:\s*(.+)$", content))
        has_safety_boundary = bool(re.search(r"(?m)^\s*-\s*Safety Boundary\s*:\s*(.+)$", content))
        has_oracles = bool(re.search(r"(?m)^\s*-\s*Success & Failure Oracles\s*:\s*(.+)$", content))
        result["has_brief"] = has_failure_class and has_safety_boundary and has_oracles

        if not has_failure_class:
            result["errors"].append("Incident Brief에 'Observed Failure Class'가 누락되었습니다.")
        if not has_safety_boundary:
            result["errors"].append("Incident Brief에 'Safety Boundary'가 누락되었습니다.")
        if not has_oracles:
            result["errors"].append("Incident Brief에 'Success & Failure Oracles'가 누락되었습니다.")

        # 4. Structured Incident-to-Fixture Mapping:
        # Expected 4-part format: PROP-<ID> -> FIXTURE-<ID> -> ORACLE-<ID> -> REQ-<ID>
        mapping_section = re.search(r"(?s)Incident-to-Fixture Mapping:(.*?)(?:\n##|\Z)", content)
        fixture_count = 0
        fixtures = []
        prop_ids = set()
        fixture_ids = set()

        if mapping_section:
            lines = [l.strip() for l in mapping_section.group(1).splitlines() if l.strip().startswith("-")]
            for l in lines:
                raw_line = l.lstrip("-").strip()
                if not raw_line or raw_line.lower() in {"n/a", "none"}:
                    continue
                if "{{" in raw_line or "}}" in raw_line or "n/a" in raw_line.lower():
                    result["errors"].append(f"Incident-to-Fixture Mapping에 플레이스홀더가 포함되어 있습니다: '{raw_line}'")
                    continue

                # Parse 4-part structure separated by ->, ➔, or →
                parts = [p.strip() for p in re.split(r"\s*(?:->|➔|→)\s*", raw_line) if p.strip()]
                if len(parts) == 4:
                    prop_id, fix_id, oracle_id, req_id = parts
                    if prop_id in prop_ids:
                        result["errors"].append(f"중복된 Incident Property ID가 감지되었습니다: '{prop_id}'")
                    if fix_id in fixture_ids:
                        result["errors"].append(f"중복된 Fixture ID가 감지되었습니다: '{fix_id}'")
                    prop_ids.add(prop_id)
                    fixture_ids.add(fix_id)
                    fixtures.append({
                        "property_id": prop_id,
                        "fixture_id": fix_id,
                        "oracle_id": oracle_id,
                        "req_id": req_id
                    })
                    fixture_count += 1
                else:
                    if verdict_val == "supported":
                        result["errors"].append(
                            f"Incident-to-Fixture Mapping 행 '{raw_line}'이 4단 정형 구조(PROP-ID -> FIXTURE-ID -> ORACLE-ID -> REQ-ID)를 충족하지 않습니다."
                        )

        result["fixture_count"] = fixture_count
        result["fixtures"] = fixtures

        if verdict_val == "supported" and fixture_count == 0:
            result["errors"].append("Applicability Verdict가 'supported'이지만 유효한 'Incident-to-Fixture Mapping' 픽스처가 정의되지 않았습니다.")

        # 5. External Claim Scope
        claim_match = re.search(r"(?m)^\s*-\s*\*\*External Claim Scope\*\*:\s*(.+)$", content)
        claim_text = claim_match.group(1).strip() if claim_match else ""
        result["external_claim"] = claim_text
        if verdict_val in {"explicitly-excluded", "discovery-only"}:
            if re.search(r"(?i)\b(?:resolved|해결|remediated|완전\s*해결)\b", claim_text):
                result["errors"].append(f"Applicability Verdict가 '{verdict_val}'이지만 External Claim Scope에 인시던트 해결(resolved)을 주장하고 있습니다.")

        # 6. Sanitization check (Secrets / Sensitive tokens)
        if re.search(r"(?i)(?:bearer\s+[a-z0-9_\-\.]{20,}|ghp_[a-z0-9]{20,}|password\s*[:=]\s*['\"][^'\"]{4,}['\"])", content):
            result["errors"].append("인시던트 기술 내용에 원시 비밀번호나 인증 토큰 등 민감 정보가 감지되었습니다. 정제(Sanitization)가 필요합니다.")

        return result

    @staticmethod
    def parse_oidr_qa(content: str, prd_content: Optional[str] = None) -> Dict[str, Any]:
        """Parse and validate conditional Consumer Delivery Readiness fields in QA_SIGNOFF.md."""
        surface_match = re.search(r"(?m)^\s*-\s*\*\*Consumer Surface Declared\*\*:\s*`?([a-zA-Z0-9_\-]+)`?", content)
        surface_val = surface_match.group(1).lower() if surface_match else "no"
        is_declared = (surface_val == "yes")

        result: Dict[str, Any] = {
            "is_declared": is_declared,
            "surface": surface_val,
            "delivery_target": None,
            "artifact_identity": None,
            "artifact_digest": None,
            "entrypoint": None,
            "clean_install_verified": False,
            "probe_exit_code": None,
            "active_target_verification": None,
            "waiver_rationale": None,
            "errors": [],
        }

        # Check trigger bypass: If PRD declared public-surface-change, consumer surface must be declared yes
        if prd_content:
            prd_oidr = MarkdownSectionParser.parse_oidr_prd(prd_content)
            if prd_oidr["is_active"] and prd_oidr["trigger_reason"] == "public-surface-change":
                if surface_val != "yes":
                    result["errors"].append(
                        "PRD에서 'public-surface-change' 트리거가 활성화되었으나 QA_SIGNOFF에서 "
                        "'Consumer Surface Declared'가 yes가 아닙니다. 소비자 전달 검증이 필수입니다."
                    )

        if not is_declared:
            return result

        # 1. Delivery Target & Expected Entrypoint
        target_match = re.search(r"(?m)^\s*-\s*\*\*Delivery Target\*\*:\s*`?([^`\n]+)`?", content)
        target_val = target_match.group(1).strip() if target_match else ""
        result["delivery_target"] = target_val
        if not target_val or target_val.lower() in {"n/a", "none"}:
            result["errors"].append("소비자 표면이 선언되었으나 'Delivery Target'이 명시되지 않았습니다.")

        entry_match = re.search(r"(?m)^\s*-\s*\*\*Expected Public Entrypoint\*\*:\s*`?([^`\n]+)`?", content)
        entry_val = entry_match.group(1).strip() if entry_match else ""
        result["entrypoint"] = entry_val
        if not entry_val or entry_val.lower() in {"n/a", "none"}:
            result["errors"].append("소비자 표면이 선언되었으나 'Expected Public Entrypoint'가 명시되지 않았습니다.")

        # 2. Candidate Artifact Identity & Digest Binding
        art_match = re.search(r"(?m)^\s*-\s*\*\*Artifact Identity\*\*:\s*`?([^`\n]+)`?", content)
        art_val = art_match.group(1).strip() if art_match else ""
        result["artifact_identity"] = art_val
        if not art_val or art_val.lower() in {"n/a", "none"}:
            result["errors"].append("소비자 표면이 선언되었으나 'Artifact Identity'가 명시되지 않았습니다.")

        digest_match = re.search(r"(?m)^\s*-\s*\*\*Artifact SHA-256 Digest\*\*:\s*`?([0-9a-fA-F]{64})`?", content)
        digest_val = digest_match.group(1).strip() if digest_match else ""
        result["artifact_digest"] = digest_val
        if not digest_val:
            result["errors"].append("소비자 표면이 선언되었으나 유효한 'Artifact SHA-256 Digest'(64자리 16진수)가 명시되지 않았습니다.")

        # 3. Clean Consumer Install Verified
        clean_match = re.search(r"(?m)^\s*-\s*\*\*Clean Consumer Install Verified\*\*:\s*`?([a-zA-Z0-9_\-]+)`?", content)
        clean_val = clean_match.group(1).lower() if clean_match else "no"
        result["clean_install_verified"] = (clean_val == "yes")
        if clean_val != "yes":
            result["errors"].append("소비자 표면(Consumer Surface)이 선언되었으나 'Clean Consumer Install Verified'가 yes가 아닙니다.")

        # 4. Non-Mutating Probe & Source-Checkout Leakage Protection
        probe_cmd = re.search(r"(?m)^\s*-\s*Probe Command\s*:\s*`?([^`\n]+)`?", content)
        probe_exit = re.search(r"(?m)^\s*-\s*Exit Code\s*:\s*(\d+)", content)
        probe_result = re.search(r"(?m)^\s*-\s*Observable Result\s*:\s*(.+)$", content)

        if not probe_cmd or not probe_result:
            result["errors"].append("Consumer Delivery Readiness에 비파괴 프로브(Probe Command 및 Observable Result)가 누락되었습니다.")
        else:
            cmd_text = probe_cmd.group(1).strip()
            # Check source-checkout leakage (e.g. executing directly from src/ or python -m against checkout)
            if re.search(r"(?:src/forgeflow|python3?\s+-m\s+forgeflow|\.py\b)", cmd_text) and "entrypoint" not in cmd_text:
                result["errors"].append(f"비파괴 프로브 커맨드('{cmd_text}')가 소스 체크아웃(src/) 또는 직접 모듈 호출을 참조하고 있습니다. 격리 설치된 소비자 엔트리포인트를 사용해야 합니다.")

        if probe_exit:
            exit_code = int(probe_exit.group(1))
            result["probe_exit_code"] = exit_code
            if exit_code != 0:
                result["errors"].append(f"비파괴 프로브 종료 코드(Exit Code)가 0이 아닙니다: {exit_code}")
        else:
            result["errors"].append("비파괴 프로브 Exit Code가 명시되지 않았습니다.")

        # 5. Active Target Verification
        target_match = re.search(r"(?m)^\s*-\s*\*\*Active Target Verification\*\*:\s*`?([a-zA-Z0-9_\-]+)`?", content)
        target_val = target_match.group(1).lower() if target_match else "none"
        result["active_target_verification"] = target_val

        if target_val not in {"verified", "waived"}:
            result["errors"].append(f"유효하지 않은 Active Target Verification: '{target_val}' (verified 또는 waived여야 함)")
        elif target_val == "waived":
            waiver_match = re.search(r"(?m)^\s*-\s*\*\*Waiver Rationale\*\*:\s*(.+)$", content)
            waiver_text = waiver_match.group(1).strip() if waiver_match else ""
            result["waiver_rationale"] = waiver_text
            if not waiver_text or "delivery ready; active target unverified" not in waiver_text.lower():
                result["errors"].append("Active Target Verification이 waived인 경우 Waiver Rationale에 'delivery ready; active target unverified' 문구가 포함되어야 합니다.")

        return result


class DocumentIntegrityValidator:
    """Validates physical presence and content integrity of release markdown documents."""

    def __init__(self, release_path: Path):
        self.release_path = Path(release_path)

    def validate(self) -> ReleaseCheckResult:
        rel_id = self.release_path.name
        res = ReleaseCheckResult(release_id=rel_id, path=str(self.release_path))

        spec_file = self.release_path / "spec.md"
        gate1_file = self.release_path / "GATE1_REVIEW.md"
        prd_file = self.release_path / "PRD.md"
        change_note_file = self.release_path / "CHANGE_NOTE.md"
        is_hybrid = spec_file.exists() or gate1_file.exists() or (self.release_path.parent.parent / ".specify").is_dir()
        is_completed = "completed" in str(self.release_path)

        if is_hybrid:
            if spec_file.exists():
                try:
                    res.tier = MarkdownSectionParser.extract_tier(spec_file.read_text(encoding="utf-8"))
                except Exception:
                    res.tier = None
            if not res.tier and gate1_file.exists():
                try:
                    res.tier = MarkdownSectionParser.extract_tier(gate1_file.read_text(encoding="utf-8"))
                except Exception:
                    res.tier = None
            if not res.tier:
                res.tier = 2

            if is_completed:
                doc_map = {
                    "spec": "spec.md",
                    "gate1_review": "GATE1_REVIEW.md",
                    "plan": "plan.md",
                    "tasks": "tasks.md",
                    "qa_signoff": "QA_SIGNOFF.md",
                    "release_signoff": "RELEASE_SIGNOFF.md",
                }
            else:
                doc_map = {
                    "spec": "spec.md",
                    "gate1_review": "GATE1_REVIEW.md",
                    "plan": "plan.md",
                    "tasks": "tasks.md",
                }
                if (self.release_path / "QA_SIGNOFF.md").exists():
                    doc_map["qa_signoff"] = "QA_SIGNOFF.md"
                if (self.release_path / "RELEASE_SIGNOFF.md").exists():
                    doc_map["release_signoff"] = "RELEASE_SIGNOFF.md"
        elif prd_file.exists():
            try:
                res.tier = MarkdownSectionParser.extract_tier(prd_file.read_text(encoding="utf-8"))
            except Exception:
                res.tier = 2
            doc_map = {
                "prd": "PRD.md",
                "design": "DESIGN.md",
                "qa_signoff": "QA_SIGNOFF.md",
                "completion_report": "COMPLETION_REPORT.md",
            }
        elif change_note_file.exists():
            try:
                res.tier = MarkdownSectionParser.extract_tier(change_note_file.read_text(encoding="utf-8")) or 1
            except Exception:
                res.tier = 1
            doc_map = {"change_note": "CHANGE_NOTE.md"} if res.tier == 1 else {
                "prd": "PRD.md",
                "design": "DESIGN.md",
                "qa_signoff": "QA_SIGNOFF.md",
                "completion_report": "COMPLETION_REPORT.md",
            }
        else:
            res.tier = 2
            doc_map = {
                "prd": "PRD.md",
                "design": "DESIGN.md",
                "qa_signoff": "QA_SIGNOFF.md",
                "completion_report": "COMPLETION_REPORT.md",
            }

        all_ok = True
        for key, fname in doc_map.items():
            stat = self.validate_file(fname)
            doc_dict = {
                "exists": stat.exists,
                "passed": stat.passed,
                "details": stat.details,
            }
            res.documents[key] = doc_dict
            res.documents[fname] = doc_dict
            if not stat.passed:
                all_ok = False
            if stat.errors:
                res.errors.extend(stat.errors)
            if stat.warnings:
                res.warnings.extend(stat.warnings)

        res.passed = all_ok
        return res

    def validate_file(self, filename: str) -> DocumentStatus:
        file_path = self.release_path / filename
        status = DocumentStatus()

        if not file_path.exists():
            status.exists = False
            status.passed = False
            status.errors.append(f"필수 문서 누락: {filename}")
            return status

        status.exists = True
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            status.passed = False
            status.errors.append(f"파일 읽기 실패 ({filename}): {e}")
            return status

        if filename == "spec.md":
            has_acceptance = "acceptance" in content.lower() or "인수 조건" in content
            status.passed = has_acceptance and len(content.strip().splitlines()) >= 10
            status.details = {"has_acceptance": has_acceptance, "lines": len(content.strip().splitlines())}
            if not has_acceptance:
                status.errors.append("spec.md에 인수 조건(Acceptance Criteria) 섹션이 누락되었습니다.")

        elif filename == "GATE1_REVIEW.md":
            has_approved = "APPROVED" in content.upper()
            has_sha = "spec sha" in content.lower() or "spec_sha" in content.lower()
            status.passed = has_approved and has_sha
            status.details = {"has_approved": has_approved, "has_sha": has_sha}
            if not has_approved:
                status.errors.append("GATE1_REVIEW.md에 APPROVED 승인 명시가 없습니다.")
            if not has_sha:
                status.errors.append("GATE1_REVIEW.md에 Spec SHA256 불변 바인딩이 누락되었습니다.")

        elif filename == "plan.md":
            has_arch = "architecture" in content.lower() or "아키텍처" in content or "설계" in content
            status.passed = has_arch and len(content.strip().splitlines()) >= 10
            status.details = {"has_architecture": has_arch, "lines": len(content.strip().splitlines())}
            if not has_arch:
                status.errors.append("plan.md에 아키텍처 또는 기술 설계 섹션이 누락되었습니다.")

        elif filename == "tasks.md":
            has_tasks = "- [" in content
            status.passed = has_tasks and len(content.strip().splitlines()) >= 5
            status.details = {"has_tasks": has_tasks, "lines": len(content.strip().splitlines())}
            if not has_tasks:
                status.errors.append("tasks.md에 체크리스트 작업 목록(- [ ])이 누락되었습니다.")

        elif filename == "RELEASE_SIGNOFF.md":
            has_signoff = "APPROVED" in content.upper() or "sign-off" in content.lower() or "승인" in content
            status.passed = has_signoff and len(content.strip().splitlines()) >= 5
            status.details = {"has_signoff": has_signoff, "lines": len(content.strip().splitlines())}
            if not has_signoff:
                status.errors.append("RELEASE_SIGNOFF.md에 릴리즈 승인(Sign-Off) 증적이 누락되었습니다.")

        elif filename == "PRD.md":
            res = MarkdownSectionParser.parse_prd(content)
            status.details = res
            status.passed = res["passed"]
            if not res["req_ids"]:
                status.errors.append("PRD.md에 요구사항 ID (REQ-Fxx / REQ-NFxx)가 정의되지 않았습니다.")
            if not res["has_acceptance"]:
                status.errors.append("PRD.md에 인수 조건(Acceptance Criteria) 섹션이 누락되었습니다.")
            oidr_res = MarkdownSectionParser.parse_oidr_prd(content)
            status.details["oidr"] = oidr_res
            if oidr_res["errors"]:
                status.passed = False
                status.errors.extend(oidr_res["errors"])

        elif filename == "DESIGN.md":
            res = MarkdownSectionParser.parse_design(content)
            status.details = res
            status.passed = res["passed"]
            if not res["has_rtm"]:
                status.errors.append("DESIGN.md에 요구사항 추적 매트릭스(RTM)가 누락되었습니다.")
            if not res["has_architecture"]:
                status.errors.append("DESIGN.md에 아키텍처 또는 컴포넌트 설계 섹션이 누락되었습니다.")

        elif filename == "QA_SIGNOFF.md":
            res = MarkdownSectionParser.parse_qa_signoff(content)
            status.details = res
            status.passed = res["passed"]
            if not res["has_approved"]:
                status.errors.append("QA_SIGNOFF.md에 최종 승인(APPROVED/PASS) 명시가 없습니다.")
            prd_file = self.release_path / "PRD.md"
            prd_content = prd_file.read_text(encoding="utf-8") if prd_file.exists() else None
            oidr_qa_res = MarkdownSectionParser.parse_oidr_qa(content, prd_content=prd_content)
            status.details["oidr"] = oidr_qa_res
            if oidr_qa_res["errors"]:
                status.passed = False
                status.errors.extend(oidr_qa_res["errors"])

        elif filename == "COMPLETION_REPORT.md":
            res = MarkdownSectionParser.parse_completion_report(content)
            status.details = res
            status.passed = res["passed"]
            if not res["has_summary"]:
                status.errors.append("COMPLETION_REPORT.md에 성과 요약 섹션이 누락되었습니다.")
            if not res["has_future_work"]:
                status.errors.append("COMPLETION_REPORT.md에 '미완 또는 향후 개선 필요 사항' 섹션이 누락되었습니다.")

        elif filename == "CHANGE_NOTE.md":
            content_lower = content.lower()
            status.passed = len(content.strip().splitlines()) >= 5 and ("gate 1" in content_lower or "pass" in content_lower)
            if not status.passed:
                status.errors.append("CHANGE_NOTE.md 내용이 불완전하거나 승인 증적이 누락되었습니다.")

        else:
            status.passed = len(content.strip()) > 0

        return status
