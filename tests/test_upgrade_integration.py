import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from forgeflow._version import __version__
from forgeflow.cli import handle_upgrade, parse_forgeflow_args

REPO_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("git"), "git is required for a real source fixture")
class TestUpgradeFromLocalSource(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.prefix = self.base / "prefix"
        self.bin_dir = self.base / "bin"
        self.skills = self.base / "skills"
        for name in ("src", "scripts"):
            shutil.copytree(REPO_ROOT / name, self.source / name)
        shutil.copy2(REPO_ROOT / "install.sh", self.source / "install.sh")
        subprocess.run(["git", "init", "-q"], cwd=self.source, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "user.email=test@example.invalid", "-c", "user.name=test", "commit", "-qm", "fixture"],
            cwd=self.source,
            check=True,
        )
        subprocess.run(["git", "branch", "-M", "main"], cwd=self.source, check=True)

    def tearDown(self):
        self.temp.cleanup()

    def _run_upgrade(self, *extra):
        env = {
            "FORGEFLOW_INSTALL_DIR": str(self.prefix),
            "FORGEFLOW_BIN_DIR": str(self.bin_dir),
            "FORGEFLOW_SKILLS_DIR": str(self.skills),
            "FORGEFLOW_REPO": str(self.source),
        }
        args = parse_forgeflow_args(
            ["upgrade", "--force", "--json", "--repo-url", self.source.as_uri(), *extra]
        )
        with patch.dict(os.environ, env, clear=False), patch("builtins.print") as printed:
            code = handle_upgrade(args)
            output = json.loads(printed.call_args[0][0])
        return code, output

    def test_real_installer_and_entrypoint_are_verified(self):
        code, output = self._run_upgrade()
        self.assertEqual(code, 0, output)
        self.assertEqual(output["status"], "success")
        self.assertTrue(output["upgraded"])
        self.assertEqual(output["current_version"], __version__)
        self.assertEqual(output["observed"]["source_identity"], output["source_identity"])

        metadata = json.loads((self.prefix / "current/package.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["version"], __version__)
        self.assertEqual(metadata["source_identity"], output["source_identity"])
        self.assertTrue(metadata["content_identity"])
        self.assertTrue((self.prefix / "current/lib/forgeflow/spec/README.md").is_file())
        for name in ("setup-forgeflow", "update-forgeflow", "forgeflow", "forgeflow-graphify"):
            self.assertTrue((self.skills / name / "SKILL.md").is_file(), name)

        probe = subprocess.run([str(self.bin_dir / "forgeflow"), "version"], capture_output=True, text=True)
        self.assertEqual(probe.returncode, 0)
        self.assertIn(f"v{__version__}", probe.stdout)

    def test_failed_activation_keeps_previous_current(self):
        code, output = self._run_upgrade()
        self.assertEqual(code, 0, output)
        previous = (self.prefix / "current").resolve()
        skills_file = self.base / "skills-is-a-file"
        skills_file.write_text("not a directory\n", encoding="utf-8")
        env = {
            "FORGEFLOW_INSTALL_DIR": str(self.prefix),
            "FORGEFLOW_BIN_DIR": str(self.bin_dir),
            "FORGEFLOW_SKILLS_DIR": str(skills_file),
            "FORGEFLOW_REPO": str(self.source),
        }
        args = parse_forgeflow_args(
            ["upgrade", "--force", "--json", "--repo-url", self.source.as_uri()]
        )
        with patch.dict(os.environ, env, clear=False), patch("builtins.print") as printed:
            code = handle_upgrade(args)
            failure = json.loads(printed.call_args[0][0])
        self.assertNotEqual(code, 0)
        self.assertFalse(failure["upgraded"])
        self.assertEqual((self.prefix / "current").resolve(), previous)
        probe = subprocess.run([str(self.bin_dir / "forgeflow"), "version"], capture_output=True, text=True)
        self.assertEqual(probe.returncode, 0)

    def test_installed_launcher_resolves_custom_prefix_without_env(self):
        code, output = self._run_upgrade()
        self.assertEqual(code, 0, output)
        env = {key: value for key, value in os.environ.items() if not key.startswith("FORGEFLOW_")}
        env["HOME"] = str(self.base / "empty-home")
        probe = subprocess.run(
            [str(self.bin_dir / "forgeflow"), "upgrade", "--check", "--json", "--repo-url", self.source.as_uri()],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        payload = json.loads(probe.stdout)
        self.assertEqual(payload["target"]["prefix"], str(self.prefix.resolve()))
        self.assertEqual(payload["target"]["bin_dir"], str(self.bin_dir.absolute()))
        self.assertEqual(payload["target"]["skills_dir"], str(self.skills.absolute()))

    def test_same_version_same_build_reports_up_to_date(self):
        code, output = self._run_upgrade()
        self.assertEqual(code, 0, output)
        env = {
            "FORGEFLOW_INSTALL_DIR": str(self.prefix),
            "FORGEFLOW_BIN_DIR": str(self.bin_dir),
            "FORGEFLOW_SKILLS_DIR": str(self.skills),
            "FORGEFLOW_REPO": str(self.source),
        }
        args = parse_forgeflow_args(
            ["upgrade", "--check", "--json", "--repo-url", self.source.as_uri()]
        )
        with patch.dict(os.environ, env, clear=False), patch("builtins.print") as printed:
            code = handle_upgrade(args)
            check = json.loads(printed.call_args[0][0])
        self.assertEqual(code, 0, check)
        self.assertEqual(check["identity_comparison"], "same")
        self.assertFalse(check["upgrade_available"])
        self.assertEqual(check["current_version"], __version__)


if __name__ == "__main__":
    unittest.main()
