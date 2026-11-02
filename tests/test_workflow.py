"""Behavioral coverage for the default workflow (real disposable Git repos)."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from forgeflow.workflow import Workflow, WorkflowError, add_parser, handle_command, _git


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.root = Path(self.temporary) / "repo"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Workflow Test")
        self.git("config", "user.email", "workflow@example.invalid")
        (self.root / "app.txt").write_text("before\n")
        (self.root / "other.txt").write_text("preserve\n")
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("switch", "-c", "task/example")
        self.workflow = Workflow(self.root, "small-change")

    def tearDown(self):
        shutil.rmtree(self.temporary)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        if result.returncode:
            self.fail(result.stderr)
        return result.stdout.strip()

    def agreement(self, **overrides):
        result = {"scope": ["app.txt"], "acceptance": ["new content is delivered"],
                  "plan": "Change app.txt and verify its content", "checks": [[sys.executable, "-c", "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"]],
                  "source": "task/example", "owner": "standalone", "target": "main",
                  "integration": "local", "permissions": ["commit", "merge", "delete-branch"],
                  "task_owned_branch": True}
        result.update(overrides)
        return result

    def prepare(self, **overrides):
        self.workflow.start(self.agreement(**overrides))
        (self.root / "app.txt").write_text("after\n")
        self.assertEqual(self.workflow.verify()["status"], "ready")

    def test_small_change_completes_without_signoff_documents_or_pr(self):
        self.prepare()
        result = self.workflow.finalize()
        self.assertEqual(result["status"], "cleaned")
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual(self.git("show", "main:app.txt"), "after")
        self.assertNotIn("task/example", self.git("branch", "--list"))
        self.assertFalse((self.root / "tasks").exists())
        self.assertEqual(self.workflow.finalize()["status"], "cleaned")

    def test_governance_only_never_commits_merges_or_deletes(self):
        self.prepare(permissions=[])
        result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "commit")
        self.assertEqual(self.git("show", "main:app.txt"), "before")
        self.assertEqual(self.git("branch", "--show-current"), "task/example")
        self.assertIn("task/example", self.git("branch", "--list"))

    def test_host_never_creates_branches_or_runs_git_writes(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"governance": {"auto_create_branch": True}}))
        self.prepare(owner="host")
        branches = self.git("branch", "--list")
        result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "commit")
        self.assertEqual(self.git("branch", "--list"), branches)
        self.assertEqual(self.git("show", "HEAD:app.txt"), "before")

    def test_unrelated_dirty_and_staged_content_is_preserved(self):
        (self.root / "other.txt").write_text("user staged\n")
        self.git("add", "other.txt")
        (self.root / "unrelated.txt").write_text("untracked user work\n")
        self.prepare(verification_paths=["app.txt"])
        self.workflow.finalize()
        self.assertEqual((self.root / "other.txt").read_text(), "user staged\n")
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "other.txt")
        self.assertEqual(self.git("show", "main:other.txt"), "preserve")
        self.assertEqual((self.root / "unrelated.txt").read_text(), "untracked user work\n")

    def test_preexisting_scope_changes_need_explicit_inclusion(self):
        (self.root / "app.txt").write_text("existing\n")
        with self.assertRaisesRegex(WorkflowError, "pre-existing"):
            self.workflow.start(self.agreement())
        state = self.workflow.start(self.agreement(include_existing_changes=True))
        self.assertEqual(state["initial_changes"], ["app.txt"])

    def test_project_checks_cannot_be_removed_by_task(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"checks": [[sys.executable, "-c", "raise SystemExit(7)"]]}}))
        self.workflow.start(self.agreement(checks=[], verification_note="task has no checks"))
        result = self.workflow.verify()
        self.assertEqual(result["status"], "verification-failed")
        self.assertEqual(result["verification"]["results"][0]["returncode"], 7)
        self.assertEqual(self.workflow.finalize()["pending"]["operation"], "verify")

    def test_failed_or_timeout_checks_invalidate_old_pass(self):
        self.prepare(checks=[[sys.executable, "-c", "import os; assert os.environ.get('WORKFLOW_CHECK_FAIL') != 'yes'"]])
        with patch.dict(os.environ, {"WORKFLOW_CHECK_FAIL": "yes"}):
            result = self.workflow.verify()
        self.assertFalse(result["verification"]["passed"])
        self.assertEqual(self.workflow.finalize()["pending"]["operation"], "verify")

    def test_content_and_declared_environment_changes_make_pass_stale(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"environment": ["WORKFLOW_INPUT"]}}))
        self.prepare()
        with patch.dict(os.environ, {"WORKFLOW_INPUT": "new-environment"}):
            self.assertEqual(self.workflow.status()["status"], "verification-stale")
        (self.root / "app.txt").write_text("changed after verification\n")
        self.assertEqual(self.workflow.finalize()["pending"]["operation"], "verify")

    def test_check_that_changes_inputs_cannot_claim_ready(self):
        self.workflow.start(self.agreement(checks=[[sys.executable, "-c", "from pathlib import Path; Path('app.txt').write_text('generated')"]]))
        result = self.workflow.verify()
        self.assertEqual(result["status"], "verification-stale")
        self.assertFalse(result["verification"]["passed"])

    def test_cleanup_failure_resumes_cleanup_without_repeating_merge(self):
        self.prepare()
        def fail_cleanup(root, *args, **kwargs):
            if args[:2] == ("branch", "-d"):
                raise WorkflowError("simulated host branch lock")
            return _git(root, *args, **kwargs)
        with patch("forgeflow.workflow._git", side_effect=fail_cleanup):
            with self.assertRaisesRegex(WorkflowError, "simulated"):
                self.workflow.finalize()
        self.assertEqual(self.workflow.load()["status"], "integrated")
        integrated = self.git("rev-parse", "main")
        result = self.workflow.finalize()
        self.assertEqual(result["status"], "cleaned")
        self.assertEqual(self.git("rev-parse", "main"), integrated)

    def test_crash_after_merge_recovers_from_git_before_state_receipt(self):
        self.prepare()
        recover = self.workflow._recover_integration
        calls = []
        def crash_after_git(state):
            calls.append(True)
            if state.get("merge_intent") and not state.get("integration"):
                raise WorkflowError("crash after successful merge")
            return recover(state)
        with patch.object(self.workflow, "_recover_integration", side_effect=crash_after_git):
            with self.assertRaisesRegex(WorkflowError, "crash"):
                self.workflow.finalize()
        self.assertEqual(self.git("show", "main:app.txt"), "after")
        result = self.workflow.finalize()
        self.assertEqual(result["status"], "cleaned")
        self.assertTrue(result["integration"]["recovered"])

    def test_diverged_target_requires_reconciliation_and_reverification(self):
        self.prepare()
        self.git("commit", "-am", "task change")
        self.git("switch", "main")
        (self.root / "other.txt").write_text("target movement\n")
        self.git("commit", "-am", "target moved")
        self.git("switch", "task/example")
        result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "reconcile")
        self.assertEqual(self.git("branch", "--show-current"), "task/example")

    def test_host_receipt_is_checked_against_observed_git(self):
        self.prepare(owner="host", permissions=["merge"])
        self.git("commit", "-am", "host implementation")
        pending = self.workflow.finalize()
        self.assertEqual(pending["pending"]["operation"], "merge")
        source = self.git("rev-parse", "HEAD")
        receipt = {"operation": "merge", "repository": str(self.workflow.root), "source": "task/example", "target": "main",
                   "source_commit": source, "tool": "test-host", "evidence": "git execution record"}
        with self.assertRaisesRegex(WorkflowError, "does not contain"):
            self.workflow.finalize(receipt)
        self.git("update-ref", "refs/heads/main", source)
        result = self.workflow.finalize(receipt)
        self.assertEqual(result["status"], "integrated")
        self.assertEqual(result["cleanup"]["status"], "not-requested")

    def test_host_cleanup_cannot_claim_success_from_unobservable_receipt(self):
        self.prepare(owner="host", permissions=["merge", "host-cleanup"])
        self.git("commit", "-am", "host implementation")
        self.workflow.finalize()
        source = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/heads/main", source)
        receipt = {"operation": "merge", "repository": str(self.workflow.root), "source": "task/example", "target": "main",
                   "source_commit": source, "tool": "test-host", "evidence": "git execution record"}
        result = self.workflow.finalize(receipt)
        self.assertEqual(result["pending"]["operation"], "host-cleanup")
        receipt["operation"] = "host-cleanup"
        with self.assertRaisesRegex(WorkflowError, "cannot be independently observed"):
            self.workflow.finalize(receipt)
        self.assertEqual(self.workflow.load()["status"], "integrated")

    def test_same_version_runtime_drift_is_not_silently_adopted(self):
        self.prepare()
        from forgeflow.runtime import RuntimeBaselineError
        with patch("forgeflow.runtime.assert_runtime", side_effect=RuntimeBaselineError("different bytes; run snapshot command")):
            self.assertEqual(self.workflow.status()["status"], "baseline-drift")
            with self.assertRaisesRegex(RuntimeBaselineError, "different bytes"):
                self.workflow.finalize()

    def test_source_branch_with_out_of_scope_commits_cannot_be_merged(self):
        (self.root / "other.txt").write_text("unapproved branch history\n")
        self.git("commit", "-am", "unapproved")
        self.prepare()
        with self.assertRaisesRegex(WorkflowError, "outside the agreed"):
            self.workflow.finalize()
        self.assertEqual(self.git("show", "main:other.txt"), "preserve")

    def test_symlink_scope_and_state_paths_are_rejected(self):
        (self.root / "link").symlink_to(Path(self.temporary))
        with self.assertRaises(WorkflowError):
            self.workflow.start(self.agreement(scope=["link/other.txt"]))
        with self.assertRaises(WorkflowError):
            Workflow(self.root, "../escape")

    def test_cli_parsing_and_machine_readable_result(self):
        agreement = self.root / "agreement.json"
        agreement.write_text(json.dumps(self.agreement()))
        parser = argparse.ArgumentParser()
        add_parser(parser.add_subparsers(dest="command"))
        args = parser.parse_args(["workflow", "start", "cli-task", "--agreement", str(agreement), "--repo-root", str(self.root), "--json"])
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = handle_command(args)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stream.getvalue())["status"], "planned")

    def test_literal_git_pathspec_cannot_stage_other_paths(self):
        magic = ":(glob)*"
        self.workflow.start(self.agreement(scope=[magic], verification_paths=[magic], checks=[[sys.executable, "-c", "pass"]], integration="none"))
        (self.root / magic).write_text("literal filename\n")
        (self.root / "other.txt").write_text("user work\n")
        self.assertEqual(self.workflow.verify()["status"], "ready")
        self.workflow.finalize()
        self.assertEqual(self.git("show", "HEAD:other.txt"), "preserve")
        self.assertEqual(self.git("show", "HEAD:" + magic), "literal filename")

    def test_merge_uses_accepted_commit_and_blocks_source_ref_race(self):
        self.prepare()
        def move_source(root, *args, **kwargs):
            result = _git(root, *args, **kwargs)
            if args == ("switch", "main"):
                current = _git(root, "rev-parse", "refs/heads/task/example")
                tree = _git(root, "rev-parse", current + "^{tree}")
                moved = _git(root, "commit-tree", tree, "-p", current, "-m", "concurrent source movement")
                _git(root, "update-ref", "refs/heads/task/example", moved)
            return result
        with patch("forgeflow.workflow._git", side_effect=move_source):
            result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "verify")
        self.assertIn("source branch moved", result["pending"]["reason"])
        self.assertEqual(self.git("branch", "--show-current"), "task/example")
        self.assertEqual(self.git("show", "main:app.txt"), "before")

    def test_merge_recovery_rejects_unverified_target_tree(self):
        self.prepare()
        recover = self.workflow._recover_integration
        def crash_after_git(state):
            if state.get("merge_intent") and not state.get("integration"):
                raise WorkflowError("crash after merge")
            return recover(state)
        with patch.object(self.workflow, "_recover_integration", side_effect=crash_after_git):
            with self.assertRaisesRegex(WorkflowError, "crash"):
                self.workflow.finalize()
        (self.root / "other.txt").write_text("concurrent integration\n")
        self.git("commit", "-am", "other actor changed target")
        with self.assertRaisesRegex(WorkflowError, "additional unverified"):
            self.workflow.finalize()
        self.assertIsNone(self.workflow.load()["integration"])

    def test_commit_hook_changes_require_new_verification_before_merge(self):
        self.prepare()
        hook = self.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nprintf 'hook changed\\n' > app.txt\n")
        hook.chmod(0o755)
        result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "verify")
        self.assertEqual(self.git("show", "main:app.txt"), "before")

    def test_explicit_verification_inputs_reuse_pass_for_metadata_only_edits(self):
        (self.root / "tasks.md").write_text("- [ ] complete\n")
        self.git("add", "tasks.md")
        self.git("commit", "-m", "planning metadata")
        self.git("update-ref", "refs/heads/main", "HEAD")
        self.prepare(scope=["app.txt", "tasks.md"], verification_paths=["app.txt"])
        (self.root / "tasks.md").write_text("- [x] complete\n")
        self.assertEqual(self.workflow.status()["status"], "ready")
        self.assertEqual(self.workflow.finalize()["status"], "cleaned")

    def test_project_verification_dependencies_cannot_be_removed(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"verification_paths": ["other.txt"]}}))
        self.prepare(verification_paths=["app.txt"])
        (self.root / "other.txt").write_text("dependency changed\n")
        self.assertEqual(self.workflow.status()["status"], "verification-stale")

    def test_new_workflow_cannot_replace_an_active_runtime(self):
        self.prepare()
        baseline = (self.root / ".forgeflow/runtime.json").read_bytes()
        from forgeflow.runtime import RuntimeBaselineError
        with patch("forgeflow.runtime.assert_runtime", side_effect=RuntimeBaselineError("different source package")):
            with self.assertRaisesRegex(RuntimeBaselineError, "different source"):
                Workflow(self.root, "second-task").start(self.agreement(include_existing_changes=True))
        self.assertEqual((self.root / ".forgeflow/runtime.json").read_bytes(), baseline)

    def test_ready_only_finalization_is_complete_without_claiming_merge(self):
        self.prepare(integration="none", permissions=["commit"])
        result = self.workflow.finalize()
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["finalization_complete"])
        self.assertIsNone(result["integration"])
        self.assertFalse(self.workflow.verify()["finalization_complete"])

    def test_explicit_push_is_observed_on_remote_without_merging(self):
        remote = Path(self.temporary) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        self.git("remote", "add", "origin", str(remote))
        self.prepare(integration="none", permissions=["commit", "push"])
        result = self.workflow.finalize()
        self.assertTrue(result["finalization_complete"])
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/task/example").split()[0], self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("show", "main:app.txt"), "before")

    def test_failed_check_has_bounded_redacted_diagnostic_evidence(self):
        self.workflow.start(self.agreement(checks=[[sys.executable, "-c", "import os; print('failure: ' + os.environ['WORKFLOW_SECRET']); raise SystemExit(3)"]]))
        with patch.dict(os.environ, {"WORKFLOW_SECRET": "do-not-persist-this-value"}):
            result = self.workflow.verify()
        diagnostic = result["verification"]["results"][0]["diagnostic_excerpt"]
        self.assertIn("failure:", diagnostic)
        self.assertIn("[redacted]", diagnostic)
        self.assertNotIn("do-not-persist-this-value", diagnostic)

    def test_repository_root_scope_is_rejected(self):
        with self.assertRaisesRegex(WorkflowError, "repository root"):
            self.workflow.start(self.agreement(scope=["."]))

    def test_timeout_replaces_previous_pass_with_failed_evidence(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"governance": {"test_timeout_seconds": 2}}))
        self.workflow.start(self.agreement(checks=[[sys.executable, "-c", "import time; print('waiting', flush=True); time.sleep(0.2)"]]))
        self.assertEqual(self.workflow.verify()["status"], "ready")
        config.write_text(json.dumps({"governance": {"test_timeout_seconds": 0.05}}))
        result = self.workflow.verify()
        self.assertEqual(result["status"], "verification-failed")
        self.assertFalse(result["verification"]["passed"])
        self.assertEqual(result["verification"]["results"][0]["error"], "TimeoutExpired")

    def test_repository_lock_rejects_concurrent_state_writers(self):
        self.prepare()
        with self.workflow.locked():
            with self.assertRaisesRegex(WorkflowError, "busy"):
                self.workflow.status()

    def test_failed_merge_restores_source_checkout_for_resumption(self):
        self.prepare()
        def fail_merge(root, *args, **kwargs):
            if args[:2] == ("merge", "--ff-only"):
                raise WorkflowError("simulated merge failure")
            return _git(root, *args, **kwargs)
        with patch("forgeflow.workflow._git", side_effect=fail_merge):
            result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "merge")
        self.assertEqual(self.git("branch", "--show-current"), "task/example")
        self.assertEqual(self.git("show", "main:app.txt"), "before")
        self.assertEqual(self.workflow.finalize()["status"], "cleaned")

    def test_pr_integration_requires_an_owner_that_can_consume_receipts(self):
        with self.assertRaisesRegex(WorkflowError, "requires owner=host"):
            self.workflow.start(self.agreement(integration="pr", owner="standalone"))
        state = self.workflow.start(self.agreement(integration="pr", owner="host"))
        self.assertEqual(state["agreement"]["owner"], "host")

    def test_uncommitted_verified_dependency_cannot_be_omitted_from_delivery(self):
        checks = [[sys.executable, "-c", "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'; assert Path('other.txt').read_text() == 'required dependency\\n'"]]
        self.workflow.start(self.agreement(checks=checks))
        (self.root / "app.txt").write_text("after\n")
        (self.root / "other.txt").write_text("required dependency\n")
        self.assertEqual(self.workflow.verify()["status"], "ready")
        result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "verify-committed-inputs")
        self.assertIn("other.txt", result["pending"]["reason"])
        self.assertEqual(self.git("show", "HEAD:app.txt"), "before")
        self.assertEqual(self.git("show", "main:other.txt"), "preserve")
        self.assertEqual((self.root / "other.txt").read_text(), "required dependency\n")

    def test_cleanup_rechecks_target_ancestry_despite_source_upstream(self):
        original = self.git("rev-parse", "main")
        self.prepare()
        def fail_cleanup(root, *args, **kwargs):
            if args[:2] == ("branch", "-d"):
                raise WorkflowError("cleanup deferred")
            return _git(root, *args, **kwargs)
        with patch("forgeflow.workflow._git", side_effect=fail_cleanup):
            with self.assertRaisesRegex(WorkflowError, "deferred"):
                self.workflow.finalize()
        accepted = self.git("rev-parse", "refs/heads/task/example")
        self.git("update-ref", "refs/remotes/origin/task/example", accepted)
        self.git("config", "remote.origin.url", str(Path(self.temporary) / "remote.git"))
        self.git("config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
        self.git("config", "branch.task/example.remote", "origin")
        self.git("config", "branch.task/example.merge", "refs/heads/task/example")
        self.git("update-ref", "refs/heads/main", original)
        result = self.workflow.finalize()
        self.assertEqual(result["pending"]["operation"], "verify-integration")
        self.assertFalse(result["finalization_complete"])
        self.assertEqual(self.git("rev-parse", "refs/heads/task/example"), accepted)

    def test_host_cannot_delegate_committed_changes_outside_scope(self):
        (self.root / "other.txt").write_text("unapproved source history\n")
        self.git("commit", "-am", "other work")
        self.prepare(owner="host")
        self.git("commit", "-am", "host task implementation")
        with self.assertRaisesRegex(WorkflowError, "outside the agreed"):
            self.workflow.finalize()
        self.assertIsNone(self.workflow.load().get("host_merge_intent"))
        self.assertEqual(self.git("show", "main:other.txt"), "preserve")

    def test_project_host_owner_rejects_standalone_agreement(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"owner": "host"}}))
        with self.assertRaisesRegex(WorkflowError, "declares host ownership"):
            self.workflow.start(self.agreement(owner="standalone"))
        self.assertEqual(self.workflow.start(self.agreement(owner="host"))["status"], "planned")

    def test_project_owner_change_blocks_preexisting_standalone_mutations(self):
        self.prepare()
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir(exist_ok=True)
        config.write_text(json.dumps({"workflow": {"owner": "host"}}))
        with self.assertRaisesRegex(WorkflowError, "declares host ownership"):
            self.workflow.finalize()
        self.assertEqual(self.git("show", "HEAD:app.txt"), "before")
        self.assertEqual(self.git("branch", "--show-current"), "task/example")

    def test_standalone_project_can_delegate_operations_to_host(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"owner": "standalone"}}))
        self.assertEqual(self.workflow.start(self.agreement(owner="host"))["agreement"]["owner"], "host")

    def test_verified_deletion_does_not_need_reverification_after_commit(self):
        self.workflow.start(self.agreement(checks=[[sys.executable, "-c", "from pathlib import Path; assert not Path('app.txt').exists()"]]))
        (self.root / "app.txt").unlink()
        self.assertEqual(self.workflow.verify()["status"], "ready")
        self.assertEqual(self.workflow.finalize()["status"], "cleaned")
        self.assertEqual(self.git("ls-tree", "main", "app.txt"), "")


if __name__ == "__main__":
    unittest.main()
