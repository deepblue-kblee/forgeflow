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


if __name__ == "__main__":
    unittest.main()
