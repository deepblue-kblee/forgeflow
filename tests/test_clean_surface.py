"""0.2.x clean-init surface and removed 0.1.x legacy surface (issue #14)."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import forgeflow


class TestCleanSurface(unittest.TestCase):
    def test_legacy_cli_commands_are_not_exposed(self):
        for command in ("release", "lifecycle", "migrate", "task", "check"):
            result = subprocess.run([sys.executable, "-m", "forgeflow.cli", command],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0,
                                f"legacy command '{command}' must not be available")
            self.assertIn("invalid choice", result.stderr)

    def test_package_has_no_legacy_modules(self):
        package_dir = Path(forgeflow.__file__).parent
        for module in ("lifecycle.py", "harness.py", "migration.py", "legacy_assets.py"):
            self.assertFalse((package_dir / module).exists(),
                             f"legacy module {module} must not ship in the package")

    def test_init_does_not_create_tasks_directory(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="ff-clean-init-"))
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
        result = subprocess.run([sys.executable, "-m", "forgeflow.cli", "init", "demo", "--json"],
                                cwd=temp_dir, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((temp_dir / "demo" / "tasks").exists())


if __name__ == "__main__":
    unittest.main()
