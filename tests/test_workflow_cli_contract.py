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
        checked = self.cli("workflow", "check", "example", "--json")
        self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)
        (self.root / "app.txt").write_text("after\n")
        verified = self.cli("workflow", "verify", "example", "--json")
        self.assertEqual(verified.returncode, 0, verified.stderr + verified.stdout)
        self.assertTrue(json.loads(verified.stdout)["verification"]["passed"])
        finished = self.cli("workflow", "finalize", "example", "--json")
        self.assertEqual(finished.returncode, 0, finished.stderr + finished.stdout)
        self.assertEqual(json.loads(finished.stdout)["status"], "cleaned")
        self.assertEqual(self.git("show", "main:app.txt"), "after")
        self.assertFalse((self.root / "tasks").exists())

    def test_fresh_skill_generation_uses_current_workflow_only(self):
        skills = Path(self.temporary.name) / "skills"
        env = dict(self.env, FORGEFLOW_SKILLS_DIR=str(skills))
        generated = subprocess.run(["bash", str(SOURCE_ROOT / "scripts/install-skills.sh")],
                                   cwd=self.root, env=env, capture_output=True, text=True)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        text = (skills / "forgeflow/SKILL.md").read_text()
        self.assertIn("workflow", text)
        self.assertIn("design", text)
        for path in skills.rglob("SKILL.md"):
            content = path.read_text()
            self.assertNotIn("git reset --hard", content)
            self.assertNotIn("Date-Based Amnesia", content)
            self.assertNotIn("package-review", content)
            self.assertNotIn("lifecycle seal", content)

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
