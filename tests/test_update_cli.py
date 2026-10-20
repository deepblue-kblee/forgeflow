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


if __name__ == "__main__":
    unittest.main()
