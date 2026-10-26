import json
import tempfile
import unittest
from pathlib import Path

from forgeflow.scaffold import TemplateScaffolder
from forgeflow.cli import main


class TestHybridScaffold(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scaffold_speckit_hybrid_creates_required_files(self):
        res = TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        self.assertEqual(res["status"], "success")

        # Verify .forgeflow.json
        config_file = self.root / ".forgeflow.json"
        self.assertTrue(config_file.exists())
        config = json.loads(config_file.read_text(encoding="utf-8"))
        self.assertEqual(config["forgeflow_version"], "0.1.0")
        self.assertEqual(config["governance"]["tasks_dir"], "tasks")
        self.assertEqual(config["governance"]["max_loop_budget"], 5)

        # Verify .specify structure
        constitution = self.root / ".specify" / "memory" / "constitution.md"
        self.assertTrue(constitution.exists())
        const_text = constitution.read_text(encoding="utf-8")
        self.assertIn("제1조 (무승인 구현 금지", const_text)
        self.assertIn("제2조 (가짜 멈춤 금지", const_text)
        self.assertIn("제6조 (기획 시 안티패턴 및 ADR 필수 준수", const_text)
        self.assertIn("docs/spec/ANTI_PATTERNS.md", const_text)

        # Verify knowledge architecture (ANTI_PATTERNS.md & ADRs)
        self.assertTrue((self.root / "docs" / "spec" / "ANTI_PATTERNS.md").exists())
        self.assertTrue((self.root / "docs" / "adr" / "template.md").exists())
        self.assertTrue((self.root / "docs" / "adr" / "001-eliminate-git-sha-and-commit-range-bindings.md").exists())
        self.assertTrue((self.root / "docs" / "adr" / "002-remove-spec-body-hash-binding.md").exists())

        extensions = self.root / ".specify" / "extensions.yml"
        self.assertTrue(extensions.exists())
        ext_text = extensions.read_text(encoding="utf-8")
        self.assertIn("forgeflow check --stage 2", ext_text)

        implement_cmd = self.root / ".specify" / "templates" / "commands" / "implement.md"
        self.assertTrue(implement_cmd.exists())

        # Verify tasks directories
        self.assertTrue((self.root / "tasks" / "in-progress").is_dir())
        self.assertTrue((self.root / "tasks" / "completed").is_dir())
        self.assertTrue((self.root / "tasks" / "README.md").exists())

        # Verify .gitignore
        gi = self.root / ".gitignore"
        self.assertTrue(gi.exists())
        self.assertIn(".forgeflow/lifecycle/.*.lock", gi.read_text(encoding="utf-8"))

    def test_scaffold_creates_speckit_bash_scripts_with_executable_mode(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        expected_scripts = [
            "check-prerequisites.sh",
            "common.sh",
            "create-new-feature.sh",
            "resolve-template.sh",
            "setup-plan.sh",
            "setup-tasks.sh",
        ]
        scripts_dir = self.root / ".specify" / "scripts" / "bash"
        self.assertTrue(scripts_dir.is_dir())
        for s in expected_scripts:
            script_path = scripts_dir / s
            self.assertTrue(script_path.exists(), f"Missing script: {s}")
            # Verify executable mode
            mode = script_path.stat().st_mode
            self.assertTrue(mode & 0o111 != 0, f"Script {s} is not executable: {oct(mode)}")

    def test_scaffold_creates_speckit_templates(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        expected_templates = [
            "spec-template.md",
            "plan-template.md",
            "tasks-template.md",
            "checklist-template.md",
        ]
        templates_dir = self.root / ".specify" / "templates"
        self.assertTrue(templates_dir.is_dir())
        for t in expected_templates:
            tmpl_path = templates_dir / t
            self.assertTrue(tmpl_path.exists(), f"Missing template: {t}")
            self.assertGreater(tmpl_path.stat().st_size, 0)

    def test_scaffold_enforces_date_based_amnesia_on_legacy_config(self):
        config_file = self.root / ".forgeflow.json"
        legacy_config = {
            "forgeflow_version": "0.22.1",
            "created_at": "2026-10-15T12:00:00Z",
            "project": {"name": "legacy-project"},
            "governance": {"default_tier": 2, "required_documents": ["PRD.md", "DESIGN.md"]}
        }
        config_file.write_text(json.dumps(legacy_config), encoding="utf-8")

        res = TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        self.assertEqual(res["status"], "success")

        # Must overwrite with v0.1.0 standard and prune legacy fields
        new_config = json.loads(config_file.read_text(encoding="utf-8"))
        self.assertEqual(new_config["forgeflow_version"], "0.1.0")
        self.assertEqual(new_config["governance"]["tasks_dir"], "tasks")
        self.assertNotIn("PRD.md", json.dumps(new_config))

    def test_cli_init_speckit(self):
        import sys
        target = self.root / "sample-project"
        with self.assertRaises(SystemExit) as cm:
            main(["init", "--speckit", "--path", str(target)])
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((target / ".forgeflow.json").exists())
        self.assertTrue((target / ".specify" / "extensions.yml").exists())


if __name__ == "__main__":
    unittest.main()
