#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from forgeflow.diagnostics import (
    DiagnosticAnalyzer,
    DiagnosticAnomaly,
    DiagnosticLogger,
    doctor_main,
)


class TestDiagnosticLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.logger = DiagnosticLogger(repo_root=self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_log_event_and_read(self):
        self.logger.log_event(
            command="lifecycle advance",
            release_id="v0.10.0-test",
            tier="Tier 3",
            status="ACTIVE",
            latency_ms=45.2,
            exit_code=0,
        )
        events = self.logger.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["command"], "lifecycle advance")
        self.assertEqual(events[0]["release_id"], "v0.10.0-test")
        self.assertEqual(events[0]["exit_code"], 0)

    def test_privacy_guard_filters_sensitive_keys(self):
        self.logger.log_event(
            command="check",
            details={
                "safe_info": "ok",
                "diff": "secret diff text",
                "code": "private source code",
                "env": "API_KEY=12345",
                "secret": "super_secret",
            },
        )
        events = self.logger.read_events()
        self.assertEqual(len(events), 1)
        det = events[0]["details"]
        self.assertIn("safe_info", det)
        self.assertNotIn("diff", det)
        self.assertNotIn("code", det)
        self.assertNotIn("env", det)
        self.assertNotIn("secret", det)

    def test_clear_logs(self):
        self.logger.log_event(command="check")
        self.assertEqual(len(self.logger.read_events()), 1)
        self.logger.clear()
        self.assertEqual(len(self.logger.read_events()), 0)


class TestDiagnosticAnalyzer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.logger = DiagnosticLogger(repo_root=self.root)
        self.analyzer = DiagnosticAnalyzer(repo_root=self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_healthy_when_no_anomalies(self):
        self.logger.log_event(command="check", exit_code=0, latency_ms=100.0)
        report = self.analyzer.generate_doctor_report()
        self.assertEqual(report["status"], "🟢 HEALTHY")
        self.assertEqual(report["summary"]["total_anomalies"], 0)

    def test_repeated_failure_detection(self):
        for _ in range(3):
            self.logger.log_event(
                command="lifecycle seal",
                exit_code=1,
                error="release_candidate_range_invalid",
            )
        anomalies = self.analyzer.analyze()
        self.assertTrue(any(a.anomaly_type == "REPEATED_FAILURE" for a in anomalies))
        report = self.analyzer.generate_doctor_report()
        self.assertEqual(report["status"], "🔴 ANOMALY DETECTED")

    def test_high_latency_detection(self):
        self.logger.log_event(command="check --all", latency_ms=65000.0, exit_code=0)
        anomalies = self.analyzer.analyze()
        self.assertTrue(any(a.anomaly_type == "HIGH_LATENCY" for a in anomalies))

    def test_redundant_check_detection(self):
        for _ in range(4):
            self.logger.log_event(command="check", release_id="v0.10.0-test", exit_code=0)
        anomalies = self.analyzer.analyze()
        self.assertTrue(any(a.anomaly_type == "REDUNDANT_CHECK" for a in anomalies))

    def test_generate_issue_draft(self):
        self.logger.log_event(
            command="lifecycle advance",
            exit_code=2,
            error="qa_evidence_malformed",
        )
        draft = self.analyzer.generate_issue_draft()
        self.assertIn("Field Diagnostic", draft["title"])
        self.assertIn("진단 환경 정보", draft["body"])
        self.assertIn("ForgeFlow Version", draft["body"])


class TestDoctorCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_doctor_main_healthy(self):
        code = doctor_main(args=[], repo_root=self.root)
        self.assertEqual(code, 0)

    def test_doctor_main_json(self):
        import io
        import sys

        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            code = doctor_main(args=["--json"], repo_root=self.root)
            self.assertEqual(code, 0)
            data = json.loads(buf.getvalue())
            self.assertIn("status", data)
            self.assertIn("system_info", data)
        finally:
            sys.stdout = old_stdout

    def test_doctor_main_clear(self):
        code = doctor_main(args=["--clear"], repo_root=self.root)
        self.assertEqual(code, 0)

    def test_doctor_detects_missing_speckit_prerequisites(self):
        # Create .specify dir without bash scripts
        (self.root / ".specify").mkdir()
        analyzer = DiagnosticAnalyzer(repo_root=self.root)
        anomalies = analyzer.analyze()
        types = [a.anomaly_type for a in anomalies]
        self.assertIn("MISSING_SPECKIT_PREREQUISITE", types)

    def test_doctor_detects_legacy_config_amnesia(self):
        config_file = self.root / ".forgeflow.json"
        # 1. Version < 0.1.0
        config_file.write_text(json.dumps({"forgeflow_version": "0.0.9"}), encoding="utf-8")
        analyzer = DiagnosticAnalyzer(repo_root=self.root)
        anomalies = analyzer.analyze()
        types = [a.anomaly_type for a in anomalies]
        self.assertIn("LEGACY_CONFIG_DETECTED", types)

        # 2. Past pre-reset version (0.22.1 / 0.23.0) without constitution.md
        config_file.write_text(json.dumps({"forgeflow_version": "0.22.1"}), encoding="utf-8")
        analyzer = DiagnosticAnalyzer(repo_root=self.root)
        anomalies = analyzer.analyze()
        types = [a.anomaly_type for a in anomalies]
        self.assertIn("LEGACY_CONFIG_DETECTED", types)

    def test_doctor_allows_newer_forgeflow_version(self):
        config_file = self.root / ".forgeflow.json"
        for ver in ("0.1.0", "0.1.9", "0.1.10", "0.1.11", "0.1.12", "0.2.0"):
            config_file.write_text(json.dumps({"forgeflow_version": ver}), encoding="utf-8")
            analyzer = DiagnosticAnalyzer(repo_root=self.root)
            anomalies = analyzer.analyze()
            types = [a.anomaly_type for a in anomalies]
            self.assertNotIn("LEGACY_CONFIG_DETECTED", types)

    def test_doctor_allows_future_high_version_with_speckit(self):
        # When future framework naturally reaches 0.22.0+, constitution.md exists
        config_file = self.root / ".forgeflow.json"
        config_file.write_text(json.dumps({"forgeflow_version": "0.22.0"}), encoding="utf-8")
        constitution = self.root / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True, exist_ok=True)
        constitution.write_text("# Constitution\n", encoding="utf-8")

        analyzer = DiagnosticAnalyzer(repo_root=self.root)
        anomalies = analyzer.analyze()
        types = [a.anomaly_type for a in anomalies]
        self.assertNotIn("LEGACY_CONFIG_DETECTED", types)

    def test_doctor_detects_legacy_governance_fields(self):
        config_file = self.root / ".forgeflow.json"
        config_file.write_text(json.dumps({
            "forgeflow_version": "0.1.11",
            "governance": {"required_documents": ["PRD.md"]}
        }), encoding="utf-8")
        analyzer = DiagnosticAnalyzer(repo_root=self.root)
        anomalies = analyzer.analyze()
        types = [a.anomaly_type for a in anomalies]
        self.assertIn("LEGACY_CONFIG_DETECTED", types)


if __name__ == "__main__":
    unittest.main()
