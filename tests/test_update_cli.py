import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from forgeflow._version import __version__
from forgeflow.cli import handle_update, parse_forgeflow_args
from forgeflow.scaffold import TemplateScaffolder


class TestUpdateCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_update_success_and_preserves_tasks(self):
        # 1. Initialize project with old version and active task
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config_path = self.root / ".forgeflow.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        config_data["forgeflow_version"] = "0.1.0"
        config_path.write_text(json.dumps(config_data, indent=2) + "\n", encoding="utf-8")

        # Create active task artifact in tasks/in-progress
        task_dir = self.root / "tasks" / "in-progress" / "v0.1.0-feature"
        task_dir.mkdir(parents=True, exist_ok=True)
        spec_file = task_dir / "spec.md"
        spec_content = "# Preserved User Spec Content\n"
        spec_file.write_text(spec_content, encoding="utf-8")

        # 2. Run forgeflow update --path <root> --json
        args = parse_forgeflow_args(["update", "--path", str(self.root), "--json"])
        code = handle_update(args)
        self.assertEqual(code, 0)

        # 3. Assertions
        updated_config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(updated_config["forgeflow_version"], __version__)

        # Scripts must exist and have executable permissions
        script_file = self.root / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        self.assertTrue(script_file.exists())
        file_mode = stat.S_IMODE(os.stat(script_file).st_mode)
        self.assertTrue(bool(file_mode & stat.S_IXUSR))

        # Existing task artifact must be 100% preserved
        self.assertTrue(spec_file.exists())
        self.assertEqual(spec_file.read_text(encoding="utf-8"), spec_content)

    def test_update_fails_when_not_forgeflow_repo(self):
        empty_dir = self.root / "empty"
        empty_dir.mkdir()
        args = parse_forgeflow_args(["update", "--path", str(empty_dir), "--json"])
        code = handle_update(args)
        self.assertEqual(code, 1)

    def test_update_includes_changelog_summary(self):
        # 1. Setup mock repo with older version
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config_path = self.root / ".forgeflow.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        config_data["forgeflow_version"] = "0.1.10"
        config_path.write_text(json.dumps(config_data, indent=2) + "\n", encoding="utf-8")

        # 2. JSON mode check
        from unittest.mock import patch
        args = parse_forgeflow_args(["update", "--path", str(self.root), "--json"])
        with patch("builtins.print") as mock_print:
            code = handle_update(args)
            self.assertEqual(code, 0)
            mock_print.assert_called_once()
            output = json.loads(mock_print.call_args[0][0])
            self.assertIn("changelog_summary", output)
            self.assertIsNotNone(output["changelog_summary"])
            # Summary should be concise, not contain raw markdown '## ' header or '### Added'
            summary_text = output["changelog_summary"]
            self.assertFalse(summary_text.startswith("## "))
            self.assertIn("- ", summary_text)

        # 3. Terminal stdout mode check
        config_data["forgeflow_version"] = "0.1.10"
        config_path.write_text(json.dumps(config_data, indent=2) + "\n", encoding="utf-8")

        args_stdout = parse_forgeflow_args(["update", "--path", str(self.root)])
        with patch("builtins.print") as mock_print:
            code = handle_update(args_stdout)
            self.assertEqual(code, 0)
            printed = " ".join(call[0][0] for call in mock_print.call_args_list if call[0])
            self.assertIn("What's Changed in this update", printed)
            self.assertIn("forgeflow doc show changelog", printed)

    def test_summarize_changelog_section(self):
        # Case 1: Standard section with custom release title
        section_with_title = (
            "## [0.1.13] - 2026-10-24\n\n"
            "### 📢 CHANGELOG 배포 연동 및 upgrade/update 변경 내역 자동 프리뷰 (Changelog Preview & Distribution)\n\n"
            "### Added\n"
            "- Some detail"
        )
        res1 = TemplateScaffolder.summarize_changelog_section(section_with_title)
        self.assertEqual(
            res1,
            "[0.1.13] - 2026-10-24\n"
            "- 📢 CHANGELOG 배포 연동 및 upgrade/update 변경 내역 자동 프리뷰 (Changelog Preview & Distribution)"
        )

        # Case 2: Standard section without custom title (category only)
        section_category_only = (
            "## [0.1.99] - 2026-10-25\n\n"
            "### Added\n"
            "- **New Feature**: Added sample feature.\n"
            "- Another feature"
        )
        res2 = TemplateScaffolder.summarize_changelog_section(section_category_only)
        self.assertEqual(
            res2,
            "[0.1.99] - 2026-10-25\n"
            "- **New Feature**: Added sample feature."
        )

        # Case 3: Empty / minimal
        self.assertEqual(TemplateScaffolder.summarize_changelog_section(""), "")
        self.assertEqual(
            TemplateScaffolder.summarize_changelog_section("## [0.1.1] - 2026-10-20"),
            "[0.1.1] - 2026-10-20\n- (세부 변경 사항 없음)"
        )

    def test_update_preserves_custom_settings_and_keys(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config_path = self.root / ".forgeflow.json"

        # User modifies .forgeflow.json with custom values and additional custom keys
        custom_config = {
            "forgeflow_version": "0.1.0",
            "governance": {
                "tasks_dir": "my-tasks",
                "strict_mode": False,
                "max_loop_budget": 12,
                "user_custom_rule": "custom_val"
            },
            "paths": {
                "in_progress": "my-tasks/in-progress",
                "completed": "my-tasks/completed"
            },
            "custom_metadata": {
                "team": "core-ai",
                "enabled": True
            },
            "custom_flag": 42
        }
        config_path.write_text(json.dumps(custom_config, indent=2) + "\n", encoding="utf-8")

        # Run forgeflow update
        args = parse_forgeflow_args(["update", "--path", str(self.root), "--json"])
        code = handle_update(args)
        self.assertEqual(code, 0)

        # Verify config after update
        updated = json.loads(config_path.read_text(encoding="utf-8"))
        # 1. Version must be updated to current
        self.assertEqual(updated["forgeflow_version"], __version__)
        # 2. All user-modified governance settings must be preserved exactly
        self.assertEqual(updated["governance"]["tasks_dir"], "my-tasks")
        self.assertEqual(updated["governance"]["strict_mode"], False)
        self.assertEqual(updated["governance"]["max_loop_budget"], 12)
        self.assertEqual(updated["governance"]["user_custom_rule"], "custom_val")
        # 3. Custom paths must be preserved
        self.assertEqual(updated["paths"]["in_progress"], "my-tasks/in-progress")
        self.assertEqual(updated["paths"]["completed"], "my-tasks/completed")
        # 4. Custom top-level keys must be preserved
        self.assertEqual(updated["custom_metadata"]["team"], "core-ai")
        self.assertEqual(updated["custom_metadata"]["enabled"], True)
        self.assertEqual(updated["custom_flag"], 42)

    def test_update_no_op_when_already_current_and_customized(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config_path = self.root / ".forgeflow.json"

        # Config is already at current __version__ with custom settings
        custom_config = {
            "forgeflow_version": __version__,
            "governance": {
                "tasks_dir": "tasks",
                "strict_mode": False,
                "max_loop_budget": 7,
            },
            "paths": {
                "in_progress": "tasks/in-progress",
                "completed": "tasks/completed",
            },
            "my_key": "my_value"
        }
        config_path.write_text(json.dumps(custom_config, indent=2) + "\n", encoding="utf-8")
        orig_mtime = os.stat(config_path).st_mtime_ns

        # Run forgeflow update
        res = TemplateScaffolder.update_repo_governance(self.root)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["current_version"], __version__)

        # .forgeflow.json must not be in updated_files because it did not change
        self.assertNotIn(".forgeflow.json", res["updated_files"])

        # Content must remain intact
        after = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(after, custom_config)

    def test_scaffold_force_preserves_custom_keys(self):
        config_path = self.root / ".forgeflow.json"
        custom_config = {
            "forgeflow_version": "0.1.0",
            "governance": {
                "tasks_dir": "tasks",
                "strict_mode": False,
                "max_loop_budget": 9,
            },
            "paths": {
                "in_progress": "tasks/in-progress",
                "completed": "tasks/completed",
            },
            "user_top_level": "preserved"
        }
        config_path.write_text(json.dumps(custom_config, indent=2) + "\n", encoding="utf-8")

        # Call scaffold_speckit_hybrid with force=True
        res = TemplateScaffolder.scaffold_speckit_hybrid(self.root, force=True)
        self.assertEqual(res["status"], "success")

        after = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(after["governance"]["strict_mode"], False)
        self.assertEqual(after["governance"]["max_loop_budget"], 9)
        self.assertEqual(after["user_top_level"], "preserved")

    def test_deep_merge_config_populates_missing_defaults_without_overwriting(self):
        existing = {
            "forgeflow_version": "0.1.0",
            "governance": {
                "strict_mode": False,
            },
            "custom": 123
        }
        defaults = {
            "forgeflow_version": "0.1.0",
            "governance": {
                "tasks_dir": "tasks",
                "strict_mode": True,
                "max_loop_budget": 5,
            },
            "paths": {
                "in_progress": "tasks/in-progress",
                "completed": "tasks/completed",
            }
        }
        merged = TemplateScaffolder.deep_merge_config(existing, defaults)

        # Existing values must take precedence
        self.assertEqual(merged["governance"]["strict_mode"], False)
        self.assertEqual(merged["custom"], 123)
        # Missing default keys must be populated
        self.assertEqual(merged["governance"]["tasks_dir"], "tasks")
        self.assertEqual(merged["governance"]["max_loop_budget"], 5)
        self.assertEqual(merged["paths"]["in_progress"], "tasks/in-progress")


if __name__ == "__main__":
    unittest.main()
