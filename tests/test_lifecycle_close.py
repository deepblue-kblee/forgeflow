#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forgeflow.harness import HarnessEngine, LifecycleError
from forgeflow.lifecycle import Status
from forgeflow.validator import SelfGovernanceValidator
from forgeflow.cli import main


class TestLifecycleClose(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = self.temp_dir / "repo"
        self.repo_root.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Tester"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=self.repo_root, check=True)

        # Initial commit on main
        readme = self.repo_root / "README.md"
        readme.write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_root, check=True, capture_output=True)

        self.release_id = "v0.9.0-test-close"
        self.rel_dir = self.repo_root / "docs" / "releases" / self.release_id
        self.rel_dir.mkdir(parents=True, exist_ok=True)
        (self.rel_dir / "PRD.md").write_text("# PRD\n", encoding="utf-8")
        self.engine = HarnessEngine(repo_root=self.repo_root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_lifecycle(self, status="COMPLETE", branch=None):
        self.engine.lifecycle_start(self.release_id)
        controller = self.engine._core_controller(self.release_id)
        task_branch = branch or f"feat/{self.release_id}"
        controller._update(lambda state: state["identity"].update(branch=task_branch))
        if status == "COMPLETE":
            controller._update(lambda state: state["progress"].update(status="COMPLETE", stage="PACKAGE_SEALED"))
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-m", "Setup release"], cwd=self.repo_root, check=True, capture_output=True)

    def test_lifecycle_close_success_and_branch_cleanup(self):
        self._setup_lifecycle(status="COMPLETE")
        task_branch = f"feat/{self.release_id}"

        # Create task branch
        subprocess.run(["git", "branch", task_branch], cwd=self.repo_root, check=True)

        result = self.engine.lifecycle_close(self.release_id)

        self.assertTrue(result["ok"])
        self.assertEqual("CLOSED", result["status"])
        self.assertTrue(result["branch_cleaned"])
        self.assertEqual(task_branch, result["deleted_branch"])

        # Verify branch is deleted
        check_branch = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/{task_branch}"],
            cwd=self.repo_root,
            capture_output=True,
        )
        self.assertNotEqual(0, check_branch.returncode)

        # Idempotent call when branch is already deleted
        result2 = self.engine.lifecycle_close(self.release_id)
        self.assertTrue(result2["ok"])
        self.assertFalse(result2["branch_cleaned"])
        self.assertIsNone(result2["deleted_branch"])

    def test_lifecycle_close_fails_when_not_on_main(self):
        self._setup_lifecycle(status="COMPLETE")
        task_branch = f"feat/{self.release_id}"
        subprocess.run(["git", "checkout", "-b", task_branch], cwd=self.repo_root, check=True)

        with self.assertRaises(LifecycleError) as ctx:
            self.engine.lifecycle_close(self.release_id)
        self.assertEqual("not_on_main_branch", ctx.exception.code)

    def test_lifecycle_close_fails_when_not_complete(self):
        self._setup_lifecycle(status="ACTIVE")

        with self.assertRaises(LifecycleError) as ctx:
            self.engine.lifecycle_close(self.release_id)
        self.assertEqual("lifecycle_not_complete", ctx.exception.code)

    def test_lifecycle_close_fails_when_worktree_dirty(self):
        self._setup_lifecycle(status="COMPLETE")
        dirty_file = self.repo_root / "dirty.txt"
        dirty_file.write_text("dirty content", encoding="utf-8")

        with self.assertRaises(LifecycleError) as ctx:
            self.engine.lifecycle_close(self.release_id)
        self.assertEqual("worktree_not_clean", ctx.exception.code)

    def test_cli_lifecycle_close_text_and_json_output(self):
        self._setup_lifecycle(status="COMPLETE")
        task_branch = f"feat/{self.release_id}"
        subprocess.run(["git", "branch", task_branch], cwd=self.repo_root, check=True)

        # Text mode
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['lifecycle', 'close', '{self.release_id}', '--repo-root', '{self.repo_root}'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(0, res.returncode, f"CLI close failed: {res.stderr}")
        self.assertIn(f"✨ Release {self.release_id} closed:", res.stdout)

        # JSON mode
        cmd_json = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['lifecycle', 'close', '{self.release_id}', '--repo-root', '{self.repo_root}', '--json'])",
        ]
        res_json = subprocess.run(cmd_json, capture_output=True, text=True)
        self.assertEqual(0, res_json.returncode, f"CLI close --json failed: {res_json.stderr}")
        payload = json.loads(res_json.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual("CLOSED", payload["status"])

    def test_self_governance_early_bailout_on_complete(self):
        self._setup_lifecycle(status="COMPLETE")
        # On main branch, without matching task branch name or prd/design,
        # normal self-governance would fail. With early bailout, it immediately succeeds!
        passed, messages = SelfGovernanceValidator.validate(self.repo_root, self.release_id, "HEAD")
        self.assertTrue(passed)
        self.assertTrue(any("already COMPLETE" in msg for msg in messages))

    def test_lifecycle_close_fails_when_detached_head(self):
        self._setup_lifecycle(status="COMPLETE")
        subprocess.run(["git", "checkout", "--detach", "HEAD"], cwd=self.repo_root, check=True, capture_output=True)

        with self.assertRaises(LifecycleError) as ctx:
            self.engine.lifecycle_close(self.release_id)
        self.assertEqual("worktree_detached_head", ctx.exception.code)

    def test_lifecycle_close_fails_when_task_branch_checked_out_in_another_worktree(self):
        self._setup_lifecycle(status="COMPLETE")
        task_branch = f"feat/{self.release_id}"
        subprocess.run(["git", "branch", task_branch], cwd=self.repo_root, check=True)

        other_wt = self.temp_dir / "wt2"
        subprocess.run(["git", "worktree", "add", str(other_wt), task_branch], cwd=self.repo_root, check=True, capture_output=True)

        try:
            with self.assertRaises(LifecycleError) as ctx:
                self.engine.lifecycle_close(self.release_id)
            self.assertEqual("task_branch_checked_out_in_worktree", ctx.exception.code)
            self.assertIn("currently checked out at worktree", ctx.exception.message)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(other_wt)], cwd=self.repo_root, check=True, capture_output=True)

    def test_lifecycle_close_post_close_invariants(self):
        self._setup_lifecycle(status="COMPLETE")
        task_branch = f"feat/{self.release_id}"
        subprocess.run(["git", "branch", task_branch], cwd=self.repo_root, check=True)

        result = self.engine.lifecycle_close(self.release_id)
        self.assertTrue(result["ok"])
        self.assertEqual("CLOSED", result["status"])

        # Invariants: branch is main, not detached, and clean
        current_branch = self.engine._git_branch(self.repo_root)
        self.assertEqual("main", current_branch)
        self.assertFalse(self.engine._is_git_detached(self.repo_root))

        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo_root, capture_output=True, text=True, check=True)
        self.assertEqual("", status.stdout.strip())

    def test_lifecycle_close_without_separate_branch(self):
        # When auto_create_branch: false was used, work was directly on main
        self._setup_lifecycle(status="COMPLETE", branch="main")

        # Do NOT create feat/<release-id> branch
        result = self.engine.lifecycle_close(self.release_id)
        self.assertTrue(result["ok"])
        self.assertEqual("CLOSED", result["status"])
        self.assertFalse(result["branch_cleaned"])
        self.assertIsNone(result["deleted_branch"])

        # Invariants: branch is main, not detached, and clean
        current_branch = self.engine._git_branch(self.repo_root)
        self.assertEqual("main", current_branch)


if __name__ == "__main__":
    unittest.main()
