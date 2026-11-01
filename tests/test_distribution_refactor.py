"""Tests for ForgeFlow distribution refactoring, spec isolation, and boot sequence modernization."""

import os
import tempfile
import unittest
from pathlib import Path

from forgeflow._version import __version__
from forgeflow.cli import OFFICIAL_SPECS, resolve_spec_directory, handle_doc, parse_forgeflow_args
from forgeflow.scaffold import TemplateScaffolder


class TestDistributionRefactor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.temp_dir, ignore_errors=True))

    def test_version_stamp_matches_framework_version(self):
        """Ensure spec/VERSION contains exact current framework version string."""
        spec_version_file = Path(__file__).resolve().parent.parent / "src" / "forgeflow" / "spec" / "VERSION"
        self.assertTrue(spec_version_file.is_file())
        version_str = spec_version_file.read_text(encoding="utf-8").strip()
        self.assertEqual(version_str, __version__)

    def test_spec_readme_exists_and_contains_router_table(self):
        """Ensure spec/README.md exists and provides situational routing for agents."""
        spec_readme_file = Path(__file__).resolve().parent.parent / "src" / "forgeflow" / "spec" / "README.md"
        self.assertTrue(spec_readme_file.is_file())
        content = spec_readme_file.read_text(encoding="utf-8")
        self.assertIn("FLOW_SPEC.md", content)
        self.assertIn("GATES_AND_LOOPS.md", content)
        self.assertIn("ANTI_PATTERNS.md", content)
        self.assertIn("DISTRIBUTION_SPEC.md", content)

    def test_changelog_is_not_inside_spec_directory(self):
        """Verify CHANGELOG.md is isolated from spec/ to prevent agent historical pollution."""
        spec_dir = Path(__file__).resolve().parent.parent / "src" / "forgeflow" / "spec"
        self.assertFalse((spec_dir / "CHANGELOG.md").exists())
        # Isolated CHANGELOG.md must exist in src/forgeflow/ or docs/
        src_changelog = Path(__file__).resolve().parent.parent / "src" / "forgeflow" / "CHANGELOG.md"
        self.assertTrue(src_changelog.is_file())

    def test_boot_anchor_template_contains_modern_directives(self):
        """Verify modern concise boot anchor template contains VERSION and README pointers."""
        anchor = TemplateScaffolder.BOOT_ANCHOR_TEMPLATE
        self.assertIn(".forgeflow/spec/README.md", anchor)
        self.assertIn(".forgeflow/spec/VERSION", anchor)
        self.assertIn("runtime identity", anchor)
        self.assertIn("baseline.command", anchor)
        self.assertIn("baseline.path/spec", anchor)
        self.assertNotIn("Amnesia", anchor)
        self.assertNotIn("current", anchor)
        # Ensure ~니다 style is not used
        self.assertNotIn("합니다", anchor)
        self.assertNotIn("바랍니다", anchor)

    def test_scaffold_creates_spec_symlink_in_forgeflow_dir(self):
        """Verify scaffolding creates .forgeflow/spec symlink."""
        res = TemplateScaffolder.scaffold_speckit_hybrid(self.temp_dir, force=True)
        self.assertEqual(res["status"], "success")
        spec_symlink = self.temp_dir / ".forgeflow" / "spec"
        self.assertTrue(spec_symlink.is_symlink())
        # Target must point to valid directory
        self.assertTrue(spec_symlink.resolve().is_dir())
        self.assertTrue((spec_symlink / "FLOW_SPEC.md").is_file())

    def test_doc_cli_resolves_via_project_spec_symlink(self):
        """Verify doc CLI resolves spec through project .forgeflow/spec symlink."""
        TemplateScaffolder.scaffold_speckit_hybrid(self.temp_dir, force=True)
        resolved = resolve_spec_directory(str(self.temp_dir))
        self.assertIsNotNone(resolved)
        self.assertTrue((resolved / "FLOW_SPEC.md").is_file())


if __name__ == "__main__":
    unittest.main()
