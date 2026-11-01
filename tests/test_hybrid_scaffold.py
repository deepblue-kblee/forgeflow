"""Default setup is lean, repeatable, and preserves project-owned content."""

import json
import tempfile
import unittest
from pathlib import Path

from forgeflow._version import __version__
from forgeflow.scaffold import TemplateScaffolder, resolve_auto_create_branch
from forgeflow.cli import main


class TestHybridScaffold(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scaffold_creates_lean_config_and_pinned_executable_specs(self):
        result = TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config = json.loads((self.root / ".forgeflow/config.json").read_text())
        self.assertEqual(config["forgeflow_version"], __version__)
        self.assertEqual(config["workflow"], {"mode": "lean", "checks": [], "owner": "standalone"})
        self.assertFalse(config["governance"]["auto_create_branch"])
        self.assertTrue((self.root / ".forgeflow/run.py").is_file())
        self.assertIn(result["baseline"]["identity"], str((self.root / ".forgeflow/spec").resolve()))
        self.assertTrue((self.root / ".forgeflow/spec/FLOW_SPEC.md").is_file())
        for name in (".specify/memory/constitution.md", ".specify/extensions.yml",
                     ".specify/templates/commands/implement.md", "docs/adr", "docs/spec"):
            self.assertFalse((self.root / name).exists(), name)
        self.assertTrue((self.root / "tasks/in-progress").is_dir())
        self.assertTrue((self.root / "tasks/completed").is_dir())
        self.assertIn(".forgeflow/runtime/", (self.root / ".gitignore").read_text())

    def test_optional_speckit_assets_are_executable_and_usable(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        for name in ("check-prerequisites.sh", "common.sh", "create-new-feature.sh",
                     "resolve-template.sh", "setup-plan.sh", "setup-tasks.sh"):
            script = self.root / ".specify/scripts/bash" / name
            self.assertTrue(script.is_file())
            self.assertTrue(script.stat().st_mode & 0o111)
        for name in ("spec-template.md", "plan-template.md", "tasks-template.md", "checklist-template.md"):
            self.assertGreater((self.root / ".specify/templates" / name).stat().st_size, 0)

    def test_force_repeated_setup_preserves_user_config_constitution_hooks_templates(self):
        contents = {
            ".forgeflow/config.json": json.dumps({"forgeflow_version": "0.22.1", "created_at": "2026-10-15",
                "governance": {"required_documents": ["PRD.md"], "default_tier": 2},
                "workflow": {"owner": "host", "checks": [["custom-test"]]}, "custom": 42}),
            ".specify/memory/constitution.md": "# My constitution\n",
            ".specify/extensions.yml": "hooks: custom\n",
            ".specify/templates/spec-template.md": "# My spec template\n",
            ".specify/scripts/bash/common.sh": "#!/bin/sh\n# My shared helper\n",
        }
        for name, content in contents.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        for _ in range(2):
            TemplateScaffolder.scaffold_speckit_hybrid(self.root, force=True)
        for name, content in contents.items():
            self.assertEqual((self.root / name).read_text(), content, name)

    def test_default_init_does_not_inject_strict_bundle_or_speckit(self):
        result = TemplateScaffolder.init_project_governance(self.root, "sample")
        self.assertEqual(result["project_name"], "sample")
        self.assertFalse((self.root / ".specify").exists())
        self.assertFalse((self.root / "docs/forgeflow").exists())
        self.assertFalse((self.root / "src").exists())
        self.assertIn(".forgeflow/spec/README.md", (self.root / "AGENTS.md").read_text())

    def test_host_owner_disables_auto_branch_even_when_legacy_setting_is_true(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"owner": "host"},
                                      "governance": {"auto_create_branch": True}}))
        self.assertFalse(resolve_auto_create_branch(self.root))

    def test_cli_init_speckit(self):
        target = self.root / "sample-project"
        with self.assertRaises(SystemExit) as raised:
            main(["init", "--speckit", "--path", str(target)])
        self.assertEqual(raised.exception.code, 0)
        self.assertTrue((target / ".forgeflow/config.json").is_file())
        self.assertTrue((target / ".specify/scripts/bash/setup-plan.sh").is_file())
        self.assertFalse((target / ".specify/extensions.yml").exists())

    def test_setup_rejects_escaping_task_path_before_creating_runtime(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"governance": {"tasks_dir": "../outside"}}))
        with self.assertRaisesRegex(ValueError, "relative and contained"):
            TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        self.assertFalse((self.root / ".forgeflow/runtime").exists())


if __name__ == "__main__":
    unittest.main()
