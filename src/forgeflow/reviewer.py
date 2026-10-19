"""
Reviewer Engine Orchestration (Zero-Dependency)
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .review_cache import ReviewCacheManager
from .review_scanner import ReviewScanner
from .scanner import HierarchicalRootScanner, ReleaseScanner
from .smell_detector import CodeSmell, SmellDetector


@dataclass
class ReviewResult:
    repo_root: str
    target_scope: str
    files_scanned: List[str]
    smells: List[CodeSmell]
    spec_source: Optional[str]
    standards_sources: List[str]
    standards_prompt: str
    spec_prompt: str
    report_path: Optional[str]
    passed: bool
    strict: bool
    cache_stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "target_scope": self.target_scope,
            "files_scanned": self.files_scanned,
            "smells": [s.to_dict() for s in self.smells],
            "spec_source": self.spec_source,
            "standards_sources": self.standards_sources,
            "standards_prompt": self.standards_prompt,
            "spec_prompt": self.spec_prompt,
            "report_path": self.report_path,
            "passed": self.passed,
            "strict": self.strict,
            "cache_stats": self.cache_stats or {"enabled": False, "hits": 0, "misses": 0},
            "summary": {
                "total_files": len(self.files_scanned),
                "total_smells": len(self.smells),
                "critical": sum(1 for s in self.smells if s.severity == "CRITICAL"),
                "warning": sum(1 for s in self.smells if s.severity == "WARNING"),
                "info": sum(1 for s in self.smells if s.severity == "INFO"),
            },
        }

    def to_remediations(self) -> List[Dict[str, Any]]:
        """Converts detected smells into structured remediation records."""
        remediations: List[Dict[str, Any]] = []
        for i, smell in enumerate(self.smells, 1):
            remediations.append({
                "id": f"REM-{i:03d}",
                "file": smell.file_path,
                "line": smell.line_no,
                "rule_id": smell.smell_type,
                "severity": smell.severity,
                "description": smell.message,
                "status": "OPEN",
            })
        return remediations


class ReviewEngine:
    """Orchestrates static AST smell analysis, incremental caching, and Fail-Closed review gates."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = (repo_root or HierarchicalRootScanner.find_root()).resolve()

    def run_review(
        self,
        targets: Optional[List[Path]] = None,
        all_files: bool = False,
        base_ref: Optional[str] = None,
        explicit_spec: Optional[str] = None,
        strict: bool = False,
        fail_on_warning: bool = False,
        no_cache: bool = False,
        report_dest: Optional[Path] = None,
    ) -> ReviewResult:
        if targets:
            files_to_scan = [t.resolve() for t in targets if t.exists() and t.is_file()]
            scope_desc = f"Explicit ({len(files_to_scan)} files)"
        elif all_files:
            files_to_scan = ReviewScanner.get_all_source_files(self.repo_root)
            scope_desc = f"All Source Files ({len(files_to_scan)} files)"
        else:
            diff_files = ReviewScanner.get_diff_files(self.repo_root, base_ref=base_ref)
            files_to_scan = [f for f in diff_files if f.suffix == ".py"]
            if not files_to_scan:
                scope_desc = "Clean Working Tree (0 changed files)"
            else:
                scope_desc = f"Git Diff ({len(files_to_scan)} files)"

        cache_mgr = ReviewCacheManager(repo_root=self.repo_root, enabled=not no_cache)
        all_smells: List[CodeSmell] = []

        for file_p in files_to_scan:
            if file_p.suffix == ".py":
                try:
                    content = file_p.read_text(encoding="utf-8")
                except UnicodeDecodeError as exc:
                    all_smells.append(
                        CodeSmell(
                            file_path=str(file_p),
                            line_no=1,
                            smell_type="Encoding Error",
                            severity="CRITICAL",
                            message=f"파일 인코딩 오류(UTF-8 디코딩 실패): {exc}",
                            suggestion="파일을 유효한 UTF-8 인코딩으로 저장하세요.",
                        )
                    )
                    continue
                except Exception as e:
                    all_smells.append(
                        CodeSmell(
                            file_path=str(file_p),
                            line_no=1,
                            smell_type="Read Error",
                            severity="CRITICAL",
                            message=f"파일 읽기 실패: {str(e)}",
                            suggestion="파일 권한 및 경로를 확인하세요.",
                        )
                    )
                    continue

                cached = cache_mgr.get(file_p, content)
                if cached is not None:
                    all_smells.extend(cached)
                else:
                    file_smells = SmellDetector.analyze_code(content, file_path=str(file_p))
                    cache_mgr.put(file_p, content, file_smells)
                    all_smells.extend(file_smells)

        cache_mgr.save()
        cache_stats = cache_mgr.get_stats()

        spec_path = ReviewScanner.find_spec_source(self.repo_root, explicit_spec=explicit_spec)
        standards_paths = ReviewScanner.find_standards_sources(self.repo_root)

        spec_content = (
            spec_path.read_text(encoding="utf-8")
            if spec_path and spec_path.exists()
            else "No spec available"
        )
        standards_names = [p.name for p in standards_paths]

        standards_prompt = self._build_standards_prompt(files_to_scan, standards_names, all_smells)
        spec_prompt = self._build_spec_prompt(files_to_scan, spec_path, spec_content)

        # Fail-Closed review validation
        effective_critical = 0
        for s in all_smells:
            if s.severity == "CRITICAL":
                if s.smell_type == "File Bloat":
                    fname = Path(s.file_path).name
                    has_exception = (
                        ("Architecture Exception" in spec_content or "모듈 비대화 예외" in spec_content or "LOC Exception" in spec_content)
                        and fname in spec_content
                    )
                    if not has_exception:
                        effective_critical += 1
                else:
                    effective_critical += 1

        warning_count = sum(1 for s in all_smells if s.severity == "WARNING")

        if strict or fail_on_warning:
            passed = effective_critical == 0 and warning_count == 0
        else:
            passed = effective_critical == 0

        saved_report_path = self._save_markdown_report(
            scope_desc=scope_desc,
            files_scanned=files_to_scan,
            smells=all_smells,
            spec_path=spec_path,
            standards_paths=standards_paths,
            passed=passed,
            strict=strict or fail_on_warning,
            cache_stats=cache_stats,
            custom_dest=report_dest,
        )

        return ReviewResult(
            repo_root=str(self.repo_root),
            target_scope=scope_desc,
            files_scanned=[str(p.relative_to(self.repo_root)) for p in files_to_scan],
            smells=all_smells,
            spec_source=str(spec_path.relative_to(self.repo_root)) if spec_path else None,
            standards_sources=[str(p.relative_to(self.repo_root)) for p in standards_paths],
            standards_prompt=standards_prompt,
            spec_prompt=spec_prompt,
            report_path=str(saved_report_path.relative_to(self.repo_root)) if saved_report_path else None,
            passed=passed,
            strict=strict or fail_on_warning,
            cache_stats=cache_stats,
        )

    def _build_standards_prompt(
        self, files: List[Path], standards: List[str], smells: List[CodeSmell]
    ) -> str:
        files_str = "\n".join(f"- {f.relative_to(self.repo_root)}" for f in files)
        smells_str = "\n".join(
            f"- [{s.severity}] {Path(s.file_path).name}:{s.line_no} ({s.smell_type}): {s.message}"
            for s in smells[:15]
        ) or "- No static code smells detected by AST analyzer."
        standards_joined = ", ".join(standards) if standards else "Repo Default Baseline"
        return f"## Standards Axis Review\nTarget Files:\n{files_str}\n\nReferenced Standards: {standards_joined}\n\nDetected AST Smells & Metrics:\n{smells_str}\n\nPrompt Brief:\nReport (a) every place the code violates documented standards, and (b) architectural Fowler code smells (Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest). Under 400 words.\n"

    def _build_spec_prompt(
        self, files: List[Path], spec_path: Optional[Path], spec_content: str
    ) -> str:
        files_str = "\n".join(f"- {f.relative_to(self.repo_root)}" for f in files)
        spec_name = str(spec_path.relative_to(self.repo_root)) if spec_path else "None"
        truncated_spec = spec_content[:2000]
        return f"## Spec Axis Review\nTarget Files:\n{files_str}\n\nSpec Source: {spec_name}\nSpec Excerpt:\n\"\"\"\n{truncated_spec}\n\"\"\"\n\nPrompt Brief:\nReport: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the code that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words.\n"

    def _save_markdown_report(
        self,
        scope_desc: str,
        files_scanned: List[Path],
        smells: List[CodeSmell],
        spec_path: Optional[Path],
        standards_paths: List[Path],
        passed: bool,
        strict: bool,
        cache_stats: Optional[Dict[str, Any]] = None,
        custom_dest: Optional[Path] = None,
    ) -> Optional[Path]:
        try:
            if custom_dest:
                dest = (
                    custom_dest
                    if custom_dest.is_absolute()
                    else (self.repo_root / custom_dest).resolve()
                )
            else:
                latest_rel = ReleaseScanner.get_latest_release(self.repo_root)
                if latest_rel:
                    dest = latest_rel / "CODE_REVIEW.md"
                else:
                    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                    dest = self.repo_root / "docs" / "reports" / "code-review" / f"{ts}.md"

            dest.parent.mkdir(parents=True, exist_ok=True)
            status_badge = "🟢 PASSED" if passed else "🔴 FAILED"
            crit_count = sum(1 for s in smells if s.severity == "CRITICAL")
            warn_count = sum(1 for s in smells if s.severity == "WARNING")
            info_count = sum(1 for s in smells if s.severity == "INFO")

            standards_repr = ", ".join(f"`{p.name}`" for p in standards_paths) if standards_paths else "기본 베이스라인"
            spec_name = str(spec_path.relative_to(self.repo_root)) if spec_path else "None"
            strict_str = "활성화" if strict else "비활성화"

            c_info = ""
            if cache_stats and cache_stats.get("enabled"):
                c_info = f"- **체크포인트 캐시**: 활성화 (Hit: {cache_stats.get('hits', 0)}, Miss: {cache_stats.get('misses', 0)})"
            else:
                c_info = "- **체크포인트 캐시**: 비활성화"

            lines = [
                "# 🔍 Code Review & Architecture Audit Report",
                "",
                f"- **판정 상태**: {status_badge}",
                f"- **검사 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **검사 범위**: {scope_desc}",
                f"- **엄격 모드(Strict)**: {strict_str}",
                c_info,
                f"- **스펙 소스**: `{spec_name}`",
                f"- **참조 표준**: {standards_repr}",
                "",
                "---",
                "",
                "## 📊 요약 통계",
                f"- 검사 파일 수: {len(files_scanned)}개",
                f"- 검출 결함 총계: {len(smells)}건 (Critical: {crit_count}, Warning: {warn_count}, Info: {info_count})",
                "",
                "---",
                "",
                "## 🛠️ 정적 AST 코드 스멜 & 메트릭 (Stage 1)",
            ]

            if not smells:
                lines.append("- 🎉 정적 코드 스멜 및 결함이 검출되지 않았습니다.")
            else:
                for s in smells:
                    badge = {
                        "CRITICAL": "🔴 CRITICAL",
                        "WARNING": "🟡 WARNING",
                        "INFO": "🔵 INFO",
                    }.get(s.severity, "⚪ INFO")
                    try:
                        p_obj = Path(s.file_path)
                        rel_f = (
                            str(p_obj.relative_to(self.repo_root))
                            if p_obj.is_absolute() and self.repo_root in p_obj.parents
                            else p_obj.name
                        )
                    except Exception:
                        rel_f = Path(s.file_path).name
                    lines.append(f"### [{badge}] `{rel_f}:{s.line_no}` - {s.smell_type}")
                    lines.append(f"- **진단**: {s.message}")
                    lines.append(f"- **개선 제안**: {s.suggestion}")
                    lines.append("")

            lines.extend([
                "---",
                "",
                "## 🧠 2축 심층 감사 가이드 (Stage 2: LLM Axis)",
                "- **Standards Axis**: Fowler 12종 리팩토링 스멜 및 리포지토리 코딩 규약 준수 검증.",
                "- **Spec Axis**: PRD/명세 대비 요구사항 누락, 스코프 초과, 오구현 검증.",
            ])
            dest.write_text("\n".join(lines), encoding="utf-8")
            return dest
        except Exception:
            return None
