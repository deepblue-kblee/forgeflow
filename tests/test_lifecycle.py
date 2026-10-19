import tempfile
import unittest
from pathlib import Path

from forgeflow.lifecycle import (
    AutonomousPolicy,
    CASConflict,
    LifecycleController,
    LifecycleStore,
    Status,
    TransitionError,
    ValidationError,
    digest,
    safe_record,
    validate_relative_path,
)


class LifecycleTests(unittest.TestCase):
    def test_interactive_default_and_atomic_state_digest(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-lifecycle-core")
            self.assertEqual(controller.status, Status.ACTIVE)
            state = controller.state
            self.assertEqual(state["progress"]["continuation_policy"], "interactive")
            self.assertEqual(state["state_digest"], controller.state["state_digest"])

            stale = controller.state
            controller.update_evidence(gate1="APPROVED")
            with self.assertRaises(CASConflict):
                controller.store.save(stale, expected_revision=stale["control"]["revision"],
                                      expected_digest=stale["state_digest"], fencing_epoch=0)

    def test_transition_guards_and_design_target(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-transition", target_checkpoint="design-only")
            with self.assertRaises(TransitionError):
                controller.transition(Status.WAITING_INTERNAL, reason="missing worker")
            controller.mark_target_reached()
            self.assertEqual(controller.status, Status.TARGET_REACHED)
            self.assertFalse(controller.can_dispatch("read_only"))

    def test_no_progress_blocks_on_fifth_meaningful_attempt(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-no-progress")
            for index in range(4):
                controller.record_attempt(stage_loop_fingerprint="stage-a", attempt_class="repair", failure=f"failure-{index}")
            self.assertEqual(controller.status, Status.ACTIVE)
            controller.record_attempt(stage_loop_fingerprint="stage-a", attempt_class="repair", failure="failure-4")
            self.assertEqual(controller.status, Status.BLOCKED)
            self.assertFalse(controller.can_dispatch("repository_write"))
            with self.assertRaises(TransitionError):
                controller.record_attempt(stage_loop_fingerprint="stage-a", attempt_class="repair", failure="failure-5")

    def test_state_writer_rejects_no_progress_count_above_limit(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-no-progress-state")
            state = controller.state
            state["control"]["no_progress"]["count"] = 6
            with self.assertRaises(ValidationError):
                controller.store.save(
                    state,
                    expected_revision=state["control"]["revision"],
                    expected_digest=state["state_digest"],
                    fencing_epoch=state["control"]["fencing_epoch"],
                )

    def test_completion_guard_requires_all_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-completion")
            with self.assertRaises(TransitionError):
                controller.transition(Status.COMPLETE, reason="premature")
            controller.update_evidence(
                gate1="APPROVED", gate2="APPROVED", gate3="APPROVED",
                reviewers={"security": "APPROVED", "reliability": "APPROVED", "maintainability": "APPROVED"},
                verification={"passed": True}, package_manifest_sha256="b" * 64, package_seal="SEALED",
            )
            controller._update(lambda state: state["identity"].update(qa_sha="c" * 40, candidate_sha="a" * 40))
            controller.transition(Status.COMPLETE, reason="all guards satisfied")
            self.assertEqual(controller.status, Status.COMPLETE)

    def test_qa_signoff_waits_for_package_review_then_release_seal(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.6.0-package-review")
            controller.update_evidence(
                gate1="APPROVED", gate2="APPROVED", gate3="APPROVED",
                reviewers={"security": "APPROVED", "reliability": "APPROVED", "maintainability": "APPROVED"},
                verification={"passed": True},
            )
            waiting = controller.mark_package_review_pending(qa_sha="a" * 40)
            self.assertEqual("PACKAGE_REVIEW_PENDING", waiting["progress"]["status"])
            sealed = controller.seal_package(release_candidate_sha="b" * 40, package_manifest_sha256="c" * 64)
            self.assertEqual("SEALED", sealed["evidence"]["package_seal"])
            self.assertEqual("a" * 40, sealed["identity"]["qa_sha"])
            self.assertEqual("b" * 40, sealed["identity"]["candidate_sha"])

    def test_safe_record_and_path_validation(self):
        value = safe_record({"summary": "token=super-secret", "stdout": "secret output", "nested": {"ok": True}})
        self.assertNotIn("stdout", value)
        self.assertNotIn("super-secret", str(value))
        redacted = safe_record({"apiKey": "TOPSECRET"})
        self.assertEqual(redacted["apiKey"], "[REDACTED]")
        event = safe_record({'summary': '{"token":"json-secret","safe":"ok"}'})
        self.assertNotIn("json-secret", str(event))
        self.assertIn("[REDACTED]", str(event))
        private = safe_record({'summary': '{"private_key":"private-secret"}'})
        self.assertNotIn("private-secret", str(private))
        self.assertEqual(validate_relative_path("docs/release/PRD.md"), "docs/release/PRD.md")
        with self.assertRaises(ValidationError):
            validate_relative_path("../outside")
        with self.assertRaises(ValidationError):
            validate_relative_path("/absolute")

    def test_lifecycle_parent_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            import os
            os.symlink(outside, str(Path(root) / ".forgeflow"))
            with self.assertRaises(ValidationError):
                LifecycleController.start(root, "v0.5.0-symlink")


if __name__ == "__main__":
    unittest.main()
