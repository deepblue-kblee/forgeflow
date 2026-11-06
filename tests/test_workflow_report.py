"""Status semantics and blocker guidance (issue #18 F, H)."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from forgeflow.workflow import Workflow


class TestWorkflowReport(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.root = Path(self.temporary) / "repo"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Report Test")
        self.git("config", "user.email", "report@example.invalid")
        (self.root / "app.txt").write_text("before\n")
        (self.root / "other.txt").write_text("other\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("switch", "-c", "task/report")

    def tearDown(self):
        shutil.rmtree(self.temporary)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if result.returncode:
            self.fail(result.stderr)
        return result.stdout.strip()

    def agreement(self, **overrides):
        result = {"scope": ["app.txt"], "acceptance": ["accepted"],
                  "plan": "plan", "checks": [[sys.executable, "-c", "pass"]],
                  "source": "task/report", "owner": "standalone", "integration": "none",
                  "permissions": ["commit"]}
        result.update(overrides)
        return result

    def test_planned_has_no_misleading_claim(self):
        wf = Workflow(self.root, "planned-demo")
        wf.start(self.agreement())
        report = wf.status()
        interp = report["interpretation"]
        self.assertEqual(interp["status"], "planned")
        self.assertFalse(interp["verification"]["recorded"])
        self.assertIn("does not indicate whether implementation has started", interp["status_note"])

    def test_ready_is_not_product_acceptance(self):
        wf = Workflow(self.root, "ready-demo")
        wf.start(self.agreement())
        (self.root / "app.txt").write_text("after\n")
        wf.verify()
        interp = wf.status()["interpretation"]
        self.assertTrue(interp["verification"]["passed"])
        self.assertTrue(interp["verification"]["fresh"])
        self.assertIn("does not mean product acceptance is complete", interp["status_note"])
        self.assertEqual(interp["acceptance"]["evidenced"], [])

    def test_stale_reports_reverify(self):
        wf = Workflow(self.root, "stale-demo")
        wf.start(self.agreement())
        (self.root / "app.txt").write_text("after\n")
        wf.verify()
        (self.root / "app.txt").write_text("after2\n")
        report = wf.status()
        self.assertEqual(report["status"], "verification-stale")
        self.assertFalse(report["interpretation"]["verification"]["fresh"])
        self.assertIn("re-verify", report["interpretation"]["status_note"])

    def test_blocker_has_structured_guidance(self):
        wf = Workflow(self.root, "blocker-demo")
        wf.start(self.agreement(permissions=[]))
        (self.root / "app.txt").write_text("after\n")
        wf.verify()
        result = wf.finalize()
        self.assertEqual(result["pending"]["operation"], "commit")
        self.assertIn("minimal_action", result["pending"])
        self.assertIn("state_command", result["pending"])
        self.assertIn("mutation_command", result["pending"])
        self.assertFalse(result["pending"]["requires_user"])

    def test_uncommitted_dependency_guidance(self):
        wf = Workflow(self.root, "dep-demo")
        wf.start(self.agreement())
        (self.root / "app.txt").write_text("after\n")
        (self.root / "other.txt").write_text("dirty outside scope\n")
        self.assertEqual(wf.verify()["status"], "ready")
        result = wf.finalize()
        self.assertEqual(result["pending"]["operation"], "verify-committed-inputs")
        self.assertIn("outside task scope", result["pending"]["reason"])

    def test_design_checkpoint_requires_user(self):
        wf = Workflow(self.root, "hitl-demo")
        wf.start(self.agreement(), hitl="design")
        result = wf.check(summary="review")
        self.assertEqual(result["pending"]["operation"], "checkpoint:design")
        self.assertTrue(result["pending"]["requires_user"])


if __name__ == "__main__":
    unittest.main()
