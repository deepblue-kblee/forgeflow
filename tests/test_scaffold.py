#!/usr/bin/env python3
"""
Unit tests for TemplateScaffolder
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from forgeflow.scaffold import TemplateScaffolder, resolve_auto_create_branch
from forgeflow.validator import DocumentIntegrityValidator


class TestScaffolder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scaffold_creates_valid_governance_docs(self):
        rel_dir = self.temp_dir / "v0.1.0-test"
        created = TemplateScaffolder.create_release_scaffold(rel_dir, "v0.1.0-test", tier=2)
        self.assertEqual(len(created), 7)

        validator = DocumentIntegrityValidator(rel_dir)
        for doc_name in ["PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md"]:
            stat = validator.validate_file(doc_name)
            self.assertTrue(stat.exists, f"{doc_name} should exist")
            self.assertTrue(stat.passed, f"{doc_name} should pass initial validation: {stat.errors}")

    def test_init_project_governance(self):
        res = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        self.assertTrue((self.temp_dir / "tasks").exists())
        self.assertTrue((self.temp_dir / "tasks" / "README.md").exists())
        self.assertTrue((self.temp_dir / "src").exists())
        self.assertTrue((self.temp_dir / "tests").exists())
        self.assertTrue((self.temp_dir / ".forgeflow" / "config.json").exists())
        self.assertTrue((self.temp_dir / "docs" / "forgeflow" / "GOVERNANCE.md").exists())
        for guide in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            self.assertIn(
                "At the start of every session, always read `docs/forgeflow/GOVERNANCE.md` and comply with its rules.",
                (self.temp_dir / guide).read_text(encoding="utf-8"),
            )

        config_data = json.loads((self.temp_dir / ".forgeflow" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config_data["project"]["name"], "test-proj")
        self.assertEqual(config_data["governance"]["default_tier"], 2)
        self.assertEqual(config_data["governance"]["continuation_policy"], "interactive")
        self.assertIn(".forgeflow/config.json", res["created_files"])
        for relative_path in TemplateScaffolder.BUNDLE_FILES:
            self.assertTrue((self.temp_dir / relative_path).exists(), relative_path)

    def test_init_supports_autonomous_policy_and_non_destructive_migration(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        config_path = self.temp_dir / ".forgeflow" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["governance"].pop("continuation_policy")
        config["custom"] = {"preserve": True}
        config_path.write_text(json.dumps(config), encoding="utf-8")
        TemplateScaffolder.init_project_governance(
            self.temp_dir, "test-proj", migrate_continuation_policy=True
        )
        migrated = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(migrated["governance"]["continuation_policy"], "interactive")
        self.assertEqual(migrated["custom"], {"preserve": True})

    def test_migration_refuses_policy_replacement(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        with self.assertRaisesRegex(ValueError, "differs"):
            TemplateScaffolder.init_project_governance(
                self.temp_dir,
                "test-proj",
                continuation_policy="autonomous",
                migrate_continuation_policy=True,
            )

    def test_init_does_not_distribute_self_governance_control_or_binding(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")

        self.assertFalse((self.temp_dir / "docs" / "forgeflow" / "SELF_GOVERNANCE.md").exists())
        for guide in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            self.assertNotIn(
                "SELF_GOVERNANCE.md",
                (self.temp_dir / guide).read_text(encoding="utf-8"),
            )
        self.assertNotIn(
            Path("docs/forgeflow/SELF_GOVERNANCE.md"),
            TemplateScaffolder.BUNDLE_FILES,
        )

    def test_init_installs_bundle_without_overwriting_existing_files(self):
        existing = self.temp_dir / "docs" / "forgeflow" / "spec" / "FLOW_SPEC.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("# local annotation\n", encoding="utf-8")

        first = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        second = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")

        self.assertEqual(existing.read_text(encoding="utf-8"), "# local annotation\n")
        self.assertIn("docs/forgeflow/spec/FLOW_SPEC.md", first["skipped_files"])
        for relative_path in TemplateScaffolder.BUNDLE_FILES:
            self.assertIn(str(relative_path), second["skipped_files"])

    def test_refresh_governance_does_not_overwrite_existing_bundle(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        spec = self.temp_dir / "docs" / "forgeflow" / "spec" / "FLOW_SPEC.md"
        spec.write_text("# project copy\n", encoding="utf-8")

        TemplateScaffolder.init_project_governance(
            self.temp_dir, "test-proj", refresh_governance=True
        )

        self.assertEqual(spec.read_text(encoding="utf-8"), "# project copy\n")

    def test_force_reinstalls_every_governed_bundle_file(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        central = self.temp_dir / TemplateScaffolder.GOVERNANCE_PATH
        central.write_text("# local central\n", encoding="utf-8")
        for relative_path in TemplateScaffolder.BUNDLE_FILES:
            (self.temp_dir / relative_path).write_text("# local bundle\n", encoding="utf-8")

        result = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj", force=True)

        self.assertIn(str(TemplateScaffolder.GOVERNANCE_PATH), result["updated_files"])
        for relative_path, resource_name in TemplateScaffolder.BUNDLE_FILES.items():
            self.assertIn(str(relative_path), result["updated_files"])
            self.assertEqual(
                TemplateScaffolder.get_template_content(resource_name),
                (self.temp_dir / relative_path).read_text(encoding="utf-8"),
            )

    def test_force_reports_created_missing_bundle_file_as_updated(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        missing = next(iter(TemplateScaffolder.BUNDLE_FILES))
        (self.temp_dir / missing).unlink()

        result = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj", force=True)

        self.assertIn(str(missing), result["updated_files"])

    def test_force_reinstall_never_changes_or_creates_root_guides(self):
        agents = self.temp_dir / "AGENTS.md"
        agents.write_text("# user-owned guide\n", encoding="utf-8")

        result = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj", force=True)

        self.assertEqual("# user-owned guide\n", agents.read_text(encoding="utf-8"))
        self.assertFalse((self.temp_dir / "CLAUDE.md").exists())
        self.assertFalse((self.temp_dir / "GEMINI.md").exists())
        self.assertIn(str(TemplateScaffolder.GOVERNANCE_PATH), result["updated_files"])

    def test_installed_bundle_matches_package_resources(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        for relative_path, resource_name in TemplateScaffolder.BUNDLE_FILES.items():
            self.assertEqual(
                (self.temp_dir / relative_path).read_text(encoding="utf-8"),
                TemplateScaffolder.get_template_content(resource_name),
            )

    def test_packaged_specifications_match_source_specifications(self):
        repository_root = Path(__file__).resolve().parent.parent
        for name in ("CHANGELOG.md", "FLOW_SPEC.md", "GATES_AND_LOOPS.md"):
            self.assertEqual(
                TemplateScaffolder.get_template_content(f"spec/{name}"),
                (repository_root / "docs" / "spec" / name).read_text(encoding="utf-8"),
            )

    def test_packaged_release_templates_match_source_templates(self):
        package_templates_root = Path(__file__).resolve().parent.parent / "src" / "forgeflow" / "templates"
        # Active templates must exist in source and match
        for name in ("QA_SIGNOFF.md", "RELEASE_SIGNOFF.md", "COMPLETION_REPORT.md"):
            content = TemplateScaffolder.get_template_content(name)
            self.assertTrue(len(content) > 0)
            self.assertEqual(
                content,
                (package_templates_root / name).read_text(encoding="utf-8"),
            )
        # Purged legacy templates must NOT exist in templates directory, but fallback works
        for legacy_name in ("PRD.md", "DESIGN.md", "ROADMAP.md", "GOVERNANCE.md", "RELEASE_NOTES.md"):
            self.assertFalse((package_templates_root / legacy_name).exists())
            legacy_content = TemplateScaffolder.get_template_content(legacy_name)
            self.assertTrue(len(legacy_content) > 0)

    def test_release_notes_is_user_facing_and_not_core_artifact(self):
        rel_dir = self.temp_dir / "v0.1.0-notes"
        created = TemplateScaffolder.create_release_scaffold(rel_dir, "v0.1.0-notes", tier=3)
        self.assertIn("RELEASE_NOTES.md", created)
        notes = (rel_dir / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        for heading in ("기능 변화", "사용자 영향", "운영·업그레이드 유의사항", "알려진 제약", "근거 문서"):
            self.assertIn(heading, notes)

    def test_governance_binding_preserves_existing_guide_and_is_idempotent(self):
        guide = self.temp_dir / "AGENTS.md"
        guide.write_text("# Local rules\n", encoding="utf-8")
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        first = guide.read_text(encoding="utf-8")
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        self.assertEqual(first, guide.read_text(encoding="utf-8"))
        self.assertIn("# Local rules", first)

    def test_governance_binding_rejects_symlinked_docs_directory(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (self.temp_dir / "docs").symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(ValueError, "Unsafe directory"):
            TemplateScaffolder.scaffold_governance_binding(self.temp_dir)

        self.assertFalse((outside / "forgeflow" / "GOVERNANCE.md").exists())

    def test_init_skips_symbolic_link_root_guide_without_dereferencing(self):
        sentinel = self.temp_dir / "sentinel.md"
        sentinel.write_text("# external\n", encoding="utf-8")
        (self.temp_dir / "GEMINI.md").symlink_to(sentinel)

        result = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "# external\n")
        self.assertTrue((self.temp_dir / "GEMINI.md").is_symlink())
        self.assertIn("GEMINI.md (symbolic link outside project or unsafe; not modified)", result["skipped_files"])
        self.assertTrue((self.temp_dir / "docs" / "forgeflow" / "GOVERNANCE.md").exists())
        self.assertIn(TemplateScaffolder.BINDING_START, (self.temp_dir / "AGENTS.md").read_text(encoding="utf-8"))

    def test_init_binds_in_project_symbolic_link_target(self):
        agents = self.temp_dir / "AGENTS.md"
        agents.write_text("# local rules\n", encoding="utf-8")
        gemini = self.temp_dir / "GEMINI.md"
        gemini.symlink_to("AGENTS.md")

        result = TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")

        self.assertTrue(gemini.is_symlink())
        self.assertIn(TemplateScaffolder.BINDING_START, agents.read_text(encoding="utf-8"))
        self.assertIn("GEMINI.md (symbolic link; target already bound)", result["skipped_files"])

    def test_governance_binding_rejects_malformed_marker_without_writes(self):
        guide = self.temp_dir / "AGENTS.md"
        guide.write_text(TemplateScaffolder.BINDING_START + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Invalid ForgeFlow governance binding markers"):
            TemplateScaffolder.scaffold_governance_binding(self.temp_dir)

        self.assertFalse((self.temp_dir / "docs" / "forgeflow" / "GOVERNANCE.md").exists())
        self.assertEqual(guide.read_text(encoding="utf-8"), TemplateScaffolder.BINDING_START + "\n")

    def test_init_rolls_back_config_and_created_directories_on_preflight_failure(self):
        guide = self.temp_dir / "AGENTS.md"
        guide.write_text(TemplateScaffolder.BINDING_START + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Invalid ForgeFlow governance binding markers"):
            TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")

        self.assertFalse((self.temp_dir / ".forgeflow" / "config.json").exists())
        self.assertFalse((self.temp_dir / ".forgeflow" / "config.json").exists())
        self.assertFalse((self.temp_dir / ".forgeflow.json").exists())
        self.assertFalse((self.temp_dir / "docs").exists())
        self.assertFalse((self.temp_dir / "src").exists())
        self.assertFalse((self.temp_dir / "tests").exists())

    def test_init_preflights_all_directories_before_creating_any(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (self.temp_dir / "src").symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(ValueError, "Unsafe directory"):
            TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")

        self.assertFalse((self.temp_dir / "docs").exists())
        self.assertFalse((self.temp_dir / "tests").exists())
        self.assertFalse((self.temp_dir / ".forgeflow" / "config.json").exists())
        self.assertFalse((self.temp_dir / ".forgeflow.json").exists())

    def test_refresh_governance_uses_numbered_backup_on_collision(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        central = self.temp_dir / TemplateScaffolder.GOVERNANCE_PATH
        original = "# Local governance\n"
        central.write_text(original, encoding="utf-8")
        fixed_backup = central.with_name(central.name + ".bak")
        fixed_backup.write_text("# Existing backup\n", encoding="utf-8")

        TemplateScaffolder.init_project_governance(
            self.temp_dir, "test-proj", refresh_governance=True
        )

        self.assertEqual(fixed_backup.read_text(encoding="utf-8"), "# Existing backup\n")
        self.assertEqual(
            central.with_name(central.name + ".bak.1").read_text(encoding="utf-8"), original
        )
        self.assertIn("forgeflow check --all --strict", central.read_text(encoding="utf-8"))

    def test_init_reports_refreshed_governance_as_updated(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        result = TemplateScaffolder.init_project_governance(
            self.temp_dir, "test-proj", refresh_governance=True
        )

        governance_path = str(TemplateScaffolder.GOVERNANCE_PATH)
        self.assertIn(governance_path, result["updated_files"])
        self.assertNotIn(governance_path, result["created_files"])

    def test_journal_cleanup_failure_keeps_backups_for_recovery(self):
        real_unlink = Path.unlink
        journal = self.temp_dir / TemplateScaffolder.JOURNAL_PATH
        (self.temp_dir / "AGENTS.md").write_text("# Existing guide\n", encoding="utf-8")

        def fail_only_journal(path, *args, **kwargs):
            if path.name == TemplateScaffolder.JOURNAL_PATH.name:
                raise OSError("simulated journal cleanup failure")
            return real_unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", new=fail_only_journal):
            with self.assertRaisesRegex(OSError, "journal cleanup failure"):
                TemplateScaffolder.scaffold_governance_binding(self.temp_dir)

        self.assertTrue(journal.exists())
        self.assertTrue(list(self.temp_dir.glob(".forgeflow-init-*.bak")))
        TemplateScaffolder.scaffold_governance_binding(self.temp_dir)
        self.assertFalse(journal.exists())
        self.assertFalse(list(self.temp_dir.glob(".forgeflow-init-*.bak")))

    def test_governance_transaction_rolls_back_replaced_and_created_files(self):
        real_replace = __import__("os").replace

        def fail_on_claude(source, destination):
            if Path(destination).name == "CLAUDE.md":
                raise OSError("simulated replace failure")
            return real_replace(source, destination)

        with patch("forgeflow.scaffold.os.replace", side_effect=fail_on_claude):
            with self.assertRaisesRegex(OSError, "simulated replace failure"):
                TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")

        self.assertFalse((self.temp_dir / ".forgeflow" / "config.json").exists())
        self.assertFalse((self.temp_dir / ".forgeflow.json").exists())
        self.assertFalse((self.temp_dir / "docs" / "forgeflow" / "GOVERNANCE.md").exists())
        for guide in TemplateScaffolder.ROOT_GUIDES:
            self.assertFalse((self.temp_dir / guide).exists())
        self.assertFalse((self.temp_dir / "docs" / "forgeflow" / "spec" / "FLOW_SPEC.md").exists())
        self.assertFalse((self.temp_dir / "docs" / "forgeflow" / "templates" / "PRD.md").exists())

    def test_governance_rejects_corrupt_transaction_journal(self):
        journal = self.temp_dir / TemplateScaffolder.JOURNAL_PATH
        journal.write_text('{"entries": []}', encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "transaction journal"):
            TemplateScaffolder.scaffold_governance_binding(self.temp_dir)

        self.assertEqual(journal.read_text(encoding="utf-8"), '{"entries": []}')

    def test_governance_recovers_after_rollback_failure(self):
        real_replace = __import__("os").replace
        calls = {"agents": 0}
        (self.temp_dir / "AGENTS.md").write_text("# Existing guide\n", encoding="utf-8")

        def fail_replace_and_rollback(source, destination):
            destination_name = Path(destination).name
            if destination_name == "CLAUDE.md":
                raise OSError("initial replacement failure")
            if destination_name == "AGENTS.md":
                calls["agents"] += 1
                if calls["agents"] == 2:
                    raise OSError("rollback failure")
            return real_replace(source, destination)

        with patch("forgeflow.scaffold.os.replace", side_effect=fail_replace_and_rollback):
            with self.assertRaisesRegex(RuntimeError, "rollback failed"):
                TemplateScaffolder.scaffold_governance_binding(self.temp_dir)

        journal = self.temp_dir / TemplateScaffolder.JOURNAL_PATH
        self.assertTrue(journal.exists())
        TemplateScaffolder.scaffold_governance_binding(self.temp_dir)
        self.assertFalse(journal.exists())
        self.assertTrue((self.temp_dir / "docs" / "forgeflow" / "GOVERNANCE.md").exists())
        for guide in TemplateScaffolder.ROOT_GUIDES:
            self.assertTrue((self.temp_dir / guide).exists())

    def test_migrate_exact_legacy_governance_binding(self):
        guide = self.temp_dir / "AGENTS.md"
        guide.write_text("# Local rules\n\n" + TemplateScaffolder.LEGACY_BINDING + "\n", encoding="utf-8")

        TemplateScaffolder.init_project_governance(
            self.temp_dir, "test-proj", migrate_governance_binding=True
        )

        content = guide.read_text(encoding="utf-8")
        self.assertIn("# Local rules", content)
        self.assertNotIn(TemplateScaffolder.LEGACY_BINDING, content)
        self.assertEqual(content.count(TemplateScaffolder.BINDING_START), 1)

    def test_rejects_unrecognized_legacy_binding_during_migration(self):
        guide = self.temp_dir / "AGENTS.md"
        guide.write_text(
            TemplateScaffolder.LEGACY_BINDING.replace("100%", "99%"), encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "Unrecognized legacy"):
            TemplateScaffolder.scaffold_governance_binding(self.temp_dir, migrate_legacy=True)

    def test_scaffold_force_overwrite(self):
        rel_dir = self.temp_dir / "v0.1.0-test"
        created = TemplateScaffolder.create_release_scaffold(rel_dir, "v0.1.0-test", tier=1)
        self.assertIn("RELEASE_NOTES.md", created)
        self.assertTrue((rel_dir / "RELEASE_NOTES.md").exists())
        prd_file = rel_dir / "CHANGE_NOTE.md"
        prd_file.write_text("CUSTOM CONTENT", encoding="utf-8")

        # Without force: should skip existing
        created_no_force = TemplateScaffolder.create_release_scaffold(rel_dir, "v0.1.0-test", tier=1, force=False)
        self.assertNotIn("CHANGE_NOTE.md", created_no_force)
        self.assertEqual(prd_file.read_text(encoding="utf-8"), "CUSTOM CONTENT")

        # With force: should overwrite
        created_force = TemplateScaffolder.create_release_scaffold(rel_dir, "v0.1.0-test", tier=1, force=True)
        self.assertIn("CHANGE_NOTE.md", created_force)
        self.assertNotEqual(prd_file.read_text(encoding="utf-8"), "CUSTOM CONTENT")

    def test_custom_template_dir(self):
        custom_tmpl_dir = self.temp_dir / "custom_templates"
        custom_tmpl_dir.mkdir(parents=True, exist_ok=True)
        (custom_tmpl_dir / "PRD.md").write_text("# CUSTOM PRD {{RELEASE_ID}}", encoding="utf-8")

        rel_dir = self.temp_dir / "v0.2.0-custom"
        created = TemplateScaffolder.create_release_scaffold(
            rel_dir, "v0.2.0-custom", tier=2, custom_template_dir=custom_tmpl_dir
        )
        self.assertIn("PRD.md", created)
        content = (rel_dir / "PRD.md").read_text(encoding="utf-8")
        self.assertEqual(content, "# CUSTOM PRD v0.2.0-custom")

    def test_resolve_auto_create_branch_defaults_to_false(self):
        # 1. When .forgeflow.json does not exist
        empty_dir = self.temp_dir / "empty_repo"
        empty_dir.mkdir()
        self.assertFalse(resolve_auto_create_branch(empty_dir))

        # 2. When .forgeflow.json exists but governance.auto_create_branch is omitted
        config_file = empty_dir / ".forgeflow.json"
        config_file.write_text(json.dumps({"forgeflow_version": "0.1.18", "governance": {}}), encoding="utf-8")
        self.assertFalse(resolve_auto_create_branch(empty_dir))

    def test_resolve_auto_create_branch_explicit_booleans(self):
        repo_dir = self.temp_dir / "repo_bool"
        repo_dir.mkdir()
        config_file = repo_dir / ".forgeflow.json"

        # Explicit True
        config_file.write_text(json.dumps({"governance": {"auto_create_branch": True}}), encoding="utf-8")
        self.assertTrue(resolve_auto_create_branch(repo_dir))

        # Explicit False
        config_file.write_text(json.dumps({"governance": {"auto_create_branch": False}}), encoding="utf-8")
        self.assertFalse(resolve_auto_create_branch(repo_dir))

    def test_resolve_auto_create_branch_strict_validation(self):
        repo_dir = self.temp_dir / "repo_invalid"
        repo_dir.mkdir()
        config_file = repo_dir / ".forgeflow.json"

        # Strings, numbers, etc. must raise ValueError
        invalid_values = ["true", "false", 1, 0, [], {}, 1.0]
        for val in invalid_values:
            config_file.write_text(json.dumps({"governance": {"auto_create_branch": val}}), encoding="utf-8")
            with self.assertRaises(ValueError, msg=f"Should raise ValueError for {val!r}"):
                resolve_auto_create_branch(repo_dir)


if __name__ == "__main__":
    unittest.main()
