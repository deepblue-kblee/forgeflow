"""Unit tests for incremental release audit, early-exit scanner, and boundary allowlist."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from forgeflow.harness import HarnessEngine
from forgeflow.renderer import ReportRenderer
from forgeflow.review_scanner import ReviewScanner
from forgeflow.scanner import ReleaseScanner
from forgeflow.validator import ReleaseCheckResult, SelfGovernanceValidator


class IncrementalAuditTests(unittest.TestCase):
    def test_validator_classifies_forgeflow_path_as_repository_state(self):
        cls = SelfGovernanceValidator
        self.assertEqual(
            "repository-state",
            cls._classify_path(".forgeflow/lifecycle/v0.8.0-incremental-audit-boundary.json")
        )
        self.assertEqual(
            "repository-state",
            cls._classify_path(".forgeflow/something.lock")
        )
        self.assertEqual(
            "session-state",
            cls._classify_path("docs/session-state/next-actions.md")
        )

    def test_scanner_early_exit_latest_release(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel_dir = root / "docs" / "releases"
            rel_dir.mkdir(parents=True)

            (rel_dir / "v0.1.0").mkdir()
            (rel_dir / "v0.1.0" / "PRD.md").write_text("# PRD", encoding="utf-8")
            (rel_dir / "v0.2.0").mkdir()
            (rel_dir / "v0.2.0" / "PRD.md").write_text("# PRD", encoding="utf-8")
            (rel_dir / "v0.3.0").mkdir()  # empty dir without md
            (rel_dir / ".hidden").mkdir()

            latest = ReleaseScanner.get_latest_release(root)
            self.assertIsNotNone(latest)
            self.assertEqual("v0.2.0", latest.name)

    def test_review_scanner_prunes_ignored_directories(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_dir = root / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("print('hello')", encoding="utf-8")

            venv_dir = root / ".venv" / "lib"
            venv_dir.mkdir(parents=True)
            (venv_dir / "ignored.py").write_text("print('skip')", encoding="utf-8")

            git_dir = root / ".git" / "hooks"
            git_dir.mkdir(parents=True)
            (git_dir / "hook.py").write_text("print('hook')", encoding="utf-8")

            files = ReviewScanner.get_all_source_files(root)
            file_names = [f.name for f in files]
            self.assertIn("main.py", file_names)
            self.assertNotIn("ignored.py", file_names)
            self.assertNotIn("hook.py", file_names)

    def test_renderer_compact_archive_summary(self):
        r1 = ReleaseCheckResult(release_id="v0.1.0", path="p1", tier=3, passed=True, archived=True)
        r2 = ReleaseCheckResult(release_id="v0.2.0", path="p2", tier=3, passed=True, archived=True)
        r3 = ReleaseCheckResult(release_id="v0.3.0", path="p3", tier=3, passed=True, archived=False)
        r3.documents = {"PRD.md": {"exists": True, "passed": True}}

        rendered = ReportRenderer.render_terminal_report([r1, r2, r3])
        self.assertIn("과거 아카이브 릴리즈: 총 2개 ➔ 🟢 ALL PASSED", rendered)
        self.assertIn("📦 릴리즈: v0.3.0", rendered)
        self.assertNotIn("📦 릴리즈: v0.1.0", rendered)
        self.assertNotIn("📦 릴리즈: v0.2.0", rendered)

    def test_check_all_releases_marks_archived_releases(self):
        temp_dir = tempfile.TemporaryDirectory()
        try:
            root = Path(temp_dir.name)
            tasks_completed = root / "tasks" / "completed"
            tasks_completed.mkdir(parents=True)
            for i in range(3):
                p = tasks_completed / f"v0.{i}.0-test"
                p.mkdir()
                (p / "PRD.md").write_text("# PRD", encoding="utf-8")
                (p / "DESIGN.md").write_text("# DESIGN", encoding="utf-8")
                (p / "QA_SIGNOFF.md").write_text("# QA", encoding="utf-8")
                (p / "COMPLETION_REPORT.md").write_text("# DONE", encoding="utf-8")
            (root / ".forgeflow.json").write_text(json.dumps({"forgeflow_version": "0.1.0", "governance": {"tasks_dir": "tasks"}}), encoding="utf-8")
            engine = HarnessEngine(repo_root=root)
            results = engine.check_all_releases(strict=False)
            self.assertEqual(len(results), 3)
            archived = [r for r in results if getattr(r, "archived", False)]
            self.assertEqual(len(archived), 3)
        finally:
            temp_dir.cleanup()

    def test_candidate_binding_allowlist_permits_lifecycle_and_session_paths(self):
        engine = HarnessEngine(repo_root=Path("."))
        release_id = "v0.8.0-test"
        qa_sha = "a" * 40
        candidate = "b" * 40

        with patch("subprocess.run") as mock_run:
            # 1. mock HEAD == candidate
            # 2. mock diff between qa_sha and candidate
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=candidate),  # rev-parse HEAD
                MagicMock(
                    returncode=0,
                    stdout=f"docs/releases/{release_id}/PRD.md\0.forgeflow/lifecycle/{release_id}.json\0docs/session-state/next-actions.md\0"
                ),  # diff
            ]
            self.assertTrue(engine._has_v2_candidate_binding(release_id, qa_sha, candidate))


if __name__ == "__main__":
    unittest.main()
