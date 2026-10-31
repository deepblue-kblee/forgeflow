"""
Field Diagnostics, Structured Event Logging, and Doctor CLI (Zero-Dependency)
"""

import json
import math
import os
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ._version import __version__
from .scanner import HierarchicalRootScanner


def _parse_version_tuple(v_str: Any) -> tuple:
    import re
    nums = re.findall(r"\d+", str(v_str))
    return tuple(map(int, nums)) if nums else (0,)


@dataclass
class DiagnosticAnomaly:
    anomaly_type: str  # REPEATED_FAILURE, REDUNDANT_CHECK, HIGH_LATENCY, WORKTREE_LOCK
    severity: str      # CRITICAL, WARNING, INFO
    message: str
    remedy: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DiagnosticLogger:
    """Non-invasive, append-only local event logger for ForgeFlow commands."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = (repo_root or HierarchicalRootScanner.find_root()).resolve()
        self.diag_dir = self.repo_root / ".forgeflow" / "diagnostics"
        self.log_file = self.diag_dir / "session.jsonl"

    def log_event(
        self,
        command: str,
        release_id: Optional[str] = None,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        latency_ms: float = 0.0,
        exit_code: int = 0,
        error: Optional[str] = None,
        unmet_conditions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append an event to session.jsonl with privacy protection."""
        try:
            self.diag_dir.mkdir(parents=True, exist_ok=True)
            # Sanitized, anonymous event payload
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "command": str(command),
                "release_id": str(release_id) if release_id else None,
                "tier": str(tier) if tier else None,
                "status": str(status) if status else None,
                "latency_ms": round(float(latency_ms), 2),
                "exit_code": int(exit_code),
                "error": str(error) if error else None,
                "unmet_conditions": list(unmet_conditions) if unmet_conditions else [],
                "details": {
                    k: str(v)
                    for k, v in (details or {}).items()
                    if k not in ("diff", "code", "env", "secret", "token", "key")
                },
            }
            line = json.dumps(event, ensure_ascii=False) + "\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            # Fail-open: never block the primary workflow
            pass

    def read_events(self) -> List[Dict[str, Any]]:
        if not self.log_file.exists():
            return []
        events = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        try:
                            events.append(json.loads(stripped))
                        except Exception:
                            continue
        except Exception:
            return []
        return events

    def clear(self) -> None:
        if self.log_file.exists():
            try:
                self.log_file.unlink()
            except Exception:
                pass


