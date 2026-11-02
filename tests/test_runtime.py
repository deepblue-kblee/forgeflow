"""Executable content identity, baseline continuity, and safe project paths."""

import json
import importlib.util
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import forgeflow.runtime as runtime_module
from forgeflow.runtime import assert_runtime, package_identity, pin_runtime
from forgeflow.scaffold import TemplateScaffolder


class TestRuntimeBaseline(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self):
        self.temporary.cleanup()

    def test_same_version_different_bytes_change_identity_and_caches_do_not(self):
        package = self.root / "package"
        package.mkdir()
        (package / "_version.py").write_text('__version__ = "0.1.25"\n')
        (package / "cli.py").write_text("before\n")
        before = package_identity(package)
        (package / "__pycache__").mkdir()
        (package / "__pycache__/cli.cpython.pyc").write_bytes(b"cache")
        self.assertEqual(package_identity(package), before)
        (package / "cli.py").write_text("after\n")
        self.assertNotEqual(package_identity(package), before)

    def test_pin_is_executable_idempotent_and_independent_of_global_current(self):
        baseline = pin_runtime(self.root)
        launcher = self.root / ".forgeflow/run.py"
        first_mtime = launcher.stat().st_mtime_ns
        self.assertEqual(pin_runtime(self.root), baseline)
        self.assertEqual(launcher.stat().st_mtime_ns, first_mtime)
        assert_runtime(self.root, baseline)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(self.root / "missing-global-runtime")
        result = subprocess.run([sys.executable, str(launcher), "--runtime-identity", baseline["identity"], "--version"],
                                cwd=self.root, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ForgeFlow", result.stdout)

    def test_executing_runtime_drift_points_to_recorded_snapshot(self):
        baseline = pin_runtime(self.root)
        actual_identity = package_identity
        def different_current(package_dir=None):
            return "f" * 64 if package_dir is None else actual_identity(package_dir)
        with patch("forgeflow.runtime.package_identity", side_effect=different_current):
            with self.assertRaisesRegex(ValueError, "--runtime-identity " + baseline["identity"]):
                assert_runtime(self.root, baseline)

    def test_two_same_version_snapshots_remain_independently_executable(self):
        first = pin_runtime(self.root)
        replacement = self.root / "replacement" / "forgeflow"
        shutil.copytree(Path(runtime_module.__file__).parent, replacement,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        cli = replacement / "cli.py"
        cli.write_text(cli.read_text() + "\n# same version, different release bytes\n")
        spec = replacement / "spec/FLOW_SPEC.md"
        spec.write_text(spec.read_text() + "\nReplacement baseline marker.\n")
        with patch.object(runtime_module, "__file__", str(replacement / "runtime.py")):
            second = pin_runtime(self.root)
        self.assertEqual(first["version"], second["version"])
        self.assertNotEqual(first["identity"], second["identity"])
        for baseline in (first, second):
            result = subprocess.run([sys.executable, str(self.root / ".forgeflow/run.py"),
                                     "--runtime-identity", baseline["identity"], "--version"],
                                    cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ForgeFlow", result.stdout)
            document = subprocess.run([sys.executable, str(self.root / ".forgeflow/run.py"),
                                       "--runtime-identity", baseline["identity"], "doc", "show", "FLOW_SPEC"],
                                      cwd=self.root, capture_output=True, text=True)
            self.assertEqual(document.returncode, 0, document.stderr)
            self.assertEqual("Replacement baseline marker." in document.stdout,
                             baseline["identity"] == second["identity"])

    def test_launcher_rejects_tampered_snapshot_before_importing_it(self):
        baseline = pin_runtime(self.root)
        source = Path(baseline["path"]) / "cli.py"
        source.write_text(source.read_text() + "\n# changed\n")
        result = subprocess.run([sys.executable, str(self.root / ".forgeflow/run.py"), "--version"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot changed", result.stderr)
        with self.assertRaisesRegex(ValueError, "damaged"):
            assert_runtime(self.root, baseline)

    def test_pinned_docs_follow_runtime_from_another_project_and_allow_explicit_path(self):
        baseline = pin_runtime(self.root)
        other = self.root / "another-project"
        docs = other / "docs/spec"
        docs.mkdir(parents=True)
        (other / ".forgeflow").mkdir()
        (other / ".forgeflow/config.json").write_text("{}\n")
        (docs / "FLOW_SPEC.md").write_text("Other project rules marker.\n")
        command = [sys.executable, str(self.root / ".forgeflow/run.py"),
                   "--runtime-identity", baseline["identity"], "doc", "show", "FLOW_SPEC"]
        pinned = subprocess.run(command, cwd=other, capture_output=True, text=True)
        self.assertEqual(pinned.returncode, 0, pinned.stderr)
        self.assertNotIn("Other project rules marker.", pinned.stdout)
        explicit = subprocess.run(command + ["--path", str(docs)], cwd=other,
                                  capture_output=True, text=True)
        self.assertEqual(explicit.returncode, 0, explicit.stderr)
        self.assertIn("Other project rules marker.", explicit.stdout)

    def test_launcher_ignores_unchecked_bytecode_inside_snapshot(self):
        baseline = pin_runtime(self.root)
        source = self.root / "untrusted.py"
        source.write_text('raise SystemExit("untrusted cached code executed")\n')
        cached = Path(importlib.util.cache_from_source(str(Path(baseline["path"]) / "cli.py")))
        cached.parent.mkdir(parents=True, exist_ok=True)
        py_compile.compile(str(source), cfile=str(cached),
                           invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        self.assertEqual(package_identity(baseline["path"]), baseline["identity"])
        result = subprocess.run([sys.executable, str(self.root / ".forgeflow/run.py"), "--version"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ForgeFlow", result.stdout)
        self.assertTrue(cached.exists(), "The launcher must preserve cache files, not delete them")

    def test_user_launcher_and_symlink_parents_are_preserved(self):
        (self.root / ".forgeflow").mkdir()
        launcher = self.root / ".forgeflow/run.py"
        launcher.write_text("# user launcher\n")
        with self.assertRaisesRegex(ValueError, "user file"):
            pin_runtime(self.root)
        self.assertEqual(launcher.read_text(), "# user launcher\n")
        launcher.unlink()
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / ".forgeflow/runtime").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symbolic link"):
            pin_runtime(self.root)
        self.assertFalse(list(outside.iterdir()))

    def test_user_spec_directory_and_unknown_symlink_are_never_removed(self):
        (self.root / ".forgeflow/spec").mkdir(parents=True)
        sentinel = self.root / ".forgeflow/spec/local.md"
        sentinel.write_text("keep\n")
        with self.assertRaisesRegex(ValueError, "user directory"):
            pin_runtime(self.root)
        self.assertEqual(sentinel.read_text(), "keep\n")
        sentinel.unlink()
        sentinel.parent.rmdir()
        outside = self.root / "custom-spec"
        outside.mkdir()
        sentinel.parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "unrecognized user"):
            pin_runtime(self.root)
        self.assertTrue(sentinel.parent.is_symlink())

    def test_setup_does_not_rewrite_external_root_guide(self):
        outside = self.root / "outside.md"
        outside.write_text("# external rules\n")
        (self.root / "AGENTS.md").symlink_to(outside)
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        self.assertEqual(outside.read_text(), "# external rules\n")
        self.assertTrue((self.root / "AGENTS.md").is_symlink())

    def test_update_blocks_active_lean_and_legacy_work_before_mutation(self):
        TemplateScaffolder.scaffold_speckit_hybrid(self.root)
        config_path = self.root / ".forgeflow/config.json"
        original = config_path.read_bytes()
        baseline_path = self.root / ".forgeflow/runtime.json"
        baseline = baseline_path.read_bytes()
        state = self.root / ".forgeflow/workflows/task.json"
        state.parent.mkdir()
        for status in ("planned", "verification-failed", "ready", "integrated"):
            state.write_text(json.dumps({"status": status}))
            result = TemplateScaffolder.update_repo_governance(self.root)
            self.assertEqual(result["status"], "needs-action")
            self.assertTrue(any(item["kind"] == "active-work" for item in result["blockers"]))
            self.assertEqual(config_path.read_bytes(), original)
            self.assertEqual(baseline_path.read_bytes(), baseline)
        state.write_text(json.dumps({"status": "ready", "finalization_complete": True}))
        self.assertIn(
            TemplateScaffolder.update_repo_governance(self.root)["status"],
            {"applied", "no-op"},
        )
        package = self.root / "tasks/in-progress/v0.1.24-unfinished"
        package.mkdir()
        (package / "spec.md").write_text("# unfinished\n")
        result = TemplateScaffolder.update_repo_governance(self.root)
        self.assertEqual(result["status"], "needs-action")
        self.assertTrue(any(item.get("task") == "v0.1.24-unfinished" for item in result["blockers"]))
        self.assertEqual((package / "spec.md").read_text(), "# unfinished\n")


if __name__ == "__main__":
    unittest.main()
