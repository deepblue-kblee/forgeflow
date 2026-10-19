import hashlib
import tempfile
import unittest
from pathlib import Path

from forgeflow.cli import verify_stage2_gatekeeper, main


class TestStage2Gatekeeper(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        # Create minimal tasks/in-progress directory
        self.tasks_dir = self.root / "tasks" / "in-progress"
        self.tasks_dir.mkdir(parents=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_gatekeeper_fails_when_no_active_package(self):
        code = verify_stage2_gatekeeper(self.root, quiet=True)
        self.assertEqual(code, 1)

    def test_gatekeeper_fails_when_gate1_review_missing(self):
        pkg = self.tasks_dir / "v0.1.0-feature"
        pkg.mkdir()
        code = verify_stage2_gatekeeper(self.root, quiet=True)
        self.assertEqual(code, 1)

    def test_gatekeeper_fails_when_gate1_not_approved(self):
        pkg = self.tasks_dir / "v0.1.0-feature"
        pkg.mkdir()
        (pkg / "GATE1_REVIEW.md").write_text("# Review\nStatus: REJECTED\n", encoding="utf-8")
        code = verify_stage2_gatekeeper(self.root, quiet=True)
        self.assertEqual(code, 1)

    def test_gatekeeper_passes_when_approved(self):
        pkg = self.tasks_dir / "v0.1.0-feature"
        pkg.mkdir()
        (pkg / "GATE1_REVIEW.md").write_text("# Review\nStatus: APPROVED\n", encoding="utf-8")
        code = verify_stage2_gatekeeper(self.root, quiet=True)
        self.assertEqual(code, 0)

    def test_gatekeeper_sha_integrity(self):
        pkg = self.tasks_dir / "v0.1.0-feature"
        pkg.mkdir()
        spec_content = "# Feature Spec\nDescription here.\n"
        (pkg / "spec.md").write_text(spec_content, encoding="utf-8")
        actual_hash = hashlib.sha256(spec_content.encode("utf-8")).hexdigest()

        # Approved with matching hash
        (pkg / "GATE1_REVIEW.md").write_text(
            f"# Review\nStatus: APPROVED\nSpec SHA256: {actual_hash}\n",
            encoding="utf-8",
        )
        self.assertEqual(verify_stage2_gatekeeper(self.root, quiet=True), 0)

        # Alter spec content -> should fail closed
        (pkg / "spec.md").write_text("# Tampered Spec Content\n", encoding="utf-8")
        self.assertEqual(verify_stage2_gatekeeper(self.root, quiet=True), 1)

    def test_cli_check_stage2(self):
        pkg = self.tasks_dir / "v0.1.0-feature"
        pkg.mkdir()
        (pkg / "GATE1_REVIEW.md").write_text("# Review\nStatus: APPROVED\n", encoding="utf-8")

        with self.assertRaises(SystemExit) as cm:
            main(["check", "--stage", "2", "--repo-root", str(self.root), "--quiet"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
