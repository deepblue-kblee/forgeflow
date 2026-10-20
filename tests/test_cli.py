#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forgeflow.scaffold import TemplateScaffolder
from forgeflow._version import __version__


class TestCliIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.rel_dir = self.temp_dir / "docs" / "releases" / "v0.1.0-test"
        TemplateScaffolder.create_release_scaffold(self.rel_dir, "v0.1.0-test", tier=2)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_harness_check_cli(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import harness_main; harness_main(['check', '--repo-root', '{self.temp_dir}', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI check failed: {res.stderr}")
        self.assertIn('"all_passed": true', res.stdout)

    def test_version_commands_report_the_canonical_version(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        forgeflow = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['version'])",
            ],
            capture_output=True,
            text=True,
        )
        harness = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import harness_main; harness_main(['version'])",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(forgeflow.returncode, 0, forgeflow.stderr)
        self.assertEqual(harness.returncode, 0, harness.stderr)
        self.assertIn(f"v{__version__}", forgeflow.stdout)
        self.assertIn(f"v{__version__}", harness.stdout)

    def test_forgeflow_review_cli(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        sample_file = self.temp_dir / "src" / "sample.py"
        sample_file.parent.mkdir(parents=True, exist_ok=True)
        sample_file.write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['review', '--repo-root', '{self.temp_dir}', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI review failed: {res.stderr}")
        self.assertIn('"passed": true', res.stdout)

    def test_forgeflow_init_project_cli(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        target_dir = self.temp_dir / "new_project"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['init', '--project', 'new_project', '--path', '{self.temp_dir}', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI init project failed: {res.stderr}")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["mode"], "project")
        self.assertTrue((target_dir / ".forgeflow.json").exists())
        self.assertTrue((target_dir / "tasks").exists())
        self.assertTrue((target_dir / "tasks" / "README.md").exists())

    def test_forgeflow_init_project_cli_selects_autonomous_policy(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        target_dir = self.temp_dir / "autonomous_project"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['init', '--project', 'autonomous_project', '--path', '{self.temp_dir}', '--continuation-policy', 'autonomous'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        config = json.loads((target_dir / ".forgeflow.json").read_text(encoding="utf-8"))
        self.assertEqual(config["governance"]["continuation_policy"], "autonomous")

    def test_forgeflow_init_no_target_forwards_autonomous_policy(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        target_dir = self.temp_dir / "no_target_project"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['init', '--path', '{target_dir}', '--continuation-policy', 'autonomous'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        config = json.loads((target_dir / ".forgeflow.json").read_text(encoding="utf-8"))
        self.assertEqual(config["governance"]["continuation_policy"], "autonomous")

    def test_forgeflow_init_project_cli_rejects_symlinked_parent(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        symlink_parent = self.temp_dir / "linked-parent"
        symlink_parent.symlink_to(outside, target_is_directory=True)
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['init', '--project', 'new_project', '--path', '{symlink_parent}'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Unsafe project path contains symlink", res.stderr)
        self.assertFalse((outside / "new_project").exists())

    def test_forgeflow_init_migrates_exact_legacy_binding(self):
        legacy_guide = self.temp_dir / "AGENTS.md"
        legacy_guide.write_text(TemplateScaffolder.LEGACY_BINDING, encoding="utf-8")
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['init', '--path', '{self.temp_dir}', '--migrate-governance-binding', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI migration failed: {res.stderr}")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["mode"], "project")
        migrated = legacy_guide.read_text(encoding="utf-8")
        self.assertNotIn(TemplateScaffolder.LEGACY_BINDING, migrated)
        self.assertIn(TemplateScaffolder.BINDING_START, migrated)

    def test_forgeflow_init_json_reports_updated_files_separately(self):
        TemplateScaffolder.init_project_governance(self.temp_dir, "test-proj")
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['init', '--path', '{self.temp_dir}', '--refresh-governance', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI refresh failed: {res.stderr}")
        payload = json.loads(res.stdout)
        governance_path = str(TemplateScaffolder.GOVERNANCE_PATH)
        self.assertIn(governance_path, payload["updated_files"])
        self.assertNotIn(governance_path, payload["created_files"])

    def test_forgeflow_init_release_cli(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['init', 'v0.3.0-feature', '--path', '{self.temp_dir}', '--tier', '3', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI init release failed: {res.stderr}")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["mode"], "release")
        self.assertEqual(payload["tier"], 3)
        self.assertTrue((self.temp_dir / "docs" / "releases" / "v0.3.0-feature" / "PRD.md").exists())

    def test_lifecycle_check_is_read_only_artifact_evidence_audit(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import harness_main; harness_main(['check', '--lifecycle', 'v0.1.0-test', '--repo-root', '{self.temp_dir}', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        payload = json.loads(res.stdout)
        self.assertFalse(payload["ok"])
        self.assertTrue(
            any(item.startswith("evidence_malformed:") for item in payload["unmet_conditions"])
        )
        self.assertIsInstance(payload["next_action"], str)
        self.assertFalse((self.temp_dir / ".forgeflow" / "lifecycle").exists())

    def test_forgeflow_check_forwards_lifecycle_evidence_audit(self):
        repo_src = Path(__file__).resolve().parent.parent / "src"
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{repo_src}'); from forgeflow.cli import main; main(['check', '--lifecycle', 'v0.1.0-test', '--repo-root', '{self.temp_dir}', '--json'])",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        payload = json.loads(res.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("strict_audit_not_run", payload["unmet_conditions"])


if __name__ == "__main__":
    unittest.main()

