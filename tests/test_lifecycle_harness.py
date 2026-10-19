import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from forgeflow.harness import HarnessEngine, LifecycleError
from forgeflow.scaffold import TemplateScaffolder


class TestLifecycleHarness(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.release_id = "v0.5.0-harness-fixture"
        self.release = self.root / "docs" / "releases" / self.release_id
        TemplateScaffolder.create_release_scaffold(self.release, self.release_id, tier=3)
        self.engine = HarnessEngine(self.root)

    def test_legacy_evidence_audit_does_not_require_lifecycle_state(self):
        result = self.engine.check_lifecycle_evidence(self.release_id)
        self.assertFalse(result["ok"])
        self.assertTrue(any(item.startswith("evidence_malformed:") for item in result["unmet_conditions"]))
        self.assertFalse((self.root / ".forgeflow" / "lifecycle").exists())

    def test_malformed_state_is_fail_closed(self):
        state_dir = self.root / ".forgeflow" / "lifecycle"
        state_dir.mkdir(parents=True)
        (state_dir / f"{self.release_id}.json").write_text("{broken", encoding="utf-8")
        result = self.engine.check_lifecycle_evidence(self.release_id)
        self.assertIn("lifecycle_state_malformed", result["unmet_conditions"])

    def test_explicit_autonomous_state_requires_attestation_and_terminal_completion(self):
        self.engine.lifecycle_start(self.release_id)
        controller = self.engine._core_controller(self.release_id)
        controller._update(lambda state: state["progress"].update(continuation_policy="autonomous"))
        self.assertEqual(controller.status.value, "ACTIVE")
        result = self.engine.check_lifecycle_evidence(self.release_id)
        self.assertIn("autonomous_activation_unverified", result["unmet_conditions"])

    def test_lifecycle_state_candidate_must_match_evidence_when_evidence_exists(self):
        self.engine.lifecycle_start(self.release_id)
        controller = self.engine._core_controller(self.release_id)
        controller._update(lambda state: state["identity"].update(candidate_sha="0" * 40))
        loaded = self.engine.lifecycle_status(self.release_id)
        self.assertEqual(loaded["release_id"], self.release_id)
        self.assertEqual(loaded["status"], "ACTIVE")

    def test_cli_store_rejects_stale_revision_and_digest(self):
        store = self.engine.lifecycle_store()
        store.create(self.release_id, tier=3)
        stale = store.load(self.release_id)
        current = store.load(self.release_id)
        current["next_action"] = "advance"
        store.update(current, "advance")
        with self.assertRaises(LifecycleError) as context:
            store.save(stale)
        self.assertEqual(context.exception.code, "lifecycle_state_cas_conflict")

    def test_advance_requires_complete_worker_identity_and_uses_core_begin_work(self):
        self.engine.lifecycle_start(self.release_id)
        with self.assertRaises(LifecycleError) as context:
            self.engine.lifecycle_advance(self.release_id, worker="worker")
        self.assertEqual(context.exception.code, "worker_dispatch_identity_incomplete")
        advanced = self.engine.lifecycle_advance(
            self.release_id, worker="worker", invocation_id="invocation",
            attempt_id="attempt", status="WAITING_INTERNAL",
        )
        self.assertEqual(advanced["status"], "WAITING_INTERNAL")
        self.assertEqual(advanced["current_worker"], "worker")

    def test_evidence_v2_rejects_reviewer_bound_to_a_different_qa_sha(self):
        qa_sha = "a" * 40
        evidence = {
            "Schema-Version": "2", "Release-ID": self.release_id, "Tier": "3",
            "Task-Branch": "feat/v0.5.0-harness-fixture", "Base-SHA": "b" * 40,
            "QA-SHA": qa_sha, "Stage": "PACKAGE_REVIEW_PENDING", "Gate-1": "APPROVED",
            "Gate-2": "APPROVED", "Next-Action": "RELEASE_SIGNOFF",
            "Reviewer": [
                f"id=security; perspective=Security; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=reliability; perspective=Reliability; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=maintainability; perspective=Maintainability; verdict=APPROVED; qa-sha={'c' * 40}",
            ],
            "Verification": [f"id=unit; command=python -m unittest; result=PASS; exit-code=0; qa-sha={qa_sha}"],
        }
        with self.assertRaisesRegex(ValueError, "evidence_v2_reviewer_shape"):
            self.engine._validate_evidence_v2(self.release_id, "", evidence)

    def test_release_signoff_parser_accepts_one_blank_line_before_evidence(self):
        signoff = self.release / "RELEASE_SIGNOFF.md"
        signoff.write_text(
            "## ForgeFlow Release Sign-off v1\n\n```text\nRelease-ID: sample\n```\n",
            encoding="utf-8",
        )
        self.assertIsNotNone(__import__("re").search(
            r"(?ms)^## ForgeFlow Release Sign-off v1\n(?:\n)?```text\n(.*?)^```\s*$",
            signoff.read_text(encoding="utf-8"),
        ))

    def test_complete_core_state_accepts_terminal_next_action(self):
        self.engine.lifecycle_start(self.release_id)
        controller = self.engine._core_controller(self.release_id)
        controller._update(lambda state: state["progress"].update(status="COMPLETE", last_checkpoint="C4", next_action="terminal"))
        self.assertNotIn(
            "lifecycle_completion_guard_unmet",
            self.engine._validate_lifecycle_state_for_audit(controller.state, None, True),
        )

    def test_evidence_v2_accepts_five_reviewers_and_package_review_next_action(self):
        qa_sha = "a" * 40
        evidence = {
            "Schema-Version": "2", "Release-ID": self.release_id, "Tier": "3",
            "Task-Branch": "codex/v0.3.8-feature", "Base-SHA": "b" * 40,
            "QA-SHA": qa_sha, "Stage": "PACKAGE_REVIEW_PENDING", "Gate-1": "APPROVED",
            "Gate-2": "APPROVED", "Next-Action": "PACKAGE_REVIEW",
            "Reviewer": [
                f"id=security; perspective=Security; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=reliability; perspective=Reliability; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=maintainability; perspective=Maintainability; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=prog1; perspective=Programming; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=prog2; perspective=Programming; verdict=APPROVED; qa-sha={qa_sha}",
            ],
            "Verification": [
                f"id=unit; command=python -m unittest; result=PASS; exit-code=0; qa-sha={qa_sha}; output-digest={'d' * 64}",
            ],
        }
        self.engine._validate_evidence_v2(self.release_id, "", evidence)

    def test_evidence_v2_rejects_missing_required_perspectives_or_duplicate_ids(self):
        qa_sha = "a" * 40
        evidence = {
            "Schema-Version": "2", "Release-ID": self.release_id, "Tier": "3",
            "Task-Branch": "feat/valid", "Base-SHA": "b" * 40,
            "QA-SHA": qa_sha, "Stage": "PACKAGE_REVIEW_PENDING", "Gate-1": "APPROVED",
            "Gate-2": "APPROVED", "Next-Action": "RELEASE_SIGNOFF",
            "Reviewer": [
                f"id=security; perspective=Security; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=reliability; perspective=Reliability; verdict=APPROVED; qa-sha={qa_sha}",
                f"id=other; perspective=Architecture; verdict=APPROVED; qa-sha={qa_sha}",
            ],
            "Verification": [f"id=unit; command=test; result=PASS; exit-code=0; qa-sha={qa_sha}"],
        }
        with self.assertRaisesRegex(ValueError, "evidence_v2_reviewer_identity"):
            self.engine._validate_evidence_v2(self.release_id, "", evidence)

        evidence["Reviewer"] = [
            f"id=same; perspective=Security; verdict=APPROVED; qa-sha={qa_sha}",
            f"id=same; perspective=Reliability; verdict=APPROVED; qa-sha={qa_sha}",
            f"id=same; perspective=Maintainability; verdict=APPROVED; qa-sha={qa_sha}",
        ]
        with self.assertRaisesRegex(ValueError, "evidence_v2_reviewer_duplicate"):
            self.engine._validate_evidence_v2(self.release_id, "", evidence)

    def test_lifecycle_package_review_rejects_evidence_branch_mismatch(self):
        self.engine.lifecycle_start(self.release_id)
        controller = self.engine._core_controller(self.release_id)
        controller._update(lambda s: s["identity"].update(branch="feat/original-branch"))
        qa_sha = "a" * 40
        qa_signoff = self.release / "QA_SIGNOFF.md"
        qa_signoff.write_text(f"""## ForgeFlow Evidence v2
```text
Schema-Version: 2
Release-ID: {self.release_id}
Tier: 3
Task-Branch: feat/different-branch
Base-SHA: {"b" * 40}
QA-SHA: {qa_sha}
Stage: PACKAGE_REVIEW_PENDING
Gate-1: APPROVED
Gate-2: APPROVED
Reviewer: id=security; perspective=Security; verdict=APPROVED; qa-sha={qa_sha}
Reviewer: id=reliability; perspective=Reliability; verdict=APPROVED; qa-sha={qa_sha}
Reviewer: id=maintainability; perspective=Maintainability; verdict=APPROVED; qa-sha={qa_sha}
Verification: id=unit; command=test; result=PASS; exit-code=0; qa-sha={qa_sha}
Next-Action: RELEASE_SIGNOFF
```
""", encoding="utf-8")
        with patch.object(self.engine, "_is_local_commit", return_value=True):
            with self.assertRaises(LifecycleError) as context:
                self.engine.lifecycle_package_review(self.release_id, qa_sha)
            self.assertEqual(context.exception.code, "evidence_branch_mismatch")

    def _setup_valid_qa_state(self, qa_sha="a" * 40):
        self.engine.lifecycle_start(self.release_id)
        controller = self.engine._core_controller(self.release_id)
        branch = controller.state["identity"].get("branch") or "main"
        qa_signoff = self.release / "QA_SIGNOFF.md"
        qa_signoff.write_text(f"""## ForgeFlow Evidence v2
```text
Schema-Version: 2
Release-ID: {self.release_id}
Tier: 3
Task-Branch: {branch}
Base-SHA: {"b" * 40}
QA-SHA: {qa_sha}
Stage: PACKAGE_REVIEW_PENDING
Gate-1: APPROVED
Gate-2: APPROVED
Reviewer: id=security; perspective=Security; verdict=APPROVED; qa-sha={qa_sha}
Reviewer: id=reliability; perspective=Reliability; verdict=APPROVED; qa-sha={qa_sha}
Reviewer: id=maintainability; perspective=Maintainability; verdict=APPROVED; qa-sha={qa_sha}
Verification: id=unit; command=test; result=PASS; exit-code=0; qa-sha={qa_sha}
Next-Action: RELEASE_SIGNOFF
```
""", encoding="utf-8")
        # Ensure DESIGN.md and COMPLETION_REPORT.md have valid structure
        (self.release / "DESIGN.md").write_text("# Design\n## Requirements Traceability Matrix (RTM)\n| REQ | Design |\n## Gate 1 Verdict\nAPPROVED\n", encoding="utf-8")
        (self.release / "COMPLETION_REPORT.md").write_text("# Completion Report\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5\n", encoding="utf-8")
        with patch.object(self.engine, "_is_local_commit", return_value=True):
            self.engine.lifecycle_package_review(self.release_id, qa_sha)

    def test_seal_rejects_missing_or_invalid_release_signoff(self):
        qa_sha = "a" * 40
        candidate_sha = "c" * 40
        self._setup_valid_qa_state(qa_sha)

        # 1. Missing RELEASE_SIGNOFF.md
        (self.release / "RELEASE_SIGNOFF.md").unlink(missing_ok=True)
        with patch.object(self.engine, "_is_local_commit", return_value=True), \
             patch.object(self.engine, "_has_v2_candidate_binding", return_value=True):
            with self.assertRaises(LifecycleError) as ctx:
                self.engine.lifecycle_seal(self.release_id, candidate_sha)
            self.assertEqual(ctx.exception.code, "release_signoff_unreadable")

        # 2. Malformed RELEASE_SIGNOFF.md
        (self.release / "RELEASE_SIGNOFF.md").write_text("invalid block", encoding="utf-8")
        with patch.object(self.engine, "_is_local_commit", return_value=True), \
             patch.object(self.engine, "_has_v2_candidate_binding", return_value=True):
            with self.assertRaises(LifecycleError) as ctx:
                self.engine.lifecycle_seal(self.release_id, candidate_sha)
            self.assertEqual(ctx.exception.code, "release_signoff_malformed")

        # 3. Not approved / Not GO
        manifest, _ = self.engine._package_manifest(self.release_id, self.release)
        (self.release / "RELEASE_SIGNOFF.md").write_text(f"""## ForgeFlow Release Sign-off v1
```text
Release-ID: {self.release_id}
Gate-3: REJECTED
User-Verdict: NO-GO
Package-Manifest-SHA256: {manifest}
```
""", encoding="utf-8")
        with patch.object(self.engine, "_is_local_commit", return_value=True), \
             patch.object(self.engine, "_has_v2_candidate_binding", return_value=True):
            with self.assertRaises(LifecycleError) as ctx:
                self.engine.lifecycle_seal(self.release_id, candidate_sha)
            self.assertEqual(ctx.exception.code, "release_signoff_not_approved")

        # 4. Manifest mismatch
        (self.release / "RELEASE_SIGNOFF.md").write_text(f"""## ForgeFlow Release Sign-off v1
```text
Release-ID: {self.release_id}
Gate-3: APPROVED
User-Verdict: GO
Package-Manifest-SHA256: {"0" * 64}
```
""", encoding="utf-8")
        with patch.object(self.engine, "_is_local_commit", return_value=True), \
             patch.object(self.engine, "_has_v2_candidate_binding", return_value=True):
            with self.assertRaises(LifecycleError) as ctx:
                self.engine.lifecycle_seal(self.release_id, candidate_sha)
            self.assertEqual(ctx.exception.code, "package_manifest_mismatch")

    def test_seal_succeeds_and_sets_package_sealed_status(self):
        qa_sha = "a" * 40
        candidate_sha = "c" * 40
        self._setup_valid_qa_state(qa_sha)

        manifest, _ = self.engine._package_manifest(self.release_id, self.release)
        (self.release / "RELEASE_SIGNOFF.md").write_text(f"""## ForgeFlow Release Sign-off v1
```text
Release-ID: {self.release_id}
Gate-3: APPROVED
User-Verdict: GO
Package-Manifest-SHA256: {manifest}
```
""", encoding="utf-8")

        with patch.object(self.engine, "_is_local_commit", return_value=True), \
             patch.object(self.engine, "_has_v2_candidate_binding", return_value=True):
            result = self.engine.lifecycle_seal(self.release_id, candidate_sha)

        self.assertEqual(result["status"], "PACKAGE_SEALED")
        self.assertEqual(result["stage"], "PACKAGE_SEALED")
        controller = self.engine._core_controller(self.release_id)
        self.assertEqual(controller.status.value, "PACKAGE_SEALED")
        self.assertEqual(controller.state["evidence"]["gate3"], "APPROVED")
        self.assertEqual(controller.state["evidence"]["package_seal"], "SEALED")

    def test_artifact_mutation_invalidates_seal(self):
        qa_sha = "a" * 40
        candidate_sha = "c" * 40
        self._setup_valid_qa_state(qa_sha)
        manifest, _ = self.engine._package_manifest(self.release_id, self.release)
        (self.release / "RELEASE_SIGNOFF.md").write_text(f"""## ForgeFlow Release Sign-off v1
```text
Release-ID: {self.release_id}
Gate-3: APPROVED
User-Verdict: GO
Package-Manifest-SHA256: {manifest}
```
""", encoding="utf-8")
        with patch.object(self.engine, "_is_local_commit", return_value=True), \
             patch.object(self.engine, "_has_v2_candidate_binding", return_value=True):
            self.engine.lifecycle_seal(self.release_id, candidate_sha)

        # Mutate a package file after sealing
        (self.release / "DESIGN.md").write_text("# Mutated Design\n## RTM\n## Gate 1\n", encoding="utf-8")

        # Now validate evidence
        controller = self.engine._core_controller(self.release_id)
        evidence = self.engine._parse_evidence_v2((self.release / "QA_SIGNOFF.md").read_text(encoding="utf-8"))
        unmet = self.engine._validate_v2_package_evidence(self.release_id, self.release, controller.state, evidence, False)
        self.assertIn("package_manifest_mismatch", unmet)

        # Check controller state was unsealed and returned to PACKAGE_REVIEW_PENDING
        refreshed = self.engine._core_controller(self.release_id)
        self.assertEqual(refreshed.status.value, "PACKAGE_REVIEW_PENDING")
        self.assertEqual(refreshed.state["evidence"]["package_seal"], "UNSEALED")
        self.assertIsNone(refreshed.state["evidence"]["gate3"])

    def test_candidate_descendant_paths_evaluation(self):
        import subprocess
        release_id = "v0.5.0-descendant-test"
        qa_sha = "a" * 40
        candidate = "c" * 40
        current_head = "h" * 40

        # Simulate git command outputs:
        # candidate is local commit, qa_sha is local commit, rev-parse HEAD returns current_head,
        # merge-base returns 0 (is-ancestor), diff qa..candidate has allowed package file,
        # diff candidate..head has allowed lifecycle state file
        with patch.object(self.engine, "_is_local_commit", return_value=True):
            def mock_run(cmd, **kwargs):
                if cmd[3] == "rev-parse":
                    return subprocess.CompletedProcess(cmd, 0, stdout=f"{current_head}\n", stderr="")
                if cmd[3] == "merge-base":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                if cmd[3] == "diff":
                    range_spec = cmd[7]
                    if range_spec == f"{qa_sha}..{candidate}":
                        return subprocess.CompletedProcess(cmd, 0, stdout=f"docs/releases/{release_id}/PRD.md\0", stderr="")
                    elif range_spec == f"{candidate}..{current_head}":
                        return subprocess.CompletedProcess(cmd, 0, stdout=f".forgeflow/lifecycle/{release_id}.json\0", stderr="")
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")

            with patch("subprocess.run", side_effect=mock_run):
                disallowed = self.engine._candidate_disallowed_paths(release_id, qa_sha, candidate)
                self.assertEqual(disallowed, [])

            # Now test rejected when candidate..head has code changes
            def mock_run_bad_code(cmd, **kwargs):
                if cmd[3] == "rev-parse":
                    return subprocess.CompletedProcess(cmd, 0, stdout=f"{current_head}\n", stderr="")
                if cmd[3] == "merge-base":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                if cmd[3] == "diff":
                    range_spec = cmd[7]
                    if range_spec == f"{qa_sha}..{candidate}":
                        return subprocess.CompletedProcess(cmd, 0, stdout=f"docs/releases/{release_id}/PRD.md\0", stderr="")
                    elif range_spec == f"{candidate}..{current_head}":
                        return subprocess.CompletedProcess(cmd, 0, stdout="src/forgeflow/harness.py\0", stderr="")
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")

            with patch("subprocess.run", side_effect=mock_run_bad_code):
                disallowed = self.engine._candidate_disallowed_paths(release_id, qa_sha, candidate)
                self.assertEqual(disallowed, ["src/forgeflow/harness.py"])

    def test_evidence_v2_tier2_support(self):
        qa_sha = "a" * 40
        base_sha = "b" * 40
        tier2_text = f"""## ForgeFlow Evidence v2
```text
Schema-Version: 2
Release-ID: {self.release_id}
Tier: 2
Task-Branch: feat/sample-feature
Base-SHA: {base_sha}
QA-SHA: {qa_sha}
Stage: PACKAGE_REVIEW_PENDING
Gate-1: APPROVED
Gate-2: APPROVED
Next-Action: RELEASE_SIGNOFF
Reviewer: id=reviewer-1; perspective=Quality; verdict=APPROVED; qa-sha={qa_sha}
Verification: id=v1; command=pytest; result=PASS; exit-code=0; qa-sha={qa_sha}
```
"""
        evidence = self.engine._parse_evidence_v2(tier2_text)
        # Should not raise exception for Tier 2 with single reviewer
        self.engine._validate_evidence_v2(self.release_id, tier2_text, evidence)
        self.assertEqual(evidence["Tier"], "2")
        self.assertEqual(len(evidence["Reviewer"]), 1)

    def test_evidence_v2_friendly_error_messages(self):
        missing_block = "# Some title\nNo evidence block here\n"
        with self.assertRaises(ValueError) as ctx:
            self.engine._parse_evidence_v2(missing_block)
        self.assertIn("requires exactly one '## ForgeFlow Evidence v2'", str(ctx.exception))

        malformed_line = """## ForgeFlow Evidence v2
```text
Schema-Version 2
```
"""
        with self.assertRaises(ValueError) as ctx:
            self.engine._parse_evidence_v2(malformed_line)
        self.assertIn("lines in Evidence v2 must match 'Key: Value'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
