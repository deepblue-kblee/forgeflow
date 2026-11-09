"""Agreement amendment (issue #18 D): revise an in-progress plan without a new workflow."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from forgeflow.workflow import Workflow, WorkflowError


class TestWorkflowAmend(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.root = Path(self.temporary) / "repo"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Amend Test")
        self.git("config", "user.email", "amend@example.invalid")
        (self.root / "app.txt").write_text("before\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("switch", "-c", "task/amend")
        self.workflow = Workflow(self.root, "amend-demo")

    def tearDown(self):
        shutil.rmtree(self.temporary)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if result.returncode:
            self.fail(result.stderr)
        return result.stdout.strip()

    def check(self, content):
        return [sys.executable, "-c", "from pathlib import Path; assert Path('app.txt').read_text() == %r" % content]

    def agreement(self, **overrides):
        result = {"scope": ["app.txt"], "acceptance": ["app contains the new text"],
                  "plan": "Change app.txt", "checks": [self.check("after\n")],
                  "source": "task/amend", "owner": "standalone", "integration": "none",
                  "permissions": ["commit"]}
        result.update(overrides)
        return result

    def test_amend_revises_checks_without_a_new_workflow(self):
        self.workflow.start(self.agreement())
        (self.root / "app.txt").write_text("after\n")
        self.assertEqual(self.workflow.verify()["status"], "ready")

        state = self.workflow.amend(self.agreement(checks=[self.check("after2\n")],
                                                  acceptance=["app contains after2"]),
                                    reason="acceptance refined", impact="verification reruns")
        self.assertEqual(state["status"], "planned")
        self.assertIsNone(state["verification"])
        self.assertEqual(len(state["amendments"]), 1)
        self.assertEqual(state["amendments"][0]["reason"], "acceptance refined")

        (self.root / "app.txt").write_text("after2\n")
        self.assertEqual(self.workflow.verify()["status"], "ready")
        self.assertEqual(self.workflow.finalize()["status"], "ready")
        self.assertTrue(self.workflow.load()["finalization_complete"])

    def test_amend_preserves_previous_agreement_history(self):
        self.workflow.start(self.agreement())
        original = self.workflow.load()["agreement"]
        self.workflow.amend(self.agreement(checks=[self.check("after2\n")]),
                            reason="scope", impact="recheck")
        state = self.workflow.load()
        self.assertEqual(state["amendments"][0]["before"], original)
        self.assertEqual(state["agreement"]["checks"], [self.check("after2\n")])

    def test_amend_rejects_authority_or_repository_change(self):
        self.workflow.start(self.agreement())
        for field, value in [("owner", "host"), ("source", "other"), ("target", "other"),
                             ("permissions", ["push"]), ("integration", "local")]:
            with self.assertRaises(WorkflowError):
                self.workflow.amend(self.agreement(**{field: value}), reason="x", impact="y")

    def test_amend_rejects_while_design_checkpoint_is_pending(self):
        self.workflow.start(self.agreement(), hitl="design")
        self.workflow.check(summary="review")
        with self.assertRaises(WorkflowError):
            self.workflow.amend(self.agreement(), reason="x", impact="y")

    def test_amend_requires_reason_and_impact(self):
        self.workflow.start(self.agreement())
        with self.assertRaises(WorkflowError):
            self.workflow.amend(self.agreement(), reason="", impact="y")
        with self.assertRaises(WorkflowError):
            self.workflow.amend(self.agreement(), reason="x", impact="")

    def test_amend_completed_workflow_is_blocked(self):
        self.workflow.start(self.agreement())
        (self.root / "app.txt").write_text("after\n")
        self.workflow.verify()
        self.assertEqual(self.workflow.finalize()["status"], "ready")
        self.assertTrue(self.workflow.load()["finalization_complete"])
        with self.assertRaisesRegex(WorkflowError, "historical evidence"):
            self.workflow.amend(self.agreement(), reason="x", impact="y")


if __name__ == "__main__":
    unittest.main()
