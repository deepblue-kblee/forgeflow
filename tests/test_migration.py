import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from forgeflow import legacy_assets
from forgeflow._version import __version__
from forgeflow.cli import handle_update, parse_forgeflow_args
from forgeflow.migration import apply_update_plan, build_update_plan, update_project
from forgeflow.scaffold import TemplateScaffolder

FIXTURE = Path(__file__).parent / "fixtures" / "legacy_v0_1_24"


def _snapshot(root: Path):
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = ("link", os.readlink(path))
        elif path.is_file():
            result[relative] = ("file", path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        elif path.is_dir():
            result[relative] = ("dir",)
    return result


class TestLegacyMigration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        shutil.copytree(FIXTURE, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def _config(self):
        return json.loads((self.root / ".forgeflow/config.json").read_text(encoding="utf-8"))

    def test_m01_unmodified_v0124_project_becomes_lean(self):
        plan = build_update_plan(self.root)
        self.assertEqual(plan["status"], "planned")
        self.assertEqual(plan["conflicts"], [])
        self.assertEqual(plan["blockers"], [])

        result = update_project(self.root)
        self.assertEqual(result["status"], "applied")
        self.assertTrue(result["complete"])
        self.assertEqual((self.root / ".specify/memory/constitution.md").read_text(), legacy_assets.LEAN_CONSTITUTION)
        self.assertEqual((self.root / ".specify/extensions.yml").read_text(), legacy_assets.LEAN_EXTENSIONS)
        self.assertEqual(
            (self.root / ".specify/templates/commands/implement.md").read_text(),
            legacy_assets.LEAN_IMPLEMENT_COMMAND,
        )
        config = self._config()
        self.assertEqual(config["forgeflow_version"], __version__)
        self.assertEqual(config["workflow"]["mode"], "lean")
        self.assertTrue(config["governance"]["strict_mode"])
        self.assertNotIn("Gate 1", (self.root / ".specify/memory/constitution.md").read_text())
        self.assertNotIn("forgeflow-gatekeeper", (self.root / ".specify/extensions.yml").read_text())

        baseline = json.loads((self.root / ".forgeflow/runtime.json").read_text())
        self.assertTrue((self.root / baseline["path"] / "spec" / "README.md").is_file())
        probe = subprocess.run(
            ["python3", ".forgeflow/run.py", "version"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        self.assertIn(f"v{__version__}", probe.stdout)

        second = update_project(self.root)
        self.assertEqual(second["status"], "no-op")
        self.assertEqual(second["created_files"], [])
        self.assertEqual(second["updated_files"], [])

    def test_m02_user_modified_instruction_is_preserved_and_needs_action(self):
        path = self.root / ".specify/memory/constitution.md"
        path.write_text(path.read_text() + "\n사용자 추가 규칙\n", encoding="utf-8")
        before = path.read_bytes()

        plan = build_update_plan(self.root)
        self.assertEqual(plan["status"], "needs-action")
        self.assertTrue(any(item["path"] == ".specify/memory/constitution.md" for item in plan["conflicts"]))
        self.assertFalse((self.root / ".forgeflow/managed-assets.json").exists())
        self.assertEqual(path.read_bytes(), before)

        args = parse_forgeflow_args(["update", "--path", str(self.root), "--json"])
        with patch("builtins.print"):
            code = handle_update(args)
        self.assertEqual(code, 3)
        self.assertEqual(path.read_bytes(), before)

        accepted = update_project(self.root, accept_paths=[".specify/memory/constitution.md"])
        self.assertEqual(accepted["status"], "applied")
        self.assertIn(".specify/memory/constitution.md", accepted["accepted"])
        self.assertEqual(path.read_text(), legacy_assets.LEAN_CONSTITUTION)
        backup = self.root / accepted["backup_dir"] / ".specify/memory/constitution.md"
        self.assertIn("사용자 추가 규칙", backup.read_text())

    def test_m03_legacy_config_only_and_custom_tasks_dir(self):
        config_path = self.root / ".forgeflow/config.json"
        legacy_path = self.root / ".forgeflow.json"
        config = json.loads(config_path.read_text())
        config["governance"]["tasks_dir"] = "my-tasks"
        config["governance"]["custom_policy"] = "keep"
        legacy_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        config_path.unlink()

        result = update_project(self.root)
        self.assertEqual(result["status"], "applied")
        self.assertTrue(config_path.is_file())
        self.assertTrue(legacy_path.is_file())
        migrated = self._config()
        self.assertEqual(migrated["governance"]["tasks_dir"], "my-tasks")
        self.assertEqual(migrated["governance"]["custom_policy"], "keep")
        self.assertTrue((self.root / "my-tasks/in-progress").is_dir())
        self.assertIn(".forgeflow.json", result["preserved_files"])

    def test_m04_active_work_blocks_before_writing(self):
        state_dir = self.root / ".forgeflow/workflows"
        state_dir.mkdir(parents=True)
        state = {
            "id": "active",
            "status": "ready",
            "finalization_complete": False,
            "baseline": {
                "identity": "a" * 64,
                "version": "0.1.25",
                "command": "python3 .forgeflow/run.py --runtime-identity " + "a" * 64,
            },
        }
        (state_dir / "active.json").write_text(json.dumps(state), encoding="utf-8")
        before = _snapshot(self.root)

        plan = build_update_plan(self.root)
        self.assertEqual(plan["status"], "needs-action")
        blocked = [item for item in plan["blockers"] if item["kind"] == "active-work"]
        self.assertEqual(blocked[0]["task"], "active")
        self.assertIn("--runtime-identity", blocked[0]["next_action"])
        self.assertEqual(_snapshot(self.root), before)

    def test_m08_dry_run_and_plan_drift_never_write(self):
        before = _snapshot(self.root)
        plan = build_update_plan(self.root)
        self.assertEqual(build_update_plan(self.root)["status"], "planned")
        self.assertEqual(_snapshot(self.root), before)
        self.assertFalse((self.root / ".forgeflow/migrations").exists())
        self.assertFalse((self.root / ".forgeflow/migration-backups").exists())

        path = self.root / ".specify/memory/constitution.md"
        path.write_text("# user edit after plan\n", encoding="utf-8")
        changed = _snapshot(self.root)
        result = apply_update_plan(plan)
        self.assertEqual(result["status"], "needs-action")
        self.assertTrue(any(item["kind"] == "plan-drift" for item in result["blockers"]))
        self.assertEqual(_snapshot(self.root), changed)

    def test_m09_failed_apply_restores_managed_changes(self):
        before = _snapshot(self.root)
        real_write = __import__("forgeflow.migration", fromlist=["_write_text_atomic"])._write_text_atomic
        calls = {"count": 0}

        def fail_second(path, content, root):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("injected write failure")
            return real_write(path, content, root)

        with patch("forgeflow.migration._write_text_atomic", side_effect=fail_second):
            result = update_project(self.root)
        self.assertIn(result["status"], {"failed-rolled-back", "partial"})
        self.assertFalse(result["complete"])
        after = _snapshot(self.root)
        # Managed files are restored; journals/backups may remain as evidence.
        for path, value in before.items():
            if path.startswith(".forgeflow/migrations") or path.startswith(".forgeflow/migration-backups"):
                continue
            self.assertIn(path, after)
            self.assertEqual(after[path], value, path)

    def test_cli_dry_run_is_success_and_lists_planned_changes(self):
        args = parse_forgeflow_args(["update", "--path", str(self.root), "--dry-run", "--json"])
        with patch("builtins.print") as printed:
            code = handle_update(args)
            output = json.loads(printed.call_args[0][0])
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "planned")
        self.assertTrue(output["dry_run"])
        self.assertIn(".specify/memory/constitution.md", output["updated_files"])
        self.assertFalse((self.root / ".forgeflow/migrations").exists())
        self.assertFalse((self.root / ".forgeflow/migration-backups").exists())

    def test_recovery_rejects_unsafe_journal_paths(self):
        journal_dir = self.root / ".forgeflow/migrations"
        journal_dir.mkdir(parents=True)
        operation_id = "20260101T000000Z-abcdef123456"
        journal = journal_dir / f"{operation_id}.json"
        git_config = self.root / ".git/config"
        git_config.parent.mkdir()
        git_config.write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")
        before = git_config.read_bytes()
        journal.write_text(json.dumps({
            "id": operation_id,
            "status": "partial",
            "entries": [{
                "path": ".git/config",
                "operation": "replaced",
                "backup": ".forgeflow/migration-backups/x/.git/config",
            }],
        }), encoding="utf-8")
        from forgeflow.migration import recover_migration
        result = recover_migration(self.root, operation_id)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["restore_errors"])
        self.assertEqual(git_config.read_bytes(), before)

    def test_recovery_restores_recorded_backup(self):
        from forgeflow.migration import recover_migration
        target = self.root / ".specify/memory/constitution.md"
        original = target.read_bytes()
        backup = self.root / ".forgeflow/migration-backups/test/.specify/memory/constitution.md"
        backup.parent.mkdir(parents=True)
        backup.write_bytes(b"# previous managed content\n")
        journal_dir = self.root / ".forgeflow/migrations"
        journal_dir.mkdir(parents=True)
        operation_id = "20260101T000001Z-abcdef123456"
        new_hash = __import__("hashlib").sha256(target.read_bytes()).hexdigest()
        (journal_dir / f"{operation_id}.json").write_text(json.dumps({
            "id": operation_id,
            "status": "partial",
            "entries": [{
                "path": ".specify/memory/constitution.md",
                "operation": "replaced",
                "backup": ".forgeflow/migration-backups/test/.specify/memory/constitution.md",
                "new_sha256": new_hash,
            }],
        }), encoding="utf-8")
        result = recover_migration(self.root, operation_id)
        self.assertEqual(result["status"], "applied", result)
        self.assertEqual(target.read_text(), "# previous managed content\n")
        self.assertNotEqual(target.read_bytes(), original)

    def test_m10_report_matches_filesystem(self):
        result = update_project(self.root)
        self.assertEqual(result["status"], "applied")
        for relative in result["created_files"] + result["updated_files"]:
            path = self.root / relative
            self.assertTrue(path.exists() or path.is_symlink(), relative)
        for relative in result["preserved_files"]:
            self.assertTrue((self.root / relative).exists(), relative)
        self.assertTrue((self.root / result["backup_dir"]).is_dir())
        self.assertTrue((self.root / result["migration_record"]).is_file())
        manifest = json.loads((self.root / ".forgeflow/managed-assets.json").read_text())
        self.assertIn(".specify/memory/constitution.md", manifest["assets"])

    def test_explicit_strict_mode_preserves_legacy_instructions(self):
        config_path = self.root / ".forgeflow/config.json"
        config = json.loads(config_path.read_text())
        config["forgeflow_version"] = __version__
        config["workflow"] = {"mode": "strict", "owner": "standalone", "checks": []}
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        before = (self.root / ".specify/memory/constitution.md").read_bytes()

        result = update_project(self.root)
        self.assertIn(result["status"], {"applied", "no-op"})
        self.assertEqual((self.root / ".specify/memory/constitution.md").read_bytes(), before)
        self.assertEqual((self.root / ".specify/extensions.yml").read_text(), legacy_assets.LEGACY_EXTENSIONS)


if __name__ == "__main__":
    unittest.main()
