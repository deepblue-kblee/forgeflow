"""
Unit and Integration Tests for ForgeFlow Multi-User Distribution & install.sh
"""

import json
import os
import re
import shlex
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
        test_env = dict(os.environ, FORGEFLOW_SKILLS_DIR=str(self.temp_dir / "skills"))
        return subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, env=test_env)

    def test_package_accumulation_and_current_symlink(self):
        # 1. Install current version
        res = self._run_installer()
        self.assertEqual(res.returncode, 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")

        # Check directories
        pkg_dir = (self.prefix / "current").resolve()
        self.assertTrue(pkg_dir.is_dir(), "Package directory must exist")
        self.assertTrue((pkg_dir / "lib" / "forgeflow" / "__init__.py").is_file(), "Library files must exist")
        self.assertTrue((pkg_dir / "bin" / "forgeflow").is_file(), "Launcher must exist")
        self.assertEqual((pkg_dir / "scripts/install-skills.sh").read_bytes(),
                         (self.repo_root / "scripts/install-skills.sh").read_bytes())

        # Check current symlink
        current_link = self.prefix / "current"
        self.assertTrue(current_link.is_symlink(), "Current symlink must exist")
        self.assertTrue(os.readlink(current_link).startswith(f"packages/{__version__}-"))

        # Check bin symlinks
        self.assertTrue((self.prefix / "bin" / "forgeflow").is_symlink())
        self.assertTrue((self.bin_dir / "forgeflow").is_symlink())

        # Check package.json metadata
        meta_file = pkg_dir / "package.json"
        self.assertTrue(meta_file.is_file())
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        self.assertEqual(meta["version"], __version__)
        self.assertEqual(meta["name"], "forgeflow")
        self.assertEqual(pkg_dir.name, f"{__version__}-{meta['content_identity'][:16]}")

    def test_dry_run_does_not_publish_runtime_or_skills(self):
        result = self._run_installer("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.prefix.exists())
        self.assertFalse((self.temp_dir / "skills").exists())
        self.assertIn("Generate skills", result.stdout)

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
        check_proc = subprocess.run([str(self.bin_dir / "forgeflow"), "workflow", "--help"], capture_output=True, text=True, env=isolated_env)
        self.assertEqual(check_proc.returncode, 0)
        self.assertIn("usage: forgeflow workflow", check_proc.stdout)

        # 3. Test multi-level chained symlink (extra_bin -> global_bin -> prefix/bin -> pkg/bin)
        extra_bin = self.temp_dir / "extra_bin"
        extra_bin.mkdir(parents=True, exist_ok=True)
        chained_link = extra_bin / "forgeflow"
        chained_link.symlink_to(self.bin_dir / "forgeflow")

        chain_proc = subprocess.run([str(chained_link), "version"], capture_output=True, text=True, env=isolated_env)
        self.assertEqual(chain_proc.returncode, 0, chain_proc.stderr)
        self.assertIn(f"ForgeFlow v{__version__}", chain_proc.stdout)

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

        # A legacy package has no matching skill generator, so rollback must
        # preserve the current complete CLI/spec/skill distribution.
        active_before = os.readlink(self.prefix / "current")
        skill_before = (self.temp_dir / "skills/forgeflow/SKILL.md").read_bytes()
        rb_res = self._run_installer("--rollback", "0.0.9")
        self.assertNotEqual(rb_res.returncode, 0)
        self.assertIn("no restorable skill generator", rb_res.stderr)
        self.assertEqual(os.readlink(self.prefix / "current"), active_before)
        self.assertEqual((self.temp_dir / "skills/forgeflow/SKILL.md").read_bytes(), skill_before)

        # 4. Test re-installing current version switches current back
        res2 = self._run_installer("--force")
        self.assertEqual(res2.returncode, 0)
        self.assertTrue(os.readlink(self.prefix / "current").startswith(f"packages/{__version__}-"))

        # 5. Test retention pruning with --keep 2
        prune_res = self._run_installer("--force", "--keep", "2")
        self.assertEqual(prune_res.returncode, 0)
        remaining = sorted([p.name for p in (self.prefix / "packages").iterdir() if p.is_dir()])
        self.assertLessEqual(len(remaining), 2)
        self.assertIn((self.prefix / "current").resolve().name, remaining)

    def test_same_version_different_content_gets_a_distinct_build(self):
        fixture = self.temp_dir / "fixture"
        (fixture / "src").mkdir(parents=True)
        (fixture / "scripts").mkdir()
        shutil.copytree(self.repo_root / "src/forgeflow", fixture / "src/forgeflow",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(self.repo_root / "install.sh", fixture / "install.sh")
        shutil.copyfile(self.repo_root / "scripts/install-skills.sh", fixture / "scripts/install-skills.sh")
        env = dict(os.environ, FORGEFLOW_SKILLS_DIR=str(self.temp_dir / "skills"))
        cmd = ["bash", str(fixture / "install.sh"), "--prefix", str(self.prefix),
               "--bin-dir", str(self.bin_dir), "--keep", "0"]
        first = subprocess.run(cmd, cwd=fixture, env=env, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        original = (self.prefix / "current").resolve()
        # A same-version template change must identify a new build while the
        # original package remains available for an existing baseline.
        template = fixture / "src/forgeflow/templates/speckit/scripts/bash/common.sh"
        template.write_text(template.read_text() + "\n# Same-version test build.\n")
        second = subprocess.run(cmd, cwd=fixture, env=env, capture_output=True, text=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(original, (self.prefix / "current").resolve())
        self.assertTrue(original.is_dir())
        self.assertNotIn("Same-version test build.",
                         (original / "lib/forgeflow/templates/speckit/scripts/bash/common.sh").read_text())

    def test_rollback_restores_skills_from_the_selected_build_generator(self):
        fixture = self.temp_dir / "rollback-fixture"
        (fixture / "src").mkdir(parents=True)
        (fixture / "scripts").mkdir()
        shutil.copytree(self.repo_root / "src/forgeflow", fixture / "src/forgeflow",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(self.repo_root / "install.sh", fixture / "install.sh")
        generator = fixture / "scripts/install-skills.sh"
        shutil.copyfile(self.repo_root / "scripts/install-skills.sh", generator)
        env = dict(os.environ, FORGEFLOW_SKILLS_DIR=str(self.temp_dir / "skills"))
        command = ["bash", str(fixture / "install.sh"), "--prefix", str(self.prefix),
                   "--bin-dir", str(self.bin_dir), "--keep", "0"]
        first = subprocess.run(command, cwd=fixture, env=env, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        original = (self.prefix / "current").resolve()
        first_skills = {name: (self.temp_dir / "skills" / name / "SKILL.md").read_bytes()
                        for name in ("forgeflow", "setup-forgeflow", "update-forgeflow", "forgeflow-graphify")}
        generator.write_text(generator.read_text().replace("# forgeflow\n", "# forgeflow\n\nSecond build marker.\n"))
        second = subprocess.run(command, cwd=fixture, env=env, capture_output=True, text=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(original, (self.prefix / "current").resolve())
        self.assertIn("Second build marker.", (self.temp_dir / "skills/forgeflow/SKILL.md").read_text())
        rolled_back = subprocess.run([*command, "--rollback", original.name], cwd=fixture, env=env,
                                     capture_output=True, text=True)
        self.assertEqual(rolled_back.returncode, 0, rolled_back.stderr)
        self.assertEqual((self.prefix / "current").resolve(), original)
        for name, content in first_skills.items():
            self.assertEqual((self.temp_dir / "skills" / name / "SKILL.md").read_bytes(), content, name)

    def test_failed_rollback_generator_preserves_active_cli_and_skills(self):
        installed = self._run_installer()
        self.assertEqual(installed.returncode, 0, installed.stderr)
        current = (self.prefix / "current").resolve()
        skill_before = (self.temp_dir / "skills/forgeflow/SKILL.md").read_bytes()
        failing = self.prefix / "packages" / (__version__ + "-deadbeef")
        shutil.copytree(current, failing, symlinks=True)
        (failing / "scripts/install-skills.sh").write_text("#!/bin/sh\nexit 17\n")
        result = self._run_installer("--rollback", failing.name)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.prefix / "current").resolve(), current)
        self.assertEqual((self.temp_dir / "skills/forgeflow/SKILL.md").read_bytes(), skill_before)
        self.assertIn("generation failed", result.stderr)

    def _marked_rollback_package(self):
        installed = self._run_installer()
        self.assertEqual(installed.returncode, 0, installed.stderr)
        current = (self.prefix / "current").resolve()
        package = self.prefix / "packages" / (__version__ + "-abcdef01")
        shutil.copytree(current, package, symlinks=True)
        generator = package / "scripts/install-skills.sh"
        generator.write_text(generator.read_text() + """
for name in setup-forgeflow update-forgeflow forgeflow forgeflow-graphify; do
  printf '\\nNew rollback marker.\\n' >> "$FORGEFLOW_SKILLS_DIR/$name/SKILL.md"
done
""")
        return current, package

    def test_invalid_later_skill_destination_preserves_all_earlier_skills(self):
        current, package = self._marked_rollback_package()
        skills = self.temp_dir / "skills"
        shutil.rmtree(skills / "update-forgeflow")
        (skills / "update-forgeflow").write_text("User file must survive.\n")
        before = {path.relative_to(skills): path.read_bytes()
                  for path in skills.rglob("*") if path.is_file()}
        result = self._run_installer("--rollback", package.name)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid skill destination", result.stderr)
        self.assertEqual((self.prefix / "current").resolve(), current)
        after = {path.relative_to(skills): path.read_bytes()
                 for path in skills.rglob("*") if path.is_file()}
        self.assertEqual(after, before)

    def test_later_skill_publish_failure_restores_every_previous_skill(self):
        current, package = self._marked_rollback_package()
        skills = self.temp_dir / "skills"
        before = {path.relative_to(skills): path.read_bytes()
                  for path in skills.rglob("*") if path.is_file()}
        fake_bin = self.temp_dir / "fake-bin"
        fake_bin.mkdir()
        fake_mv = fake_bin / "mv"
        real_mv = shutil.which("mv")
        fake_mv.write_text("""#!/bin/sh
for arg in "$@"; do
  case "$arg" in */.forgeflow-skills.*/new/update-forgeflow) exit 19 ;; esac
done
exec "$FORGEFLOW_TEST_REAL_MV" "$@"
""")
        fake_mv.chmod(0o755)
        env = dict(os.environ, FORGEFLOW_SKILLS_DIR=str(skills),
                   FORGEFLOW_TEST_REAL_MV=real_mv, PATH=str(fake_bin) + os.pathsep + os.environ["PATH"])
        result = subprocess.run(["bash", str(self.repo_root / "install.sh"), "--prefix", str(self.prefix),
                                 "--bin-dir", str(self.bin_dir), "--rollback", package.name],
                                cwd=self.repo_root, env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("restoring the previous skills", result.stderr)
        self.assertEqual((self.prefix / "current").resolve(), current)
        after = {path.relative_to(skills): path.read_bytes()
                 for path in skills.rglob("*") if path.is_file()}
        self.assertEqual(after, before)
        self.assertFalse(list(skills.glob(".forgeflow-skills.*")))

    def test_installed_and_pinned_spec_adr_links_resolve(self):
        installed = self._run_installer()
        self.assertEqual(installed.returncode, 0, installed.stderr)
        package = (self.prefix / "current").resolve() / "lib/forgeflow"
        project = self.temp_dir / "adr-project"
        project.mkdir()
        env = dict(os.environ, PYTHONNOUSERSITE="1")
        env.pop("PYTHONPATH", None)
        initialized = subprocess.run([str(self.bin_dir / "forgeflow"), "init", "--path", str(project), "--json"],
                                     cwd=project, env=env, capture_output=True, text=True)
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        baseline = json.loads((project / ".forgeflow/runtime.json").read_text())
        for root in (package, Path(baseline["path"])):
            self.assertTrue((root / "spec/FLOW_SPEC.md").is_file())
            self.assertEqual((root / "CHANGELOG.md").read_bytes(),
                             (self.repo_root / "src/forgeflow/CHANGELOG.md").read_bytes())
        history = subprocess.run([*shlex.split(baseline["command"]), "doc", "show", "CHANGELOG", "--json"],
                                 cwd=project, env=env, capture_output=True, text=True)
        self.assertEqual(history.returncode, 0, history.stderr)
        history_result = json.loads(history.stdout)
        self.assertEqual(Path(history_result["path"]), Path(baseline["path"]) / "CHANGELOG.md")
        self.assertEqual(history_result["content"],
                         (self.repo_root / "src/forgeflow/CHANGELOG.md").read_text())


if __name__ == "__main__":
    unittest.main()
