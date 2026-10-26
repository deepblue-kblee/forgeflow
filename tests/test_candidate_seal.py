import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from forgeflow.harness import HarnessEngine


class CandidateSealTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.release_id = "v0.16.1-test-seal"

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_root, capture_output=True, check=True)

        # Create initial commit
        readme = self.repo_root / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_root, capture_output=True, check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_candidate_allows_roadmap_update(self):
        engine = HarnessEngine(repo_root=self.repo_root)

        # Create release directory
        rel_dir = self.repo_root / "docs" / "releases" / self.release_id
        rel_dir.mkdir(parents=True, exist_ok=True)
        (rel_dir / "PRD.md").write_text("# PRD\n", encoding="utf-8")
        (rel_dir / "DESIGN.md").write_text("# DESIGN\n", encoding="utf-8")
        (rel_dir / "QA_SIGNOFF.md").write_text("# QA SIGNOFF\n", encoding="utf-8")
        (rel_dir / "ROADMAP.md").write_text("# ROADMAP\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA signoff commit"], cwd=self.repo_root, capture_output=True, check=True)

        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Now update ROADMAP.md and COMPLETION_REPORT.md
        (rel_dir / "ROADMAP.md").write_text("# ROADMAP (Updated checklist)\n", encoding="utf-8")
        (rel_dir / "COMPLETION_REPORT.md").write_text("# COMPLETION REPORT\n", encoding="utf-8")
        (rel_dir / "RELEASE_SIGNOFF.md").write_text("# RELEASE SIGNOFF\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit with updated roadmap"], cwd=self.repo_root, capture_output=True, check=True)

        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertEqual(disallowed, [], f"Disallowed paths found: {disallowed}")
        self.assertTrue(engine._has_v2_candidate_binding(self.release_id, qa_sha=qa_sha, candidate=candidate_sha))

    def test_candidate_rejects_unallowed_file(self):
        engine = HarnessEngine(repo_root=self.repo_root)
        rel_dir = self.repo_root / "docs" / "releases" / self.release_id
        rel_dir.mkdir(parents=True, exist_ok=True)
        (rel_dir / "QA_SIGNOFF.md").write_text("# QA\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA commit"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Update an unauthorized file
        src_file = self.repo_root / "src" / "code.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("print('unauthorized change after qa')\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Bad candidate commit"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertIsNotNone(disallowed)
        self.assertIn("src/code.py", disallowed)

    def test_candidate_allows_speckit_hybrid_documents(self):
        engine = HarnessEngine(repo_root=self.repo_root)

        pkg_dir = self.repo_root / "tasks" / "in-progress" / self.release_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
        (pkg_dir / "GATE1_REVIEW.md").write_text("# Gate 1\n", encoding="utf-8")
        (pkg_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        (pkg_dir / "tasks.md").write_text("# Tasks\n- [ ] task 1\n", encoding="utf-8")
        (pkg_dir / "QA_SIGNOFF.md").write_text("# QA\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA commit with speckit docs"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Update tasks.md to completed checklist and add CHANGE_NOTE.md
        (pkg_dir / "tasks.md").write_text("# Tasks\n- [x] task 1\n", encoding="utf-8")
        (pkg_dir / "CHANGE_NOTE.md").write_text("# Change Note\n", encoding="utf-8")
        (pkg_dir / "RELEASE_SIGNOFF.md").write_text("# Release Signoff\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit with updated tasks and change note"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertEqual(disallowed, [], f"Disallowed paths found: {disallowed}")
        self.assertTrue(engine._has_v2_candidate_binding(self.release_id, qa_sha=qa_sha, candidate=candidate_sha))

    def test_verify_stage2_gatekeeper_rejects_unsafe_release_id(self):
        from forgeflow.cli import verify_stage2_gatekeeper

        unsafe_pkg = self.repo_root / "tasks" / "in-progress" / "unsafe_id_without_semver"
        unsafe_pkg.mkdir(parents=True, exist_ok=True)
        (unsafe_pkg / "GATE1_REVIEW.md").write_text("APPROVED", encoding="utf-8")

        res = verify_stage2_gatekeeper(repo_root=self.repo_root, quiet=True)
        self.assertEqual(res, 1)

    def test_post_candidate_committed_completion_relocation_allowed(self):
        engine = HarnessEngine(repo_root=self.repo_root)

        pkg_dir = self.repo_root / "tasks" / "in-progress" / self.release_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
        (pkg_dir / "GATE1_REVIEW.md").write_text("# Gate 1\n", encoding="utf-8")
        (pkg_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        (pkg_dir / "tasks.md").write_text("# Tasks\n", encoding="utf-8")
        (pkg_dir / "QA_SIGNOFF.md").write_text("# QA\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA commit"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Candidate commit adds RELEASE_SIGNOFF.md
        (pkg_dir / "RELEASE_SIGNOFF.md").write_text("# Release Signoff\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Post-candidate: move from in-progress to completed, and add lifecycle JSON and session state
        completed_dir = self.repo_root / "tasks" / "completed" / self.release_id
        completed_dir.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.move(str(pkg_dir), str(completed_dir))

        lifecycle_file = self.repo_root / ".forgeflow" / "lifecycle" / f"{self.release_id}.json"
        lifecycle_file.parent.mkdir(parents=True, exist_ok=True)
        lifecycle_file.write_text('{"status": "COMPLETE"}\n', encoding="utf-8")

        session_state = self.repo_root / "docs" / "session-state" / "next-actions.md"
        session_state.parent.mkdir(parents=True, exist_ok=True)
        session_state.write_text("# Next Actions\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Completion relocation commit"], cwd=self.repo_root, capture_output=True, check=True)

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertEqual(disallowed, [], f"Disallowed paths found: {disallowed}")
        self.assertTrue(engine._has_v2_candidate_binding(self.release_id, qa_sha=qa_sha, candidate=candidate_sha))

    def test_post_candidate_relocation_fails_if_package_mutated(self):
        engine = HarnessEngine(repo_root=self.repo_root)

        pkg_dir = self.repo_root / "tasks" / "in-progress" / self.release_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")
        (pkg_dir / "QA_SIGNOFF.md").write_text("# QA\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA commit"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        (pkg_dir / "RELEASE_SIGNOFF.md").write_text("# Release Signoff\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Relocate but MUTATE spec.md
        completed_dir = self.repo_root / "tasks" / "completed" / self.release_id
        completed_dir.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.move(str(pkg_dir), str(completed_dir))
        (completed_dir / "spec.md").write_text("# Mutated Spec after Candidate!\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Relocation with mutation"], cwd=self.repo_root, capture_output=True, check=True)

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertIsNotNone(disallowed)
        self.assertNotEqual(disallowed, [])
        self.assertFalse(engine._has_v2_candidate_binding(self.release_id, qa_sha=qa_sha, candidate=candidate_sha))

    def test_post_candidate_relocation_fails_if_extra_file_added(self):
        engine = HarnessEngine(repo_root=self.repo_root)

        pkg_dir = self.repo_root / "tasks" / "in-progress" / self.release_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA commit"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        (pkg_dir / "RELEASE_SIGNOFF.md").write_text("# Release Signoff\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Relocate but ADD an extra file
        completed_dir = self.repo_root / "tasks" / "completed" / self.release_id
        completed_dir.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.move(str(pkg_dir), str(completed_dir))
        (completed_dir / "unauthorized_extra.md").write_text("# Extra\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Relocation with extra file"], cwd=self.repo_root, capture_output=True, check=True)

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertIsNotNone(disallowed)
        self.assertNotEqual(disallowed, [])
        self.assertFalse(engine._has_v2_candidate_binding(self.release_id, qa_sha=qa_sha, candidate=candidate_sha))

    def test_post_candidate_relocation_fails_if_source_files_remain(self):
        engine = HarnessEngine(repo_root=self.repo_root)

        pkg_dir = self.repo_root / "tasks" / "in-progress" / self.release_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA commit"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        (pkg_dir / "RELEASE_SIGNOFF.md").write_text("# Release Signoff\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Copy to completed instead of move, leaving source files behind
        completed_dir = self.repo_root / "tasks" / "completed" / self.release_id
        completed_dir.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copytree(str(pkg_dir), str(completed_dir), dirs_exist_ok=True)

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Copied without removing source"], cwd=self.repo_root, capture_output=True, check=True)

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertIsNotNone(disallowed)
        self.assertNotEqual(disallowed, [])
        self.assertFalse(engine._has_v2_candidate_binding(self.release_id, qa_sha=qa_sha, candidate=candidate_sha))

    def test_post_candidate_relocation_fails_if_unrelated_release(self):
        engine = HarnessEngine(repo_root=self.repo_root)

        pkg_dir = self.repo_root / "tasks" / "in-progress" / self.release_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "QA commit"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        (pkg_dir / "RELEASE_SIGNOFF.md").write_text("# Release Signoff\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # In post-candidate, relocate an unrelated release
        other_src = self.repo_root / "tasks" / "in-progress" / "v0.99.0-unrelated"
        other_src.mkdir(parents=True, exist_ok=True)
        (other_src / "spec.md").write_text("# Other Spec\n", encoding="utf-8")
        other_dst = self.repo_root / "tasks" / "completed" / "v0.99.0-unrelated"
        other_dst.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.move(str(other_src), str(other_dst))

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Relocate unrelated release"], cwd=self.repo_root, capture_output=True, check=True)

        disallowed = engine._candidate_disallowed_paths(self.release_id, qa_sha=qa_sha, candidate=candidate_sha)
        self.assertIsNotNone(disallowed)
        self.assertIn("tasks/completed/v0.99.0-unrelated/spec.md", disallowed)
        self.assertFalse(engine._has_v2_candidate_binding(self.release_id, qa_sha=qa_sha, candidate=candidate_sha))

    def test_full_seal_complete_commit_lifecycle_audit_flow(self):
        from unittest.mock import patch
        from forgeflow.runner import RuntimeTestRunner
        engine = HarnessEngine(repo_root=self.repo_root)

        base_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        pkg_dir = self.repo_root / "tasks" / "in-progress" / self.release_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        spec_content = "# Feature Specification\n\n## Overview\nTest Overview\n\n## Acceptance Criteria\n- [x] AC-1: Functional\n- [x] AC-2: Reliability\n- [x] AC-3: Security\n\n## Details\nAdditional specification details\n"
        (pkg_dir / "spec.md").write_text(spec_content, encoding="utf-8")
        (pkg_dir / "GATE1_REVIEW.md").write_text("# Gate 1 Review\nGate 1 Verdict: APPROVED\n", encoding="utf-8")
        plan_content = "# Architecture & Technical Plan\n\n## Architecture\nSystem design and architecture description.\n\n## Technical Details\nImplementation steps and verification strategy.\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10\n"
        (pkg_dir / "plan.md").write_text(plan_content, encoding="utf-8")
        tasks_content = "# Tasks Checklist\n\n- [x] task 1: setup\n- [x] task 2: implement\n- [x] task 3: test\n- [x] task 4: review\n- [x] task 5: complete\n"
        (pkg_dir / "tasks.md").write_text(tasks_content, encoding="utf-8")
        (pkg_dir / "PRD.md").write_text("# PRD\n\n## Functional Requirements\n- REQ-1: Core function\n", encoding="utf-8")
        (pkg_dir / "DESIGN.md").write_text("# Design\n## Requirements Traceability Matrix (RTM)\n| REQ | Design |\n| REQ-1 | Core Design |\n## Gate 1 Verdict\nAPPROVED\n", encoding="utf-8")
        (pkg_dir / "COMPLETION_REPORT.md").write_text("# COMPLETION REPORT\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5\n", encoding="utf-8")
        (pkg_dir / "RELEASE_NOTES.md").write_text("# Release Notes\n", encoding="utf-8")

        qa_signoff_dummy = f"""## ForgeFlow Evidence v2
```text
Schema-Version: 2
Release-ID: {self.release_id}
Tier: 2
Task-Branch: feat/{self.release_id}
Base-SHA: {base_sha}
QA-SHA: {"0" * 40}
Stage: PACKAGE_REVIEW_PENDING
Gate-1: APPROVED
Gate-2: APPROVED
Reviewer: id=lead; perspective=Quality; verdict=APPROVED; qa-sha={"0" * 40}
Verification: id=unit; command=test; result=PASS; exit-code=0; qa-sha={"0" * 40}
Next-Action: RELEASE_SIGNOFF
```
"""
        (pkg_dir / "QA_SIGNOFF.md").write_text(qa_signoff_dummy, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Pre QA commit"], cwd=self.repo_root, capture_output=True, check=True)
        qa_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        qa_signoff_real = f"""## ForgeFlow Evidence v2
```text
Schema-Version: 2
Release-ID: {self.release_id}
Tier: 2
Task-Branch: feat/{self.release_id}
Base-SHA: {base_sha}
QA-SHA: {qa_sha}
Stage: PACKAGE_REVIEW_PENDING
Gate-1: APPROVED
Gate-2: APPROVED
Reviewer: id=lead; perspective=Quality; verdict=APPROVED; qa-sha={qa_sha}
Verification: id=unit; command=test; result=PASS; exit-code=0; qa-sha={qa_sha}
Next-Action: RELEASE_SIGNOFF
```
"""
        (pkg_dir / "QA_SIGNOFF.md").write_text(qa_signoff_real, encoding="utf-8")

        # Compute manifest
        manifest, _ = engine._package_manifest(self.release_id, pkg_dir)
        (pkg_dir / "RELEASE_SIGNOFF.md").write_text(f"""## ForgeFlow Release Sign-off v1
```text
Release-ID: {self.release_id}
Gate-3: APPROVED
User-Verdict: GO
Package-Manifest-SHA256: {manifest}
```
""", encoding="utf-8")

        # Initialize lifecycle state to PACKAGE_REVIEW_PENDING
        engine.lifecycle_start(self.release_id)
        controller = engine._core_controller(self.release_id)
        controller._update(lambda state: (
            state["identity"].update(
                tier=2,
                branch=f"feat/{self.release_id}",
                base_sha=base_sha,
                qa_sha=qa_sha,
            ),
            state["progress"].update(
                status="PACKAGE_REVIEW_PENDING",
                last_checkpoint="C4",
            ),
            state["evidence"].update(
                qa_sha=qa_sha,
                gate1="APPROVED",
                gate2="APPROVED",
                reviewers={"lead": "APPROVED"},
                verification={"passed": True},
                strict_audit={"passed": True},
                package_manifest_sha256=manifest,
            )
        ))

        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Candidate commit"], cwd=self.repo_root, capture_output=True, check=True)
        candidate_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True).stdout.strip()

        # Step 2: Seal package
        seal_res = engine.lifecycle_seal(self.release_id, candidate_sha)
        self.assertEqual(seal_res["status"], "PACKAGE_SEALED")

        # Step 3: Complete lifecycle
        with patch.object(RuntimeTestRunner, "run_tests", return_value={"executed": True, "passed": True, "returncode": 0}):
            comp_res = engine.lifecycle_complete(self.release_id)
        self.assertEqual(comp_res.get("unmet_conditions", []), [])
        self.assertEqual(comp_res["status"], "COMPLETE")
        self.assertFalse(pkg_dir.exists())
        completed_dest = self.repo_root / "tasks" / "completed" / self.release_id
        self.assertTrue(completed_dest.exists())

        # Step 4: Commit completion relocation and lifecycle state
        subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Complete and relocate release"], cwd=self.repo_root, capture_output=True, check=True)

        # Step 5: Terminal lifecycle audit (Issue #5 regression test)
        with patch.object(RuntimeTestRunner, "run_tests", return_value={"executed": True, "passed": True, "returncode": 0}):
            audit = engine.check_lifecycle_evidence(self.release_id, strict=True, require_terminal_state=True)
        self.assertEqual(audit["unmet_conditions"], [], f"Audit failed: {audit['unmet_conditions']}")
        self.assertTrue(audit["ok"])


if __name__ == "__main__":
    unittest.main()
