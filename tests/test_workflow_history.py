"""Workflow history classification and lifecycle (issue #18 E): list, supersede, stop/resume."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from forgeflow.workflow import Workflow, WorkflowError, list_workflows


class TestWorkflowHistory(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.root = Path(self.temporary) / "repo"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "History Test")
        self.git("config", "user.email", "history@example.invalid")
        (self.root / "app.txt").write_text("before\n")
        (self.root / "other.txt").write_text("other\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("switch", "-c", "task/history")

    def tearDown(self):
        shutil.rmtree(self.temporary)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if result.returncode:
            self.fail(result.stderr)
        return result.stdout.strip()

    def agreement(self, scope, task_id):
        return {"scope": scope, "acceptance": ["accepted"],
                "plan": "plan", "checks": [[sys.executable, "-c", "pass"]],
                "source": "task/history", "owner": "standalone", "integration": "none",
                "permissions": ["commit"]}

    def test_list_classifies_active_and_historical(self):
        first = Workflow(self.root, "first")
        first.start(self.agreement(["app.txt"], "first"))
        second = Workflow(self.root, "second")
        second.start(self.agreement(["other.txt"], "second"))
        # first is completed, second stays active
        (self.root / "app.txt").write_text("after\n")
        first.verify()
        first.finalize()

        active = list_workflows(self.root)
        self.assertEqual([item["id"] for item in active], ["second"])
        all_items = {item["id"]: item for item in list_workflows(self.root, all_history=True)}
        self.assertEqual(all_items["first"]["kind"], "completed")
        self.assertEqual(all_items["second"]["kind"], "active")

    def test_supersede_links_successor_and_blocks_finalize(self):
        old = Workflow(self.root, "old")
        old.start(self.agreement(["app.txt"], "old"))
        new = Workflow(self.root, "new")
        new.start(self.agreement(["other.txt"], "new"))

        state = old.supersede("new", "replaced by a revised plan")
        self.assertEqual(state["status"], "superseded")
        self.assertEqual(state["superseded_by"]["id"], "new")
        with self.assertRaises(WorkflowError):
            old.finalize()

        items = {item["id"]: item for item in list_workflows(self.root, all_history=True)}
        self.assertEqual(items["old"]["kind"], "superseded")
        self.assertEqual(items["new"]["kind"], "active")

    def test_supersede_rejects_invalid_targets(self):
        old = Workflow(self.root, "old")
        old.start(self.agreement(["app.txt"], "old"))
        with self.assertRaises(WorkflowError):
            old.supersede("old", "self")
        with self.assertRaises(WorkflowError):
            old.supersede("missing", "not here")
        with self.assertRaises(WorkflowError):
            old.supersede("old", "")

    def test_completed_workflow_cannot_be_superseded(self):
        done = Workflow(self.root, "done")
        done.start(self.agreement(["app.txt"], "done"))
        (self.root / "app.txt").write_text("after\n")
        done.verify()
        done.finalize()
        other = Workflow(self.root, "other")
        other.start(self.agreement(["other.txt"], "other"))
        with self.assertRaises(WorkflowError):
            done.supersede("other", "replace evidence")

    def test_general_stop_resume_roundtrip(self):
        wf = Workflow(self.root, "pause-demo")
        wf.start(self.agreement(["app.txt"], "pause-demo"))
        (self.root / "app.txt").write_text("after\n")
        self.assertEqual(wf.verify()["status"], "ready")

        stopped = wf.stop("paused for review")
        self.assertEqual(stopped["status"], "stopped")
        self.assertIn("paused", stopped)
        with self.assertRaises(WorkflowError):
            wf.verify()
        with self.assertRaises(WorkflowError):
            wf.finalize()

        resumed = wf.resume()
        self.assertEqual(resumed["status"], "ready")
        self.assertNotIn("paused", resumed)
        self.assertEqual(wf.finalize()["status"], "ready")
        self.assertTrue(wf.load()["finalization_complete"])

    def test_stop_after_integration_is_rejected(self):
        local = {"scope": ["app.txt"], "acceptance": ["accepted"],
                 "plan": "plan", "checks": [[sys.executable, "-c", "pass"]],
                 "source": "task/history", "owner": "standalone", "integration": "local",
                 "target": "main", "permissions": ["commit", "merge", "delete-branch"],
                 "task_owned_branch": True}
        wf = Workflow(self.root, "integrated")
        wf.start(local)
        (self.root / "app.txt").write_text("after\n")
        wf.verify()
        self.assertEqual(wf.finalize()["status"], "cleaned")
        with self.assertRaises(WorkflowError):
            wf.stop("too late")


if __name__ == "__main__":
    unittest.main()
