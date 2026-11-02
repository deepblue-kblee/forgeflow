import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from forgeflow._version import __version__
from forgeflow.cli import handle_update, parse_forgeflow_args
from forgeflow.scaffold import TemplateScaffolder


class TestUpdateCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_update_refreshes_current_project_without_tasks(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config_path = self.root / ".forgeflow/config.json"
        config = json.loads(config_path.read_text())
        config["forgeflow_version"] = "0.1.0"
        config["custom_key"] = "preserved"
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

        args = parse_forgeflow_args(["update", "--path", str(self.root), "--json"])
        code = handle_update(args)
        self.assertEqual(code, 0)
        updated = json.loads(config_path.read_text())
        self.assertEqual(updated["forgeflow_version"], __version__)
        self.assertEqual(updated["custom_key"], "preserved")
        self.assertFalse((self.root / "tasks").exists())

    def test_update_rejects_legacy_layout(self):
        legacy = {"forgeflow_version": "0.1.24", "governance": {"tasks_dir": "tasks"}}
        (self.root / ".forgeflow.json").write_text(json.dumps(legacy), encoding="utf-8")
        (self.root / "tasks/in-progress").mkdir(parents=True)
        args = parse_forgeflow_args(["update", "--path", str(self.root), "--json"])
        code = handle_update(args)
        self.assertEqual(code, 3)

    def test_update_dry_run_does_not_write(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config_path = self.root / ".forgeflow/config.json"
        config = json.loads(config_path.read_text())
        config["forgeflow_version"] = "0.1.0"
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        before = config_path.read_bytes()
        args = parse_forgeflow_args(["update", "--path", str(self.root), "--dry-run", "--json"])
        with patch("builtins.print") as printed:
            code = handle_update(args)
            output = json.loads(printed.call_args[0][0])
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "planned")
        self.assertEqual(config_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
