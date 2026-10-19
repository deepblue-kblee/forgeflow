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
