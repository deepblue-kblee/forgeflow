"""Tests for tasks architecture, deterministic seal pipeline, and legacy migration."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from forgeflow.cli import parse_forgeflow_args
from forgeflow.harness import HarnessEngine
from forgeflow.scanner import HierarchicalRootScanner, ReleaseScanner
from forgeflow.scaffold import TemplateScaffolder


class TestTasksArchitecture(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # Initialize bare git repository for testing git-based discovery
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.com"], check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scanner_tasks_and_ff_tasks_priority(self):
        # 1. Initially no releases dir
        self.assertIsNone(ReleaseScanner.find_releases_dir(self.root))

        # 2. When tasks/ exists
        tasks_dir = self.root / "tasks"
        tasks_dir.mkdir()
        self.assertEqual(ReleaseScanner.find_releases_dir(self.root), tasks_dir)

        # 3. When .forgeflow.json specifies custom tasks_dir
        config = {
            "governance": {"tasks_dir": "custom-tasks"}
        }
        (self.root / ".forgeflow.json").write_text(json.dumps(config), encoding="utf-8")
        custom_dir = self.root / "custom-tasks"
        custom_dir.mkdir()
        self.assertEqual(ReleaseScanner.find_releases_dir(self.root), custom_dir)

    def test_scanner_kanban_subcontainers(self):
        tasks_dir = self.root / "tasks"
        tasks_dir.mkdir()

        # Create tasks in in-progress and completed
        in_prog = tasks_dir / "in-progress" / "v0.1.0-alpha"
        in_prog.mkdir(parents=True)
        (in_prog / "PRD.md").write_text("# PRD", encoding="utf-8")

        completed = tasks_dir / "completed" / "v0.0.9"
        completed.mkdir(parents=True)
        (completed / "PRD.md").write_text("# PRD", encoding="utf-8")

        all_rels = ReleaseScanner.get_all_releases(self.root)
        rel_names = [r.name for r in all_rels]
        self.assertIn("v0.0.9", rel_names)
        self.assertIn("v0.1.0-alpha", rel_names)

        # Test find_release_path
        found_in_prog = ReleaseScanner.find_release_path(self.root, "v0.1.0-alpha")
        self.assertEqual(found_in_prog, in_prog)
        found_completed = ReleaseScanner.find_release_path(self.root, "v0.0.9")
        self.assertEqual(found_completed, completed)

    def test_scaffold_tasks_guard_and_resolve_dir(self):
        # resolve_release_dir in fresh repo defaults to tasks/in-progress
        target = TemplateScaffolder.resolve_release_dir(self.root, "task-101", stage="in-progress")
        self.assertEqual(target, self.root / "tasks" / "in-progress" / "task-101")

        # Create scaffold creates tasks/README.md guard
        created = TemplateScaffolder.create_release_scaffold(target, "task-101", tier=2)
        self.assertTrue((self.root / "tasks" / "README.md").exists())
        guard_text = (self.root / "tasks" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Non-Guidance Boundary", guard_text)
        self.assertIn("PRD.md", created)

    def test_migrate_to_tasks_engine(self):
        # Set up legacy docs/releases structure
        legacy_rel = self.root / "docs" / "releases" / "v0.1.0-old"
        legacy_rel.mkdir(parents=True)
        (legacy_rel / "PRD.md").write_text("# Old PRD", encoding="utf-8")
        (legacy_rel / "DESIGN.md").write_text("# Old DESIGN", encoding="utf-8")

        (self.root / ".forgeflow.json").write_text(json.dumps({"governance": {"default_tier": 2}}), encoding="utf-8")

        # Run migration
        result = TemplateScaffolder.migrate_to_tasks(self.root, target_dir_name="tasks")
        self.assertEqual(result["status"], "success")
        self.assertIn("v0.1.0-old", result["migrated"])

        # Check completed destination
        dest = self.root / "tasks" / "completed" / "v0.1.0-old"
        self.assertTrue(dest.exists())
        self.assertTrue((dest / "PRD.md").exists())
        self.assertTrue((self.root / "tasks" / "README.md").exists())

        # Check .forgeflow.json updated
        cfg = json.loads((self.root / ".forgeflow.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["governance"]["tasks_dir"], "tasks")
        self.assertEqual(cfg["paths"]["releases"], "tasks")

    def test_ff_tasks_fallback_when_tasks_is_file(self):
        # When 'tasks' exists as a file (e.g. task runner script)
        (self.root / "tasks").write_text("echo 'celery'", encoding="utf-8")

        result = TemplateScaffolder.migrate_to_tasks(self.root, target_dir_name="tasks")
        # should fallback to ff-tasks if docs/releases exists
        legacy_rel = self.root / "docs" / "releases" / "v0.2.0-legacy"
        legacy_rel.mkdir(parents=True)
        (legacy_rel / "PRD.md").write_text("# PRD", encoding="utf-8")

        res = TemplateScaffolder.migrate_to_tasks(self.root, target_dir_name="tasks")
        self.assertEqual(res["target_dir"], "ff-tasks")
        self.assertTrue((self.root / "ff-tasks" / "completed" / "v0.2.0-legacy").exists())
        self.assertTrue((self.root / "ff-tasks" / "README.md").exists())

    def test_cli_task_and_migrate_commands(self):
        # Test CLI task create
        args = parse_forgeflow_args(["task", "create", "v1.0.0-feat", "--tier", "2", "--stage", "in-progress"])
        self.assertEqual(args.command, "task")
        self.assertEqual(args.task_command, "create")
        self.assertEqual(args.task_id, "v1.0.0-feat")

        # Test CLI migrate
        m_args = parse_forgeflow_args(["migrate", "--tasks", "--target", "tasks"])
        self.assertEqual(m_args.command, "migrate")
        self.assertTrue(m_args.tasks)
        self.assertEqual(m_args.target, "tasks")


if __name__ == "__main__":
    unittest.main()
