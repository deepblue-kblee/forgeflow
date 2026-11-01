"""Source-entrypoint and generated-product contracts in disposable repositories."""

import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class TestWorkflowCLIContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        self.env = dict(os.environ, PYTHONPATH=str(SOURCE_ROOT / "src"))
        self.git("init", "-b", "main")
        self.git("config", "user.name", "CLI Test")
        self.git("config", "user.email", "test@example.invalid")
        (self.root / "app.txt").write_text("before\n")
        self.git("add", "app.txt")
        self.git("commit", "-m", "initial")
        self.git("switch", "-c", "codex/example")

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "forgeflow.cli", *args],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def test_source_cli_plan_check_verify_and_local_integration(self):
        agreement = Path(self.temporary.name) / "agreement.json"
        agreement.write_text(json.dumps({
            "scope": ["app.txt"], "acceptance": ["app contains the new text"],
            "plan": "Update the text and verify the delivered file", "owner": "standalone",
            "source": "codex/example", "target": "main", "integration": "local",
            "permissions": ["commit", "merge", "delete-branch"], "task_owned_branch": True,
            "checks": [[sys.executable, "-c", "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"]],
        }))
        started = self.cli("workflow", "start", "example", "--agreement", str(agreement), "--json")
        self.assertEqual(started.returncode, 0, started.stderr + started.stdout)
        checked = self.cli("check", "example", "--stage", "2", "--quiet")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        (self.root / "app.txt").write_text("after\n")
        verified = self.cli("workflow", "verify", "example", "--json")
        self.assertEqual(verified.returncode, 0, verified.stderr + verified.stdout)
        self.assertTrue(json.loads(verified.stdout)["verification"]["passed"])
        finished = self.cli("workflow", "finalize", "example", "--json")
        self.assertEqual(finished.returncode, 0, finished.stderr + finished.stdout)
        self.assertEqual(json.loads(finished.stdout)["status"], "cleaned")
        self.assertEqual(self.git("show", "main:app.txt"), "after")
        self.assertFalse((self.root / "tasks").exists())

    def test_host_branch_option_cannot_override_ownership(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"owner": "host"},
                                      "governance": {"auto_create_branch": True}}))
        result = self.cli("release", "create", "v0.1.0-example", "--create-branch")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Host owns", result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "codex/example")
        self.assertFalse((self.root / "tasks").exists())

    def test_legacy_close_honors_host_ownership(self):
        config = self.root / ".forgeflow/config.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"workflow": {"owner": "host"}}))
        result = self.cli("lifecycle", "close", "v0.1.0-example", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["error"], "host_owned_workspace")

    def test_fresh_skill_generation_uses_workflow_and_keeps_strict_order(self):
        skills = Path(self.temporary.name) / "skills"
        env = dict(self.env, FORGEFLOW_SKILLS_DIR=str(skills))
        generated = subprocess.run(["bash", str(SOURCE_ROOT / "scripts/install-skills.sh")],
                                   cwd=self.root, env=env, capture_output=True, text=True)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        text = (skills / "forgeflow/SKILL.md").read_text()
        self.assertIn("workflow", text)
        self.assertIn("host", text)
        self.assertLess(text.index("package-review"), text.index("lifecycle seal"))
        self.assertLess(text.index("RELEASE_SIGNOFF.md"), text.index("lifecycle seal"))
        for path in skills.rglob("SKILL.md"):
            self.assertNotIn("git reset --hard", path.read_text())
            self.assertNotIn("Date-Based Amnesia", path.read_text())

    def test_canonical_distribution_documents_are_identical(self):
        result = subprocess.run([sys.executable, str(SOURCE_ROOT / "scripts/sync-distribution.py"), "--check"],
                                cwd=SOURCE_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_packaged_spec_relative_document_links_resolve(self):
        for document in (SOURCE_ROOT / "src/forgeflow/spec").glob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
                path = target.split("#", 1)[0]
                if path and not path.startswith(("https:", "http:")):
                    self.assertTrue((document.parent / path).is_file(),
                                    f"Broken packaged link: {document.name} -> {path}")


if __name__ == "__main__":
    unittest.main()
