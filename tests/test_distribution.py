"""
Unit and Integration Tests for ForgeFlow Multi-User Distribution & install.sh
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from forgeflow import __version__


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ff-dist-test-"))
        self.prefix = self.temp_dir / "opt_forgeflow"
        self.bin_dir = self.temp_dir / "global_bin"
        self.repo_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_installer(self, *extra_args):
        installer_script = self.repo_root / "install.sh"
        cmd = [
            "bash",
            str(installer_script),
            "--prefix",
            str(self.prefix),
            "--bin-dir",
            str(self.bin_dir),
            *extra_args,
        ]
        return subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)

    def test_package_accumulation_and_current_symlink(self):
        # 1. Install current version
        res = self._run_installer()
        self.assertEqual(res.returncode, 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")

        # Check directories
        pkg_dir = self.prefix / "packages" / __version__
        self.assertTrue(pkg_dir.is_dir(), "Package directory must exist")
        self.assertTrue((pkg_dir / "lib" / "forgeflow" / "__init__.py").is_file(), "Library files must exist")
        self.assertTrue((pkg_dir / "bin" / "forgeflow").is_file(), "Launcher must exist")
        self.assertTrue((pkg_dir / "bin" / "harness").is_symlink(), "Harness compatibility symlink must exist")

        # Check current symlink
        current_link = self.prefix / "current"
        self.assertTrue(current_link.is_symlink(), "Current symlink must exist")
        self.assertEqual(os.readlink(current_link), f"packages/{__version__}")

        # Check bin symlinks
        self.assertTrue((self.prefix / "bin" / "forgeflow").is_symlink())
        self.assertTrue((self.bin_dir / "forgeflow").is_symlink())
        self.assertTrue((self.bin_dir / "harness").is_symlink())

        # Check package.json metadata
        meta_file = pkg_dir / "package.json"
        self.assertTrue(meta_file.is_file())
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        self.assertEqual(meta["version"], __version__)
        self.assertEqual(meta["name"], "forgeflow")

    def test_launcher_execution_and_pythonpath(self):
        res = self._run_installer()
        self.assertEqual(res.returncode, 0)

        # Isolated environment without user site packages to ensure launcher sets PYTHONPATH correctly
        isolated_env = os.environ.copy()
        isolated_env["PYTHONNOUSERSITE"] = "1"
        isolated_env.pop("PYTHONPATH", None)

        # 1. Run forgeflow version via global bin symlink
        cmd = [str(self.bin_dir / "forgeflow"), "version"]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=isolated_env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"ForgeFlow v{__version__}", proc.stdout)

        # 2. Run forgeflow check --help
        check_proc = subprocess.run([str(self.bin_dir / "forgeflow"), "check", "--help"], capture_output=True, text=True, env=isolated_env)
        self.assertEqual(check_proc.returncode, 0)
        self.assertIn("Run ForgeFlow governance gate audit", check_proc.stdout)

        # 3. Test multi-level chained symlink (extra_bin -> global_bin -> prefix/bin -> pkg/bin)
        extra_bin = self.temp_dir / "extra_bin"
        extra_bin.mkdir(parents=True, exist_ok=True)
        chained_link = extra_bin / "forgeflow"
        chained_link.symlink_to(self.bin_dir / "forgeflow")

        chain_proc = subprocess.run([str(chained_link), "version"], capture_output=True, text=True, env=isolated_env)
        self.assertEqual(chain_proc.returncode, 0, chain_proc.stderr)
        self.assertIn(f"ForgeFlow v{__version__}", chain_proc.stdout)

    def test_harness_backward_compatibility(self):
        res = self._run_installer()
        self.assertEqual(res.returncode, 0)

        # Run harness version via global bin symlink
        cmd = [str(self.bin_dir / "harness"), "version"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(__version__, proc.stdout)

    def test_installer_flags_rollback_and_retention(self):
        # 1. Install current version
        res = self._run_installer()
        self.assertEqual(res.returncode, 0)

        # 2. Simulate historical packages 0.0.8, 0.0.9
        for fake_ver in ("0.0.8", "0.0.9"):
            fake_dir = self.prefix / "packages" / fake_ver
            fake_dir.mkdir(parents=True, exist_ok=True)
            (fake_dir / "bin").mkdir(exist_ok=True)
            (fake_dir / "bin" / "forgeflow").write_text("#!/bin/sh\necho fake", encoding="utf-8")
            (fake_dir / "bin" / "harness").symlink_to("forgeflow")

        # 3. Test rollback to 0.0.9
        rb_res = self._run_installer("--rollback", "0.0.9")
        self.assertEqual(rb_res.returncode, 0, rb_res.stderr)
        self.assertEqual(os.readlink(self.prefix / "current"), "packages/0.0.9")

        # 4. Test re-installing current version switches current back
        res2 = self._run_installer("--force")
        self.assertEqual(res2.returncode, 0)
        self.assertEqual(os.readlink(self.prefix / "current"), f"packages/{__version__}")

        # 5. Test retention pruning with --keep 2
        prune_res = self._run_installer("--force", "--keep", "2")
        self.assertEqual(prune_res.returncode, 0)
        remaining = sorted([p.name for p in (self.prefix / "packages").iterdir() if p.is_dir()])
        self.assertLessEqual(len(remaining), 2)
        self.assertIn(__version__, remaining)


if __name__ == "__main__":
    unittest.main()
