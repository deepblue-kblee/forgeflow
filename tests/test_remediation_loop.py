"""
Unit and integration tests for Lightweight Autonomous Remediation Loop and Deterministic Failure Fingerprinting.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from forgeflow.harness import HarnessEngine, LifecycleError
from forgeflow.lifecycle import (
    AutonomousPolicy,
    ContinuationPolicy,
    LifecycleController,
    LifecycleStore,
    Status,
)
from forgeflow.reviewer import ReviewResult
from forgeflow.scaffold import TemplateScaffolder
from forgeflow.smell_detector import CodeSmell


class TestRemediationLoop(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.release_id = "v0.17.0-test-remediation"
        self.release = self.root / "docs" / "releases" / self.release_id
        TemplateScaffolder.create_release_scaffold(self.release, self.release_id, tier=3)
        self.engine = HarnessEngine(self.root)

    def test_autonomous_policy_activation_lightweight(self):
        # 1. Start lifecycle with policy="autonomous" without heavy HMAC attestation
        start_payload = self.engine.lifecycle_start(self.release_id, policy="autonomous")
        self.assertTrue(start_payload["ok"])
        self.assertEqual(start_payload["continuation_policy"], "autonomous")
        self.assertIsNotNone(start_payload.get("loop_record"))
        loop_rec = start_payload["loop_record"]
        self.assertEqual(loop_rec["continuation_policy"], "autonomous")
        self.assertEqual(loop_rec["attempt_count"], 0)
        self.assertEqual(loop_rec["no_progress_count"], 0)
        self.assertEqual(loop_rec["budget"], 5)
        self.assertEqual(loop_rec["remediations"], [])

        # 2. Check that check_lifecycle_evidence does not emit autonomous_activation_unverified
        result = self.engine.check_lifecycle_evidence(self.release_id)
        self.assertNotIn("autonomous_activation_unverified", result["unmet_conditions"])

    def test_deterministic_failure_fingerprint(self):
        # Errors with identical structure but volatile memory addresses, timestamps, and temp dirs
        err1 = (
            "Traceback (most recent call last):\n"
            "  File '/tmp/tmp_xyz123/module.py', line 42, in test_fn\n"
            "    raise AssertionError('failed at 2026-10-17T18:00:00Z object at 0x7ffd5b6c')\n"
            "AssertionError: failed"
        )
        err2 = (
            "Traceback (most recent call last):\n"
            "  File '/var/folders/ab/cd/T/tmp_abc987/module.py', line 42, in test_fn\n"
            "    raise AssertionError('failed at 2026-10-17T19:35:12.123456Z object at 0x10a2b3c4')\n"
            "AssertionError: failed"
        )
        fp1 = HarnessEngine.compute_failure_fingerprint("test_fn", err1)
        fp2 = HarnessEngine.compute_failure_fingerprint("test_fn", err2)
        self.assertEqual(fp1, fp2, "Volatile noise (paths, timestamps, addresses) must produce identical fingerprints")

        # Different error should produce different fingerprint
        err3 = "AssertionError: unexpected value"
        fp3 = HarnessEngine.compute_failure_fingerprint("test_other", err3)
        self.assertNotEqual(fp1, fp3)

    def test_loop_record_persistence_and_remediation_lifecycle(self):
        self.engine.lifecycle_start(self.release_id, policy="autonomous")
        controller = self.engine._core_controller(self.release_id)

        # Record a remediation finding
        findings = [
            {"id": "REM-001", "file": "src/module.py", "line": 42, "description": "IndexError in parser", "severity": "CRITICAL"}
        ]
        fp = HarnessEngine.compute_failure_fingerprint("src/module.py", "IndexError")
        updated = controller.record_remediation(findings, verdict="REJECT", failure_fingerprint=fp)

        loop_rec = updated["control"]["loop_record"]
        self.assertEqual(loop_rec["attempt_count"], 1)
        self.assertEqual(loop_rec["no_progress_count"], 1)
        self.assertEqual(loop_rec["latest_verdict"], "REJECT")
        self.assertEqual(len(loop_rec["remediations"]), 1)
        self.assertEqual(loop_rec["remediations"][0]["status"], "OPEN")

        # Verify persistence and reload
        store = LifecycleStore(self.root, self.release_id)
        reloaded = store.load()
        self.assertEqual(reloaded["control"]["loop_record"]["attempt_count"], 1)
        self.assertEqual(reloaded["control"]["loop_record"]["remediations"][0]["id"], "REM-001")

        # Resolve remediation with new candidate SHA
        new_candidate = "a" * 40
        resolved = controller.resolve_remediation("REM-001", candidate_sha=new_candidate)
        loop_rec_res = resolved["control"]["loop_record"]
        self.assertEqual(loop_rec_res["remediations"][0]["status"], "RESOLVED")
        self.assertEqual(loop_rec_res["latest_verdict"], "PASS")
        self.assertEqual(loop_rec_res["candidate_sha"], new_candidate)
        self.assertEqual(resolved["identity"]["candidate_sha"], new_candidate)

    def test_circuit_breaker_exact_five_rounds(self):
        self.engine.lifecycle_start(self.release_id, policy="autonomous")
        controller = self.engine._core_controller(self.release_id)
        fp = HarnessEngine.compute_failure_fingerprint("test_loop", "AssertionError: stuck")

        for i in range(1, 5):
            res = controller.record_remediation(
                [{"id": "REM-STUCK", "description": "Stuck defect"}],
                verdict="REJECT",
                failure_fingerprint=fp,
            )
            loop_rec = res["control"]["loop_record"]
            self.assertEqual(loop_rec["no_progress_count"], i)
            self.assertEqual(res["progress"]["status"], "ACTIVE")
            self.assertIsNone(loop_rec["terminal_reason"])

        # 5th attempt must trip the circuit breaker
        res5 = controller.record_remediation(
            [{"id": "REM-STUCK", "description": "Stuck defect"}],
            verdict="REJECT",
            failure_fingerprint=fp,
        )
        loop_rec5 = res5["control"]["loop_record"]
        self.assertEqual(loop_rec5["no_progress_count"], 5)
        self.assertEqual(loop_rec5["terminal_reason"], "circuit-breaker")
        self.assertEqual(res5["progress"]["status"], "BLOCKED")
        self.assertIn("circuit_breaker_tripped", res5["progress"]["next_action"])

    def test_completion_guard_blocks_unresolved_remediation(self):
        self.engine.lifecycle_start(self.release_id, policy="autonomous")
        controller = self.engine._core_controller(self.release_id)

        # Record active open remediation
        controller.record_remediation(
            [{"id": "REM-BLOCK", "description": "Must be fixed", "status": "OPEN"}],
            verdict="REJECT"
        )

        ready, reasons = controller.completion_ready()
        self.assertFalse(ready)
        self.assertIn("unresolved_remediation_active", reasons)

        # Also verify lifecycle_complete reports unresolved_remediation_active
        res = self.engine.lifecycle_complete(self.release_id)
        self.assertIn("unresolved_remediation_active", res["unmet_conditions"])

        # Once resolved, the condition is cleared
        controller.resolve_remediation("REM-BLOCK", candidate_sha="b" * 40)
        ready_after, reasons_after = controller.completion_ready()
        self.assertNotIn("unresolved_remediation_active", reasons_after)

    def test_review_result_to_remediations(self):
        smells = [
            CodeSmell(file_path="src/app.py", line_no=10, smell_type="IO_IN_LOOP", severity="WARNING", message="I/O in loop", suggestion="move outside"),
            CodeSmell(file_path="src/sec.py", line_no=20, smell_type="SECURITY_VULN", severity="CRITICAL", message="eval() detected", suggestion="use ast.literal_eval"),
        ]
        review_res = ReviewResult(
            repo_root=str(self.root),
            target_scope="src",
            files_scanned=["src/app.py", "src/sec.py"],
            smells=smells,
            spec_source=None,
            standards_sources=[],
            standards_prompt="",
            spec_prompt="",
            report_path=None,
            passed=False,
            strict=True,
        )
        remediations = review_res.to_remediations()
        self.assertEqual(len(remediations), 2)
        self.assertEqual(remediations[0]["id"], "REM-001")
        self.assertEqual(remediations[0]["rule_id"], "IO_IN_LOOP")
        self.assertEqual(remediations[0]["status"], "OPEN")
        self.assertEqual(remediations[1]["id"], "REM-002")
        self.assertEqual(remediations[1]["severity"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()