class DiagnosticAnalyzer:
    """Analyzes local diagnostic events to detect bottlenecks and anomalies."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = (repo_root or HierarchicalRootScanner.find_root()).resolve()
        self.logger = DiagnosticLogger(repo_root=self.repo_root)

    def analyze(self, events: Optional[List[Dict[str, Any]]] = None) -> List[DiagnosticAnomaly]:
        if events is None:
            events = self.logger.read_events()
        anomalies: List[DiagnosticAnomaly] = []

        # 1. Repeated Failures Detection (No-progress loop)
        failure_streak = 0
        last_failed_cmd = None
        last_failed_ev = None

        def record_failure_streak() -> None:
            nonlocal failure_streak, last_failed_cmd, last_failed_ev
            if failure_streak >= 3 and last_failed_cmd is not None and last_failed_ev is not None:
                anomalies.append(
                    DiagnosticAnomaly(
                        anomaly_type="REPEATED_FAILURE",
                        severity="CRITICAL",
                        message=f"명령어 '{last_failed_cmd}'가 {failure_streak}회 연속 실패하여 No-Progress 루프에 진입했습니다.",
                        remedy=f"'{last_failed_cmd}'의 오류 사유({last_failed_ev.get('error') or last_failed_ev.get('unmet_conditions')})를 검토하고 필수 선행 조건을 충족하세요.",
                        context={"command": last_failed_cmd, "streak": failure_streak, "error": last_failed_ev.get("error")},
                    )
                )

        for ev in events:
            is_failure = ev.get("exit_code", 0) != 0 or ev.get("error") is not None
            cmd = ev.get("command")
            if is_failure:
                if cmd == last_failed_cmd:
                    failure_streak += 1
                else:
                    record_failure_streak()
                    failure_streak = 1
                    last_failed_cmd = cmd
                last_failed_ev = ev
            else:
                record_failure_streak()
                failure_streak = 0
                last_failed_cmd = None
                last_failed_ev = None
        record_failure_streak()

        # 2. Redundant Verification Detection
        check_streak = 0
        last_check_rel = None

        def record_check_streak() -> None:
            nonlocal check_streak, last_check_rel
            if check_streak >= 4 and last_check_rel is not None:
                anomalies.append(
                    DiagnosticAnomaly(
                        anomaly_type="REDUNDANT_CHECK",
                        severity="WARNING",
                        message=f"동일 릴리즈('{last_check_rel}')에 대해 불필요한 반복 검증이 {check_streak}회 연속 실행되었습니다.",
                        remedy="동일 커밋 상태에서는 엄격 감사 캐시를 활용하거나 Fast-Path 클로즈를 적용하세요.",
                        context={"release_id": last_check_rel, "streak": check_streak},
                    )
                )

        for ev in events:
            cmd = ev.get("command", "")
            if "check" in cmd or "complete" in cmd:
                rel = ev.get("release_id")
                if rel == last_check_rel and ev.get("exit_code") == 0:
                    check_streak += 1
                else:
                    record_check_streak()
                    check_streak = 1
                    last_check_rel = rel
            else:
                record_check_streak()
                check_streak = 0
                last_check_rel = None
        record_check_streak()

        # 3. High Latency Detection (> 60,000ms)
        for ev in events:
            lat = ev.get("latency_ms", 0.0)
            if lat > 60000.0:
                cmd = ev.get("command")
                anomalies.append(
                    DiagnosticAnomaly(
                        anomaly_type="HIGH_LATENCY",
                        severity="WARNING",
                        message=f"명령어 '{cmd}' 실행에 {lat/1000:.1f}초가 소요되어 병목이 발생했습니다.",
                        remedy="회귀 테스트 범위 및 정적 분석 파일 대상을 점검하고 증분 감사 옵션을 사용하세요.",
                        context={"command": cmd, "latency_ms": lat},
                    )
                )

        # 4. Spec Kit Hybrid Environment Prerequisite Validation
        specify_dir = self.repo_root / ".specify"
        if specify_dir.is_dir():
            required_scripts = ["check-prerequisites.sh", "setup-plan.sh"]
            for s in required_scripts:
                s_path = specify_dir / "scripts" / "bash" / s
                if not s_path.exists():
                    anomalies.append(
                        DiagnosticAnomaly(
                            anomaly_type="MISSING_SPECKIT_PREREQUISITE",
                            severity="CRITICAL",
                            message=f"Spec Kit 필수 런타임 스크립트(.specify/scripts/bash/{s})가 누락되었습니다.",
                            remedy="후속 /speckit-clarify 및 /speckit-plan의 exit 127 방지를 위해 'forgeflow init --speckit'을 실행하세요.",
                            context={"missing_file": str(s_path.relative_to(self.repo_root))},
                        )
                    )
                elif not os.access(s_path, os.X_OK):
                    anomalies.append(
                        DiagnosticAnomaly(
                            anomaly_type="SPECKIT_SCRIPT_NOT_EXECUTABLE",
                            severity="CRITICAL",
                            message=f"Spec Kit 스크립트(.specify/scripts/bash/{s})에 실행 권한이 없습니다.",
                            remedy=f"chmod +x {s_path} 를 실행하거나 'forgeflow init --speckit'을 재실행하세요.",
                            context={"script_file": str(s_path.relative_to(self.repo_root))},
                        )
                    )

        # 5. Legacy Configuration & Amnesia Policy Check (Baseline Date: 2026-10-20)
        modern_cfg = self.repo_root / ".forgeflow" / "config.json"
        legacy_cfg = self.repo_root / ".forgeflow.json"
        config_file = modern_cfg if modern_cfg.is_file() else legacy_cfg
        cfg_name = ".forgeflow/config.json" if config_file == modern_cfg else ".forgeflow.json"
        if config_file.is_file():
            try:
                cfg = json.loads(config_file.read_text(encoding="utf-8"))
                version_str = cfg.get("forgeflow_version", "")
                v_tuple = _parse_version_tuple(version_str) if version_str else (0,)
                gov = cfg.get("governance", {}) if isinstance(cfg.get("governance"), dict) else {}
                has_speckit = (self.repo_root / ".specify" / "memory" / "constitution.md").is_file()

                # Amnesia epoch: 2026-10-20 00:00:00 KST
                amnesia_epoch = 1792422000
                mtime = config_file.stat().st_mtime

                # Detect 2026-10-20 pre-reset legacy configurations
                is_legacy = (
                    v_tuple < (0, 1, 0)
                    or "required_documents" in gov
                    or "default_tier" in gov
                    or mtime < (amnesia_epoch - 86400)
                    or ((0, 21, 0) <= v_tuple <= (0, 23, 99) and not has_speckit)
                )
                if is_legacy:
                    anomalies.append(
                        DiagnosticAnomaly(
                            anomaly_type="LEGACY_CONFIG_DETECTED",
                            severity="WARNING",
                            message="2026-10-20 이전의 구버전 거버넌스 설정이 감지되었습니다 (하위 호환 미지원).",
                            remedy="'forgeflow init --speckit'을 실행하여 v0.1.0+ 최신 표준 설정으로 교체하세요.",
                            context={"current_version": cfg.get("forgeflow_version")},
                        )
                    )

                # Validate test_timeout_seconds if specified in governance
                if "test_timeout_seconds" in gov:
                    raw_timeout = gov.get("test_timeout_seconds")
                    is_invalid = False
                    if isinstance(raw_timeout, bool) or not isinstance(raw_timeout, (int, float)):
                        is_invalid = True
                    elif not math.isfinite(raw_timeout) or raw_timeout <= 0:
                        is_invalid = True

                    if is_invalid:
                        anomalies.append(
                            DiagnosticAnomaly(
                                anomaly_type="INVALID_TEST_TIMEOUT",
                                severity="WARNING",
                                message="유효하지 않은 test_timeout_seconds 설정이 감지되었습니다 (양수 숫자 필요).",
                                remedy=f"{cfg_name}의 governance.test_timeout_seconds 값을 60 이상의 양수 숫자로 수정하세요.",
                                context={"test_timeout_seconds": raw_timeout},
                            )
                        )

                # Validate auto_create_branch if specified in governance
                if "auto_create_branch" in gov:
                    raw_acb = gov.get("auto_create_branch")
                    if not isinstance(raw_acb, bool):
                        anomalies.append(
                            DiagnosticAnomaly(
                                anomaly_type="INVALID_AUTO_CREATE_BRANCH",
                                severity="WARNING",
                                message="유효하지 않은 auto_create_branch 설정이 감지되었습니다 (불리언 true/false 필요).",
                                remedy=f"{cfg_name}의 governance.auto_create_branch 값을 true 또는 false로 수정하세요.",
                                context={"auto_create_branch": raw_acb},
                            )
                        )
            except Exception:
                pass

        return anomalies

    def generate_doctor_report(self) -> Dict[str, Any]:
        events = self.logger.read_events()
        anomalies = self.analyze(events=events)

        crit_count = sum(1 for a in anomalies if a.severity == "CRITICAL")
        warn_count = sum(1 for a in anomalies if a.severity == "WARNING")

        if crit_count > 0:
            status = "🔴 ANOMALY DETECTED"
        elif warn_count > 0:
            status = "🟡 WARNING"
        else:
            status = "🟢 HEALTHY"

        return {
            "status": status,
            "system_info": {
                "forgeflow_version": __version__,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "os": f"{platform.system()} {platform.release()}",
                "platform": platform.platform(),
            },
            "summary": {
                "total_events": len(events),
                "total_anomalies": len(anomalies),
                "critical": crit_count,
                "warning": warn_count,
            },
            "anomalies": [a.to_dict() for a in anomalies],
        }

    def generate_issue_draft(self, anomaly: Optional[DiagnosticAnomaly] = None) -> Dict[str, str]:
        report = self.generate_doctor_report()
        sys_info = report["system_info"]
        anomalies = report["anomalies"]

        if anomaly:
            target_anomaly = anomaly.to_dict()
        elif anomalies:
            target_anomaly = anomalies[0]
        else:
            target_anomaly = {
                "anomaly_type": "FIELD_FEEDBACK",
                "message": "사용자 자발적 피드백 및 필드 관측 리포트",
                "remedy": "원인 분석 및 개선 검토",
                "context": {},
            }

        title = f"[Field Diagnostic]: {target_anomaly['anomaly_type']} - {target_anomaly['message'][:60]}"

        body_lines = [
            "## 1. 진단 환경 정보 (Environment)",
            f"- **ForgeFlow Version**: `v{sys_info['forgeflow_version']}`",
            f"- **Python Version**: `{sys_info['python_version']}`",
            f"- **OS Platform**: `{sys_info['platform']}`",
            "",
            "## 2. 감지된 이상 징후 (Detected Anomaly)",
            f"- **유형**: `{target_anomaly['anomaly_type']}`",
            f"- **심각도**: `{target_anomaly.get('severity', 'WARNING')}`",
            f"- **현상**: {target_anomaly['message']}",
            f"- **권장 조치**: {target_anomaly['remedy']}",
            "",
            "## 3. 이상 세션 컨텍스트 (Diagnostic Context)",
            "```json",
            json.dumps(target_anomaly.get("context", {}), indent=2, ensure_ascii=False),
            "```",
            "",
            "## 4. 최근 진단 이벤트 시퀀스 (Recent Event Trace)",
            "```text",
        ]

        recent_events = self.logger.read_events()[-10:]
        if recent_events:
            for ev in recent_events:
                ts = ev.get("timestamp", "").split("T")[-1][:8]
                cmd = ev.get("command")
                ec = ev.get("exit_code", 0)
                lat = ev.get("latency_ms", 0)
                body_lines.append(f"[{ts}] {cmd} (exit={ec}, latency={lat}ms)")
        else:
            body_lines.append("No event trace recorded.")
        body_lines.extend([
            "```",
            "",
            "## 5. 기대 동작 (Expected Behavior)",
            "정상적인 상태 전이 및 멱등 가드레일이 원활히 동작해야 합니다.",
        ])

        return {"title": title, "body": "\n".join(body_lines)}


def doctor_main(args: Optional[List[str]] = None, repo_root: Optional[Path] = None) -> int:
    """CLI handler for 'forgeflow doctor'."""
    import argparse

    parser = argparse.ArgumentParser(prog="forgeflow doctor", description="Run ForgeFlow diagnostic health check")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON report")
    parser.add_argument("--report-issue", action="store_true", help="Generate structured GitHub Issue draft from diagnostics")
    parser.add_argument("--clear", action="store_true", help="Clear local diagnostic event logs")
    parsed = parser.parse_args(args)

    analyzer = DiagnosticAnalyzer(repo_root=repo_root)

    if parsed.clear:
        analyzer.logger.clear()
        print("🧹 Local diagnostic logs cleared.")
        return 0

    if parsed.report_issue:
        anomalies = analyzer.analyze()
        target = anomalies[0] if anomalies else None
        draft = analyzer.generate_issue_draft(target)
        if parsed.json:
            print(json.dumps(draft, indent=2, ensure_ascii=False))
        else:
            print("=" * 60)
            print(f"📋 Generated Issue Title: {draft['title']}")
            print("=" * 60)
            print(draft["body"])
            print("=" * 60)
            print("💡 'forgeflow issue create' 또는 GitHub 저장소에 등록하세요.")
        return 0

    report = analyzer.generate_doctor_report()
    if parsed.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    # Terminal rendering
    print("🏥 [ForgeFlow Doctor: System Health & Diagnostics]")
    print(f"• 판정 상태: {report['status']}")
    print(f"• ForgeFlow 버전: v{report['system_info']['forgeflow_version']}")
    print(f"• Python 버전: {report['system_info']['python_version']}")
    print(f"• OS 플랫폼: {report['system_info']['platform']}")
    print("-" * 60)
    print(f"📊 이벤트 요약: 총 {report['summary']['total_events']}건 기록됨")
    print(f"• 감지된 이상 징후: {report['summary']['total_anomalies']}건 (Critical: {report['summary']['critical']}, Warning: {report['summary']['warning']})")
    print("-" * 60)

    if not report["anomalies"]:
        print("🎉 현재 거버넌스 수행 이력에 이상 징후나 성능 병목이 없습니다.")
    else:
        print("🛠️ [감지된 이상 징후 상세]")
        for a in report["anomalies"]:
            badge = "🔴 CRITICAL" if a["severity"] == "CRITICAL" else "🟡 WARNING"
            print(f"  [{badge}] {a['anomaly_type']}")
            print(f"     현상: {a['message']}")
            print(f"     제안: {a['remedy']}")
        print("-" * 60)
        print("💡 '--report-issue' 플래그를 사용하여 문제 해결용 GitHub Issue 초안을 자동 생성할 수 있습니다.")

    print("=" * 60)
    return 0 if report["summary"]["critical"] == 0 else 1
