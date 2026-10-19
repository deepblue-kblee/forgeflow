#!/usr/bin/env python3
"""
Unit tests for HierarchicalRootScanner and ReleaseScanner
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from forgeflow.scanner import HierarchicalRootScanner, ReleaseScanner


class TestScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()
        self.releases_dir = self.temp_dir / "docs" / "releases"
        self.releases_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample releases
        (self.releases_dir / "v0.1.0-alpha").mkdir()
        (self.releases_dir / "v0.1.0-alpha" / "PRD.md").write_text("# PRD", encoding="utf-8")
        (self.releases_dir / "v0.2.0-beta").mkdir()
        (self.releases_dir / "v0.2.0-beta" / "PRD.md").write_text("# PRD", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_root_from_deep_nested_directory(self):
        deep_dir = self.temp_dir / "src" / "deep" / "nested"
        deep_dir.mkdir(parents=True, exist_ok=True)

        found_root = HierarchicalRootScanner.find_root(start_path=deep_dir)
        self.assertEqual(found_root, self.temp_dir)

    def test_get_all_releases_sorted(self):
        releases = ReleaseScanner.get_all_releases(self.temp_dir)
        self.assertEqual(len(releases), 2)
        self.assertEqual(releases[0].name, "v0.1.0-alpha")
        self.assertEqual(releases[1].name, "v0.2.0-beta")

    def test_get_latest_release(self):
        latest = ReleaseScanner.get_latest_release(self.temp_dir)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.name, "v0.2.0-beta")

    def test_semantic_version_sorting(self):
        # Create releases that test lexicographical vs semantic ordering:
        # Lexicographically, 'v0.10.0' < 'v0.9.0', but semantically 0.10.0 > 0.9.0.
        (self.releases_dir / "v0.9.0-feature").mkdir()
        (self.releases_dir / "v0.9.0-feature" / "PRD.md").write_text("# PRD", encoding="utf-8")
        (self.releases_dir / "v0.10.0-feature").mkdir()
        (self.releases_dir / "v0.10.0-feature" / "PRD.md").write_text("# PRD", encoding="utf-8")
        (self.releases_dir / "v0.14.0-feature").mkdir()
        (self.releases_dir / "v0.14.0-feature" / "PRD.md").write_text("# PRD", encoding="utf-8")
        (self.releases_dir / "v0.15.0-latest").mkdir()
        (self.releases_dir / "v0.15.0-latest" / "PRD.md").write_text("# PRD", encoding="utf-8")

        all_rels = ReleaseScanner.get_all_releases(self.temp_dir)
        rel_names = [r.name for r in all_rels]
        self.assertIn("v0.9.0-feature", rel_names)
        self.assertIn("v0.10.0-feature", rel_names)
        self.assertIn("v0.14.0-feature", rel_names)
        self.assertIn("v0.15.0-latest", rel_names)

        # Verify ordering: v0.9.0 must come before v0.10.0
        idx_9 = rel_names.index("v0.9.0-feature")
        idx_10 = rel_names.index("v0.10.0-feature")
        idx_14 = rel_names.index("v0.14.0-feature")
        idx_15 = rel_names.index("v0.15.0-latest")
        self.assertLess(idx_9, idx_10)
        self.assertLess(idx_10, idx_14)
        self.assertLess(idx_14, idx_15)

        latest = ReleaseScanner.get_latest_release(self.temp_dir)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.name, "v0.15.0-latest")


if __name__ == "__main__":
    unittest.main()
