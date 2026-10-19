import os
import tempfile
import unittest
from pathlib import Path

from forgeflow.lifecycle import LifecycleController, LifecycleStore, Status, TargetCheckpoint


class LifecycleIdempotencyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.release_id = "v0.16.1-test-idempotency"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_mark_package_review_pending_idempotent_and_update(self):
        store = LifecycleStore(self.repo_root, self.release_id)
        controller = LifecycleController(store)
        controller.store.create()

        # Approve Gate 1 and Gate 2
        controller.update_evidence(gate1="APPROVED", gate2="APPROVED")

        qa_sha_1 = "1111111111111111111111111111111111111111"
        res1 = controller.mark_package_review_pending(qa_sha=qa_sha_1)
        self.assertEqual(res1["progress"]["status"], Status.PACKAGE_REVIEW_PENDING.value)
        self.assertEqual(res1["identity"]["qa_sha"], qa_sha_1)

        # Calling again with identical qa_sha returns state without error
        res2 = controller.mark_package_review_pending(qa_sha=qa_sha_1)
        self.assertEqual(res2["progress"]["status"], Status.PACKAGE_REVIEW_PENDING.value)
        self.assertEqual(res2["identity"]["qa_sha"], qa_sha_1)

        # Calling again with updated qa_sha updates qa_sha without TransitionError
        qa_sha_2 = "2222222222222222222222222222222222222222"
        res3 = controller.mark_package_review_pending(qa_sha=qa_sha_2)
        self.assertEqual(res3["progress"]["status"], Status.PACKAGE_REVIEW_PENDING.value)
        self.assertEqual(res3["identity"]["qa_sha"], qa_sha_2)

    def test_seal_package_idempotent_and_update(self):
        store = LifecycleStore(self.repo_root, self.release_id)
        controller = LifecycleController(store)
        controller.store.create()

        controller.update_evidence(gate1="APPROVED", gate2="APPROVED", gate3="APPROVED")
        qa_sha = "1111111111111111111111111111111111111111"
        controller.mark_package_review_pending(qa_sha=qa_sha)

        candidate_sha_1 = "3333333333333333333333333333333333333333"
        manifest_1 = "a" * 64
        res1 = controller.seal_package(release_candidate_sha=candidate_sha_1, package_manifest_sha256=manifest_1)
        self.assertEqual(res1["progress"]["status"], Status.PACKAGE_SEALED.value)
        self.assertEqual(res1["identity"]["candidate_sha"], candidate_sha_1)
        self.assertEqual(res1["evidence"]["package_manifest_sha256"], manifest_1)

        # Calling again with identical values returns state without error
        res2 = controller.seal_package(release_candidate_sha=candidate_sha_1, package_manifest_sha256=manifest_1)
        self.assertEqual(res2["progress"]["status"], Status.PACKAGE_SEALED.value)
        self.assertEqual(res2["identity"]["candidate_sha"], candidate_sha_1)

        # Calling again with updated candidate sha / manifest updates without TransitionError
        candidate_sha_2 = "4444444444444444444444444444444444444444"
        manifest_2 = "b" * 64
        res3 = controller.seal_package(release_candidate_sha=candidate_sha_2, package_manifest_sha256=manifest_2)
        self.assertEqual(res3["progress"]["status"], Status.PACKAGE_SEALED.value)
        self.assertEqual(res3["identity"]["candidate_sha"], candidate_sha_2)
        self.assertEqual(res3["evidence"]["package_manifest_sha256"], manifest_2)


if __name__ == "__main__":
    unittest.main()
