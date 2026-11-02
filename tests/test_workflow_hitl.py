"""Design-only HITL checkpoint behavior."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forgeflow.workflow import Workflow, WorkflowError


class TestDesignCheckpoint(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.root = Path(self.temporary) / "repo"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Workflow Test")
        self.git("config", "user.email", "workflow@example.invalid")
        (self.root / "app.txt").write_text("before\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("switch", "-c", "task/example")
        self.workflow = Workflow(self.root, "design-check")

    def tearDown(self):
        shutil.rmtree(self.temporary)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if result.returncode:
            self.fail(result.stderr)
        return result.stdout.strip()

    def agreement(self):
        return {
            "scope": ["app.txt"],
            "acceptance": ["new content is delivered"],
            "plan": "Change app.txt",
            "checks": [[sys.executable, "-c", "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"]],
            "source": "task/example",
            "owner": "standalone",
            "target": "main",
            "integration": "local",
            "permissions": ["commit", "merge", "delete-branch"],
            "task_owned_branch": True,
        }

    def test_default_auto_flow_has_no_checkpoint(self):
        state = self.workflow.start(self.agreement())
        self.assertIsNone(state["hitl"])
        (self.root / "app.txt").write_text("after\n")
        self.assertEqual(self.workflow.verify()["status"], "ready")

    def test_design_checkpoint_pauses_before_verification(self):
        self.workflow.start(self.agreement(), hitl="design")
        state = self.workflow.check(summary={"spec": "short spec"})
        self.assertEqual(state["status"], "awaiting-user")
        self.assertEqual(state["pending"]["operation"], "checkpoint:design")
        self.assertEqual(state["checkpoints"]["design"]["summary"], {"spec": "short spec"})
        (self.root / "app.txt").write_text("after\n")
        with self.assertRaisesRegex(WorkflowError, "design checkpoint"):
            self.workflow.verify()
        with self.assertRaisesRegex(WorkflowError, "design checkpoint"):
            self.workflow.finalize()

        approved = self.workflow.continue_workflow("approved")
        self.assertEqual(approved["status"], "planned")
        self.assertEqual(approved["checkpoints"]["design"]["status"], "approved")
        self.assertEqual(self.workflow.verify()["status"], "ready")
        self.assertEqual(self.workflow.finalize()["status"], "cleaned")

    def test_revise_reopens_design_without_running_checks(self):
        self.workflow.start(self.agreement(), hitl="design")
        self.workflow.check()
        revised = self.workflow.revise("clarify acceptance")
        self.assertEqual(revised["status"], "planned")
        self.assertEqual(revised["checkpoints"]["design"]["status"], "changes-requested")
        self.assertEqual(revised["checkpoints"]["design"]["note"], "clarify acceptance")
        (self.root / "app.txt").write_text("after\n")
        with self.assertRaisesRegex(WorkflowError, "design checkpoint"):
            self.workflow.verify()
        self.workflow.check(summary={"revision": 2})
        self.assertEqual(self.workflow.continue_workflow()["status"], "planned")

    def test_stop_keeps_state_and_blocks_finalization(self):
        self.workflow.start(self.agreement(), hitl="design")
        self.workflow.check()
        stopped = self.workflow.stop("waiting for product input")
        self.assertEqual(stopped["status"], "stopped")
        self.assertIsNone(stopped["pending"])
        with self.assertRaisesRegex(WorkflowError, "design checkpoint"):
            self.workflow.finalize()
        self.assertEqual(json.loads(self.workflow.path.read_text())["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
