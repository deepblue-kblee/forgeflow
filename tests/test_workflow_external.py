"""External commit/push result linking (issue #18 G)."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from forgeflow.workflow import Workflow, WorkflowError


class TestWorkflowExternal(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.root = Path(self.temporary) / "repo"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "External Test")
        self.git("config", "user.email", "external@example.invalid")
        (self.root / "app.txt").write_text("before\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("switch", "-c", "task/external")

    def tearDown(self):
        shutil.rmtree(self.temporary)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if result.returncode:
            self.fail(result.stderr)
        return result.stdout.strip()

    def make_remote(self, name):
        remote = Path(self.temporary) / name
        subprocess.run(["git", "init", "--bare", str(remote)], capture_output=True, text=True, check=True)
        self.git("remote", "add", "origin", str(remote))
        return remote

    def agreement(self, **overrides):
        result = {"scope": ["app.txt"], "acceptance": ["accepted"],
                  "plan": "plan", "checks": [[sys.executable, "-c", "pass"]],
                  "source": "task/external", "owner": "standalone", "integration": "none",
                  "permissions": ["commit", "push"], "remote": "origin"}
        result.update(overrides)
        return result

    def test_externally_committed_change_finalizes_without_new_commit(self):
        remote = self.make_remote("origin.git")
        wf = Workflow(self.root, "external-demo")
        wf.start(self.agreement())
        # The change is committed externally, outside the workflow.
        (self.root / "app.txt").write_text("after\n")
        self.git("add", "app.txt")
        self.git("commit", "-m", "external commit")
        committed = self.git("rev-parse", "HEAD")

        self.assertEqual(wf.verify()["status"], "ready")
        result = wf.finalize()
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["finalization_complete"])
        # No additional commit was created by the workflow.
        self.assertEqual(self.git("rev-parse", "HEAD"), committed)
        self.assertEqual([event["operation"] for event in result["operations"]], ["push"])
        # The external commit is observed on the actual remote.
        observed = self.git("ls-remote", "--heads", "origin", "refs/heads/task/external").split()[0]
        self.assertEqual(observed, committed)

    def test_different_remote_identity_is_rejected(self):
        first = self.make_remote("first.git")
        wf = Workflow(self.root, "remote-demo")
        wf.start(self.agreement())
        (self.root / "app.txt").write_text("after\n")
        self.git("add", "app.txt")
        self.git("commit", "-m", "external commit")
        self.assertEqual(wf.verify()["status"], "ready")
        # Point the recorded remote at a different destination.
        self.git("remote", "set-url", "origin", str(Path(self.temporary) / "second.git"))
        with self.assertRaises(WorkflowError):
            wf.finalize()
        # Nothing was published to the new destination.
        result = subprocess.run(["git", "-C", str(self.root), "ls-remote", "--heads", "origin"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
