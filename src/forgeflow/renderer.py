"""
Terminal Box and JSON Report Renderer
"""

import datetime
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, List

from .validator import ReleaseCheckResult, TierRules


class ReportRenderer:
    """Renders human-readable terminal audit boxes and machine-readable JSON."""

    @staticmethod
    def render_terminal_report(results: List[ReleaseCheckResult]) -> str:
        lines = []
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
        total = len(results)

        lines.append("🔍 [ForgeFlow 하네스 게이트 감사 리포트]")
        lines.append(f"• 감사 일시: {now_str}")
        lines.append(f"• 검증 대상: 총 {total}개 릴리즈")
        lines.append("-" * 60)

        all_passed = True
        archived_count = sum(1 for r in results if getattr(r, "archived", False) and r.passed)
        display_archived_summary = archived_count > 1

        if display_archived_summary:
            lines.append(f"📦 과거 아카이브 릴리즈: 총 {archived_count}개 ➔ 🟢 ALL PASSED (증분 감사: 변경 없음/불변 보존)")
            lines.append("-" * 60)

        for r in results:
            if display_archived_summary and getattr(r, "archived", False) and r.passed:
                continue

            tier_name = TierRules.get_tier_name(r.tier)
            status_icon = "🟢 PASS" if r.passed else "🔴 FAIL"
            if not r.passed:
                all_passed = False

            lines.append(f"📦 릴리즈: {r.release_id} ({tier_name}) ➔ {status_icon}")

            # Document statuses
            for doc_name, doc_info in r.documents.items():
                if doc_info.get("exists") and doc_info.get("passed"):
                    doc_icon = "🟢"
                    state_msg = "정상 규격 충족"
                elif doc_info.get("exists") and not doc_info.get("passed"):
                    doc_icon = "🟡"
                    state_msg = "내용 불완전"
                else:
                    doc_icon = "🔴"
                    state_msg = "파일 누락"

                lines.append(f"  {doc_icon} {doc_name:<24}: {state_msg}")

            # Test execution status (if evaluated)
            if r.tests.get("executed"):
                test_icon = "🟢" if r.tests.get("passed") else "🔴"
                t_msg = "회귀 테스트 100% 통과" if r.tests.get("passed") else "회귀 테스트 실패"
                lines.append(f"  {test_icon} {'Regression Tests':<24}: {t_msg}")

            # Errors & Warnings
            if r.errors:
                lines.append("  [결함 상세]")
                for e in r.errors:
                    lines.append(f"    - ❌ {e}")

            if r.warnings:
                lines.append("  [경고]")
                for w in r.warnings:
                    lines.append(f"    - ⚠️ {w}")

            lines.append("-" * 60)

        if all_passed:
            lines.append("🎯 최종 판정: 🟢 ALL PASSED (모든 릴리즈 거버넌스 규격 충족 및 승격 가능)")
        else:
            lines.append("⚠️ 최종 판정: 🔴 FAILED (거버넌스 결함 존재. 결함 해결 전 승격 불가)")
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def render_json_report(results: List[ReleaseCheckResult]) -> str:
        all_passed = all(r.passed for r in results)
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "all_passed": all_passed,
            "total_releases": len(results),
            "releases": [asdict(r) for r in results],
            "results": [asdict(r) for r in results],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def render_terminal_review(result: Any) -> str:
        lines = []
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
        lines.append("🔍 [ForgeFlow Code Review & Architecture Audit Report]")
        lines.append(f"• 검사 일시: {now_str}")
        lines.append(f"• 검사 범위: {result.target_scope}")
        lines.append(f"• 스펙 소스: {result.spec_source or 'None'}")
        standards_str = ", ".join(result.standards_sources) if result.standards_sources else "기본 베이스라인"
        lines.append(f"• 참조 표준: {standards_str}")
        lines.append("-" * 60)

        crit_count = sum(1 for s in result.smells if s.severity == "CRITICAL")
        warn_count = sum(1 for s in result.smells if s.severity == "WARNING")
        info_count = sum(1 for s in result.smells if s.severity == "INFO")

        lines.append(
            f"📊 검사 결과: 파일 {len(result.files_scanned)}개 | 결함 {len(result.smells)}건 (Critical: {crit_count}, Warning: {warn_count}, Info: {info_count})"
        )
        lines.append("-" * 60)

        if not result.smells:
            lines.append("🎉 [Stage 1: AST 정적 분석] 정적 코드 스멜 및 결함이 검출되지 않았습니다.")
        else:
            lines.append("🛠️ [Stage 1: AST 정적 분석 결함 상세]")
            for s in result.smells[:25]:
                icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(s.severity, "⚪")
                p_name = Path(s.file_path).name
                lines.append(f"  {icon} [{s.severity}] {p_name}:{s.line_no} ({s.smell_type})")
                lines.append(f"     진단: {s.message}")
                lines.append(f"     제안: {s.suggestion}")

        refactor_needed = any(
            s.smell_type in ("File Bloat", "High Cognitive Complexity", "Deep Nesting", "Long Function")
            for s in result.smells
        )
        if refactor_needed:
            lines.append("-" * 60)
            lines.append("💡 [Deep Module & Clean Code 리팩토링 권장 사항]")
            lines.append("  • Guard Clause (Early Return): 중첩 조건문을 조기 반환으로 평탄화하여 인지 복잡도 저하")
            lines.append("  • Subroutine Extraction: 50줄 초과 및 복합 제어 루프를 논리적 보조 서브루틴으로 추출")
            lines.append("  • Deep Module 원칙: 얕은 헬퍼의 과도한 파편화를 지양하고, 단순한 인터페이스 뒤에 구현 은닉")
            lines.append("  • Module Promotion: 800줄 초과 God Module은 패키지 디렉터리로 승격(Package Promotion) 검토")

        lines.append("-" * 60)
        lines.append("🧠 [Stage 2: LLM 2축 심층 감사 가이드]")
        lines.append("  • Standards Axis: 코딩 규약 준수 및 Fowler 12종 리팩토링 스멜 점검")
        lines.append("  • Spec Axis: PRD/명세 대비 요구사항 누락, 스코프 초과, 왜곡 구현 점검")
        if result.report_path:
            lines.append(f"  📄 상세 리포트 저장됨: {result.report_path}")

        lines.append("-" * 60)
        if result.passed:
            lines.append("🎯 최종 판정: 🟢 PASSED (코드 품질 및 거버넌스 기준 충족)")
        else:
            lines.append("⚠️ 최종 판정: 🔴 FAILED (Critical 결함 존재 또는 엄격 모드 위반)")
        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def render_json_review(result: Any) -> str:
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
