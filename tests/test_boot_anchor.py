"""
Tests for Non-Destructive, Idempotent Session Boot Anchor Injection in Root Guides (AGENTS.md / CLAUDE.md)
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from forgeflow.scaffold import TemplateScaffolder


class TestBootAnchor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_bind_creates_agents_md_when_missing(self):
        result = TemplateScaffolder.bind_boot_anchor(self.temp_dir)
        self.assertEqual(result.get("AGENTS.md"), "created")
        agents_file = self.temp_dir / "AGENTS.md"
        self.assertTrue(agents_file.is_file())
        content = agents_file.read_text(encoding="utf-8")
        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_START, content)
        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_END, content)
        self.assertIn("ForgeFlow Session Boot Sequence", content)

    def test_bind_prepends_to_existing_agents_md_preserving_content(self):
        agents_file = self.temp_dir / "AGENTS.md"
        user_content = "# Project Custom Rules\n\n- Rule 1: Always test code.\n- Rule 2: Never break production.\n"
        agents_file.write_text(user_content, encoding="utf-8")

        result = TemplateScaffolder.bind_boot_anchor(self.temp_dir)
        self.assertEqual(result.get("AGENTS.md"), "updated")

        new_content = agents_file.read_text(encoding="utf-8")
        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_START, new_content)
        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_END, new_content)
        # Original content must be 100% preserved
        self.assertIn(user_content.strip(), new_content)

    def test_bind_is_idempotent_on_repeated_calls(self):
        agents_file = self.temp_dir / "AGENTS.md"
        user_content = "# User Rules\n\nPreserve me.\n"
        agents_file.write_text(user_content, encoding="utf-8")

        # First call
        res1 = TemplateScaffolder.bind_boot_anchor(self.temp_dir)
        self.assertEqual(res1.get("AGENTS.md"), "updated")
        content1 = agents_file.read_text(encoding="utf-8")

        # Second call
        res2 = TemplateScaffolder.bind_boot_anchor(self.temp_dir)
        self.assertEqual(res2.get("AGENTS.md"), "unchanged")
        content2 = agents_file.read_text(encoding="utf-8")

        self.assertEqual(content1, content2)
        self.assertEqual(content2.count(TemplateScaffolder.BOOT_ANCHOR_START), 1)
        self.assertEqual(content2.count(TemplateScaffolder.BOOT_ANCHOR_END), 1)

    def test_bind_updates_in_place_when_anchor_modified(self):
        agents_file = self.temp_dir / "AGENTS.md"
        before_text = "# Header\n\n"
        old_anchor = (
            f"{TemplateScaffolder.BOOT_ANCHOR_START}\n"
            "Old anchor text to be replaced\n"
            f"{TemplateScaffolder.BOOT_ANCHOR_END}\n"
        )
        after_text = "\n# Footer\n\nUser custom footer section.\n"
        agents_file.write_text(before_text + old_anchor + after_text, encoding="utf-8")

        result = TemplateScaffolder.bind_boot_anchor(self.temp_dir)
        self.assertEqual(result.get("AGENTS.md"), "updated")

        new_content = agents_file.read_text(encoding="utf-8")
        self.assertTrue(new_content.startswith(before_text))
        self.assertTrue(new_content.endswith(after_text))
        self.assertNotIn("Old anchor text to be replaced", new_content)
        self.assertIn("ForgeFlow Session Boot Sequence", new_content)
        self.assertEqual(new_content.count(TemplateScaffolder.BOOT_ANCHOR_START), 1)

    def test_unbind_removes_anchor_restoring_original(self):
        agents_file = self.temp_dir / "AGENTS.md"
        original = "# Original Document\n\nAll my rules are here.\n"
        agents_file.write_text(original, encoding="utf-8")

        # Bind anchor
        TemplateScaffolder.bind_boot_anchor(self.temp_dir)
        bound_content = agents_file.read_text(encoding="utf-8")
        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_START, bound_content)

        # Unbind anchor
        unbind_res = TemplateScaffolder.unbind_boot_anchor(self.temp_dir)
        self.assertEqual(unbind_res.get("AGENTS.md"), "unbound")
        unbound_content = agents_file.read_text(encoding="utf-8")
        self.assertNotIn(TemplateScaffolder.BOOT_ANCHOR_START, unbound_content)
        self.assertNotIn(TemplateScaffolder.BOOT_ANCHOR_END, unbound_content)
        self.assertIn(original.strip(), unbound_content)

    def test_bind_handles_both_agents_and_claude(self):
        (self.temp_dir / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (self.temp_dir / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")

        result = TemplateScaffolder.bind_boot_anchor(self.temp_dir)
        self.assertEqual(result.get("AGENTS.md"), "updated")
        self.assertEqual(result.get("CLAUDE.md"), "updated")

        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_START, (self.temp_dir / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_START, (self.temp_dir / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_hybrid_scaffold_integrates_boot_anchor(self):
        scaffold_res = TemplateScaffolder.scaffold_speckit_hybrid(self.temp_dir)
        self.assertIn("AGENTS.md", scaffold_res.get("created_files", []))
        agents_file = self.temp_dir / "AGENTS.md"
        self.assertTrue(agents_file.is_file())
        self.assertIn(TemplateScaffolder.BOOT_ANCHOR_START, agents_file.read_text(encoding="utf-8"))
