#!/usr/bin/env python3
import json
import math
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from forgeflow.runner import RuntimeTestRunner
from forgeflow.diagnostics import DiagnosticAnalyzer


class TestRuntimeTestRunnerTimeout(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_timeout_when_no_config(self):
        timeout = RuntimeTestRunner.resolve_test_timeout(self.root)
        self.assertEqual(timeout, 60.0)

    def test_default_timeout_when_key_absent(self):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({"governance": {"strict_mode": True}}), encoding="utf-8")
        timeout = RuntimeTestRunner.resolve_test_timeout(self.root)
        self.assertEqual(timeout, 60.0)

    def test_valid_integer_timeout(self):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": 120}}), encoding="utf-8")
        timeout = RuntimeTestRunner.resolve_test_timeout(self.root)
        self.assertEqual(timeout, 120.0)
        self.assertIsInstance(timeout, float)

    def test_valid_float_timeout(self):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": 75.5}}), encoding="utf-8")
        timeout = RuntimeTestRunner.resolve_test_timeout(self.root)
        self.assertEqual(timeout, 75.5)

    def test_reject_bool_values(self):
        for bool_val in [True, False]:
            config_path = self.root / ".forgeflow.json"
            config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": bool_val}}), encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                RuntimeTestRunner.resolve_test_timeout(self.root)
            self.assertIn("expected positive number", str(ctx.exception))

    def test_reject_string_values(self):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": "120"}}), encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            RuntimeTestRunner.resolve_test_timeout(self.root)
        self.assertIn("expected positive number", str(ctx.exception))

    def test_reject_zero_and_negative_values(self):
        for bad_val in [0, -1, -50.0]:
            config_path = self.root / ".forgeflow.json"
            config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": bad_val}}), encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                RuntimeTestRunner.resolve_test_timeout(self.root)
            self.assertIn("expected positive number", str(ctx.exception))

    def test_reject_malformed_json(self):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text("{ broken json", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            RuntimeTestRunner.resolve_test_timeout(self.root)
        self.assertIn("Failed to parse .forgeflow.json", str(ctx.exception))

    @patch("subprocess.run")
    def test_run_tests_propagates_configured_timeout(self, mock_run):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": 150}}), encoding="utf-8")
        tests_dir = self.root / "tests"
        tests_dir.mkdir(parents=True)

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "OK"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = RuntimeTestRunner.run_tests(self.root)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get("timeout"), 150.0)
        self.assertTrue(result.get("passed"))

    @patch("subprocess.run")
    def test_run_tests_explicit_param_overrides_config(self, mock_run):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": 150}}), encoding="utf-8")
        tests_dir = self.root / "tests"
        tests_dir.mkdir(parents=True)

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "OK"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = RuntimeTestRunner.run_tests(self.root, timeout=45.0)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get("timeout"), 45.0)
        self.assertTrue(result.get("passed"))

    @patch("subprocess.run")
    def test_run_tests_timeout_expired_reports_custom_timeout(self, mock_run):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({"governance": {"test_timeout_seconds": 120}}), encoding="utf-8")
        tests_dir = self.root / "tests"
        tests_dir.mkdir(parents=True)

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=120.0)

        result = RuntimeTestRunner.run_tests(self.root)
        self.assertTrue(result.get("executed"))
        self.assertFalse(result.get("passed"))
        self.assertEqual(result.get("returncode"), -1)
        self.assertIn("Tests timed out after 120.0 seconds.", result.get("output", ""))

    def test_diagnostics_detects_invalid_test_timeout(self):
        config_path = self.root / ".forgeflow.json"
        config_path.write_text(json.dumps({
            "forgeflow_version": "0.1.18",
            "governance": {
                "tasks_dir": "tasks",
                "test_timeout_seconds": -10,
            }
        }), encoding="utf-8")

        analyzer = DiagnosticAnalyzer(repo_root=self.root)
        anomalies = analyzer.analyze()
        timeout_anomalies = [a for a in anomalies if a.anomaly_type == "INVALID_TEST_TIMEOUT"]
        self.assertEqual(len(timeout_anomalies), 1)
        self.assertEqual(timeout_anomalies[0].severity, "WARNING")


if __name__ == "__main__":
    unittest.main()
