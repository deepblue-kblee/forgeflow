"""Black-box acceptance through an isolated installed CLI and actual Git.

No ForgeFlow Python API or mock is used. FORGEFLOW_E2E_EVIDENCE optionally
retains each scenario's subprocess transcript outside the disposable fixtures.
"""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
BEFORE = '''import json
from decimal import Decimal
from pathlib import Path
import sys

def total(price, rate):
    return Decimal(price).quantize(Decimal("0.01"))

if __name__ == "__main__":
    rate = sys.argv[2] if len(sys.argv) > 2 else str(json.loads(Path("rates.json").read_text())["rate"])
    print(total(sys.argv[1], rate))
'''
AFTER = BEFORE.replace('    return Decimal(price).quantize(Decimal("0.01"))', '''    rate = Decimal(rate)
    if not 0 <= rate <= 100:
        raise ValueError("rate must be between 0 and 100")
    return (Decimal(price) * (1 - rate / 100)).quantize(Decimal("0.01"))''')


def project_tests(default="100.00", feature=True):
    tests = '''import subprocess
import sys
import unittest

class QuoteTests(unittest.TestCase):
    def test_default_price(self):
        result = subprocess.run([sys.executable, "src/quote.py", "100"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "DEFAULT")
'''.replace("DEFAULT", default)
    if feature:
        tests += '''
    def test_twenty_percent_discount(self):
        result = subprocess.run([sys.executable, "src/quote.py", "100", "20"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "80.00")

    def test_invalid_discount_is_rejected(self):
        result = subprocess.run([sys.executable, "src/quote.py", "100", "101"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rate must be between 0 and 100", result.stderr)
'''
    return tests


class TestInstalledWorkflowE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installation = tempfile.TemporaryDirectory(prefix="forgeflow-e2e-install-")
        cls.addClassCleanup(cls.installation.cleanup)
        cls.install_root = Path(cls.installation.name).resolve()
        cls.environment = {key: value for key, value in os.environ.items()
                           if not key.startswith(("GIT_", "SPECIFY_"))
                           and key not in {"PYTHONPATH", "PYTHONHOME", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE"}}
        cls.environment.update(FORGEFLOW_PYTHON=sys.executable,
                               FORGEFLOW_INSTALL_SPECKIT_SKILLS="0",
                               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", PYTHONNOUSERSITE="1")
        cls.cli_path = cls.install_root / "bin/forgeflow"
        env = dict(cls.environment, FORGEFLOW_SKILLS_DIR=str(cls.install_root / "skills"))
        result = subprocess.run(["bash", str(REPOSITORY / "install.sh"),
                                 "--prefix", str(cls.install_root / "prefix"),
                                 "--bin-dir", str(cls.install_root / "bin")],
                                cwd=REPOSITORY, env=env, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="scenario-", dir=self.install_root)
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name).resolve()
        self.root = self.workspace / "project"
        self.root.mkdir()
        self.env = dict(self.environment)
        self.commands = []
        self.addCleanup(self.save_evidence)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Acceptance Fixture")
        self.git("config", "user.email", "acceptance@example.invalid")
        self.git("config", "core.hooksPath", str(self.root / ".git/hooks"))
        self.cli("init", "--speckit", "--json")
        for directory in ("src", "tests"):
            (self.root / directory).mkdir()
        # Build outputs belong to the project's Git policy, not task source.
        ignore = self.root / ".gitignore"
        ignore.write_text(ignore.read_text() + "\n__pycache__/\n*.pyc\n")
        (self.root / "src/quote.py").write_text(BEFORE)
        (self.root / "tests/test_quote.py").write_text(project_tests(feature=False))
        (self.root / "notes.txt").write_text("User notes before the task.\n")
        (self.root / "rates.json").write_text('{"rate": 0}\n')
        self.configure()
        self.git("add", ".")
        self.git("commit", "-m", "working project before feature")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.branch = "task/discount"
        self.git("switch", "-c", self.branch)

    def save_evidence(self):
        directory = os.environ.get("FORGEFLOW_E2E_EVIDENCE")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / (self._testMethodName + ".json")).write_text(json.dumps({
                "scenario": self.id(), "commands": self.commands,
            }, indent=2) + "\n")

    def run_command(self, argv, expected=0, cwd=None, env=None):
        result = subprocess.run([str(arg) for arg in argv], cwd=cwd or self.root,
                                env=env or self.env, capture_output=True, text=True, timeout=120)
        self.commands.append({"argv": [str(arg) for arg in argv], "cwd": str(cwd or self.root),
                              "returncode": result.returncode,
                              "stdout": result.stdout, "stderr": result.stderr})
        if expected is not None:
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def git(self, *args, expected=0):
        return self.run_command(["git", *args], expected=expected).stdout

    def cli(self, *args, expected=0, command=None, env=None):
        result = self.run_command([*(command or [self.cli_path]), *args], expected=expected, env=env)
        return json.loads(result.stdout)

    def configure(self, **options):
        path = self.root / ".forgeflow/config.json"
        config = json.loads(path.read_text())
        config["workflow"].update({
            "checks": [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]],
            "verification_paths": ["src", "tests", "rates.json"],
            **options,
        })
        path.write_text(json.dumps(config, indent=2) + "\n")

    def start(self, **options):
        agreement = {
            "scope": ["src", "tests"],
            "acceptance": ["100 at a 20 percent discount prints 80.00", "out-of-range rates fail"],
            "plan": "Add Decimal discount calculation and CLI regression tests",
            "owner": "standalone", "source": self.branch, "target": "main",
            "integration": "local", "permissions": ["commit", "merge", "delete-branch"],
            "task_owned_branch": True, "checks": [],
            "verification_paths": ["src", "tests"],
            **options,
        }
        path = self.workspace / "agreement.json"
        path.write_text(json.dumps(agreement, indent=2) + "\n")
        return self.cli("workflow", "start", "discount", "--agreement", str(path), "--json")

    def implement(self, default="100.00"):
        (self.root / "src/quote.py").write_text(AFTER)
        (self.root / "tests/test_quote.py").write_text(project_tests(default=default))

    def ready(self, **options):
        state = self.start(**options)
        self.implement()
        self.assertEqual(self.cli("workflow", "verify", "discount", "--json")["status"], "ready")
        return state

    def state(self):
        return json.loads((self.root / ".forgeflow/workflows/discount.json").read_text())

    def assert_application(self, expected="80.00"):
        output = self.run_command([sys.executable, "src/quote.py", "100", "20"]).stdout.strip()
        self.assertEqual(output, expected)

    def test_speckit_failed_check_fix_push_merge_cleanup_preserves_user_work(self):
        branch_before = self.git("branch", "--list")
        feature = json.loads(self.run_command([
            "bash", ".specify/scripts/bash/create-new-feature.sh", "--json",
            "--short-name", "discount", "Add a validated percentage discount",
        ]).stdout)
        spec = Path(feature["SPEC_FILE"])
        feature_dir = spec.parent
        self.run_command(["bash", ".specify/scripts/bash/setup-plan.sh", "--json"])
        tasks = json.loads(self.run_command(["bash", ".specify/scripts/bash/setup-tasks.sh", "--json"]).stdout)
        self.assertIn("TASKS_TEMPLATE_CONTENT", tasks)
        spec.write_text("# Discount\nAcceptance: 100 at 20 percent is 80.00; reject rates outside 0..100.\n")
        (feature_dir / "plan.md").write_text("# Plan\nUse Decimal and verify the public program invocation.\n")
        (feature_dir / "tasks.md").write_text("- [ ] Add failing tests\n- [ ] Implement and verify\n")
        self.run_command(["bash", ".specify/scripts/bash/check-prerequisites.sh", "--json",
                          "--require-spec", "--require-tasks"])
        self.assertEqual(self.git("branch", "--list"), branch_before)
        remote = self.workspace / "origin.git"
        self.run_command(["git", "init", "--bare", str(remote)])
        self.git("remote", "add", "origin", str(remote))
        self.start(scope=["src", "tests", str(feature_dir.relative_to(self.root)), ".specify/feature.json"],
                   include_existing_changes=True, permissions=["commit", "push", "merge", "delete-branch"])
        self.cli("workflow", "check", "discount", "--json")
        (self.root / "tests/test_quote.py").write_text(project_tests())
        failed = self.cli("workflow", "verify", "discount", "--json", expected=1)
        self.assertEqual(failed["status"], "verification-failed")
        blocked = self.cli("workflow", "finalize", "discount", "--json", expected=1)
        self.assertEqual(blocked["pending"]["operation"], "verify")
        self.assertEqual(self.git("rev-parse", "main").strip(), self.base)
        self.implement()
        (self.root / "notes.txt").write_text("User staged draft.\n")
        self.git("add", "notes.txt")
        (self.root / "notes.txt").write_text("User unstaged continuation.\n")
        (self.root / "personal-draft.txt").write_text("Untracked user work.\n")
        self.assertEqual(self.cli("workflow", "verify", "discount", "--json")["status"], "ready")
        (feature_dir / "tasks.md").write_text("- [x] Add failing tests\n- [x] Implement and verify\n")
        self.assertEqual(self.cli("workflow", "status", "discount", "--json")["status"], "ready")
        done = self.cli("workflow", "finalize", "discount", "--json")
        self.assertEqual(done["status"], "cleaned")
        self.assertTrue(done["finalization_complete"])
        target = self.git("rev-parse", "main").strip()
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/" + self.branch).split()[0], target)
        self.assertNotIn(self.branch, self.git("branch", "--list"))
        self.assertEqual(self.git("show", ":notes.txt").strip(), "User staged draft.")
        self.assertEqual((self.root / "notes.txt").read_text(), "User unstaged continuation.\n")
        self.assertEqual((self.root / "personal-draft.txt").read_text(), "Untracked user work.\n")
        self.assertEqual(self.git("show", "main:notes.txt").strip(), "User notes before the task.")
        self.assertFalse(list(feature_dir.glob("*SIGNOFF*")))
        self.assert_application()
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json")["status"], "cleaned")
        self.assertEqual(self.git("rev-parse", "main").strip(), target)

    def test_implementation_and_environment_changes_block_stale_verification(self):
        self.configure(environment=["QUOTE_CURRENCY"])
        self.env["QUOTE_CURRENCY"] = "KRW"
        self.ready()
        (self.root / "src/quote.py").write_text(AFTER + "\n# implementation input changed\n")
        stale = self.cli("workflow", "status", "discount", "--json", expected=1)
        self.assertEqual(stale["status"], "verification-stale")
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json", expected=1)["pending"]["operation"], "verify")
        (self.root / "src/quote.py").write_text(AFTER)
        self.env["QUOTE_CURRENCY"] = "JPY"
        self.assertEqual(self.cli("workflow", "status", "discount", "--json", expected=1)["status"], "verification-stale")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_unignored_check_outputs_are_reviewed_before_accepting_a_pass(self):
        ignore = self.root / ".gitignore"
        original = ignore.read_text()
        ignore.write_text(original.replace("__pycache__/\n", "").replace("*.pyc\n", ""))
        self.start()
        self.implement()
        stale = self.cli("workflow", "verify", "discount", "--json", expected=1)
        self.assertEqual(stale["status"], "verification-stale")
        self.assertEqual(stale["verification"]["results"][0]["returncode"], 0)
        self.assertIn("__pycache__", self.git("ls-files", "--others", "--exclude-standard"))
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json", expected=1)["pending"]["operation"], "verify")
        ignore.write_text(original)
        self.assertEqual(self.cli("workflow", "verify", "discount", "--json")["status"], "ready")
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json")["status"], "cleaned")

    def test_uncommitted_dependency_is_not_published_as_a_verified_commit(self):
        self.configure(verification_paths=["src", "tests", "rates.json"])
        self.start()
        self.implement(default="80.00")
        (self.root / "rates.json").write_text('{"rate": 20}\n')
        self.assertEqual(self.cli("workflow", "verify", "discount", "--json")["status"], "ready")
        blocked = self.cli("workflow", "finalize", "discount", "--json", expected=1)
        self.assertEqual(blocked["pending"]["operation"], "verify-committed-inputs")
        self.assertIn("rates.json", blocked["pending"]["reason"])
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertEqual(json.loads((self.root / "rates.json").read_text()), {"rate": 20})
        self.assertEqual(json.loads(self.git("show", "main:rates.json")), {"rate": 0})

    def test_real_git_ref_lock_allows_cleanup_only_resume_in_a_new_process(self):
        self.ready()
        self.git("add", "src", "tests")
        self.git("commit", "-m", "accepted feature")
        verification = self.state()["verification"]
        lock = Path(self.git("rev-parse", "--git-path", "refs/heads/" + self.branch + ".lock").strip())
        lock = lock if lock.is_absolute() else self.root / lock
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("Fixture owns this lock.\n")
        try:
            blocked = self.cli("workflow", "finalize", "discount", "--json", expected=1)
            self.assertEqual(blocked["status"], "blocked")
            self.assertIn("lock", blocked["reason"])
            self.assertEqual(self.state()["status"], "integrated")
            target = self.git("rev-parse", "main").strip()
            self.assert_application()
        finally:
            lock.unlink()
        self.assertEqual(self.cli("workflow", "status", "discount", "--json")["status"], "integrated")
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json")["status"], "cleaned")
        self.assertEqual(self.state()["verification"], verification)
        self.assertEqual(self.git("rev-parse", "main").strip(), target)

    def test_host_pending_receipts_require_actual_external_git_results(self):
        self.configure(owner="host")
        before = self.git("branch", "--list")
        rejected = self.run_command([self.cli_path, "release", "create", "v0.1.0-example", "--create-branch"], expected=2)
        self.assertIn("Host owns", rejected.stderr)
        self.assertEqual(self.git("branch", "--list"), before)
        self.ready(owner="host")
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json", expected=1)["pending"]["operation"], "commit")
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.git("add", "src", "tests")
        self.git("commit", "-m", "external host committed accepted feature")
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json", expected=1)["pending"]["operation"], "merge")
        source = self.git("rev-parse", "HEAD").strip()
        receipt = {"operation": "merge", "repository": str(self.root), "source": self.branch,
                   "target": "main", "source_commit": source, "tool": "external-git-fixture",
                   "evidence": "External git switch/merge command transcript retained by this acceptance test"}
        path = self.workspace / "host-receipt.json"
        path.write_text(json.dumps(receipt))
        rejected = self.cli("workflow", "finalize", "discount", "--receipt", str(path), "--json", expected=1)
        self.assertIn("does not contain", rejected["reason"])
        self.git("switch", "main")
        self.git("merge", "--ff-only", self.branch)
        integrated = self.cli("workflow", "finalize", "discount", "--receipt", str(path), "--json", expected=1)
        self.assertEqual(integrated["status"], "integrated")
        self.assertEqual(integrated["pending"]["operation"], "delete-branch")
        receipt["operation"] = "delete-branch"
        path.write_text(json.dumps(receipt))
        self.assertIn("not observed", self.cli("workflow", "finalize", "discount", "--receipt", str(path), "--json", expected=1)["reason"])
        self.git("branch", "-d", self.branch)
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--receipt", str(path), "--json")["status"], "cleaned")
        self.assert_application()

    def test_divergence_blocks_until_source_is_reconciled_and_verified(self):
        self.ready()
        self.git("add", "src", "tests")
        self.git("commit", "-m", "discount on source")
        self.git("switch", "main")
        (self.root / "notes.txt").write_text("Independent main change.\n")
        self.git("add", "notes.txt")
        self.git("commit", "-m", "target advanced independently")
        target = self.git("rev-parse", "HEAD").strip()
        self.git("switch", self.branch)
        result = self.cli("workflow", "finalize", "discount", "--json", expected=1)
        self.assertEqual(result["pending"]["operation"], "reconcile")
        self.assertEqual(self.git("rev-parse", "main").strip(), target)
        self.git("rebase", "main")
        self.assertEqual(self.cli("workflow", "verify", "discount", "--json")["status"], "ready")
        self.assertEqual(self.cli("workflow", "finalize", "discount", "--json")["status"], "cleaned")
        self.assertEqual((self.root / "notes.txt").read_text(), "Independent main change.\n")
        self.assert_application()

    def test_verification_alone_does_not_grant_git_write_authority(self):
        self.ready(permissions=[])
        done = self.cli("workflow", "finalize", "discount", "--json", expected=1)
        self.assertEqual(done["pending"]["operation"], "commit")
        self.assertFalse(done["finalization_complete"])
        self.assertEqual(self.git("rev-parse", "main").strip(), self.base)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertEqual(self.git("branch", "--show-current").strip(), self.branch)

    def test_replaced_installation_keeps_active_snapshot_until_explicit_adoption(self):
        prefix, binaries = self.workspace / "replacement-prefix", self.workspace / "replacement-bin"
        env = dict(self.env, FORGEFLOW_SKILLS_DIR=str(self.workspace / "replacement-skills"))
        self.run_command(["bash", REPOSITORY / "install.sh", "--prefix", prefix, "--bin-dir", binaries],
                         cwd=REPOSITORY, env=env)
        self.cli_path = binaries / "forgeflow"
        previous_package = (prefix / "current").resolve()
        previous_version = json.loads((previous_package / "package.json").read_text())["version"]
        first = self.ready(integration="none", permissions=["commit"])
        fixture = self.workspace / "replacement-source"
        (fixture / "src").mkdir(parents=True)
        (fixture / "scripts").mkdir()
        shutil.copytree(REPOSITORY / "src/forgeflow", fixture / "src/forgeflow",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(REPOSITORY / "install.sh", fixture / "install.sh")
        shutil.copyfile(REPOSITORY / "scripts/install-skills.sh", fixture / "scripts/install-skills.sh")
        spec = fixture / "src/forgeflow/spec/FLOW_SPEC.md"
        spec.write_text(spec.read_text() + "\nReplacement acceptance marker.\n")
        self.run_command(["bash", fixture / "install.sh", "--prefix", prefix, "--bin-dir", binaries], cwd=fixture, env=env)
        selected_package = (prefix / "current").resolve()
        self.assertNotEqual(selected_package, previous_package)
        self.assertEqual(json.loads((selected_package / "package.json").read_text())["version"], previous_version)
        replacement = [binaries / "forgeflow"]
        drift = self.cli("workflow", "status", "discount", "--json", expected=1, command=replacement)
        self.assertEqual(drift["status"], "baseline-drift")
        pinned = shlex.split(first["baseline"]["command"])
        # The installed launcher injects its library into PYTHONPATH. The
        # pinned launcher keeps the caller environment, so that environment
        # transition correctly requires checks again, without changing rules.
        pinned_state = self.cli("workflow", "status", "discount", "--json", command=pinned, expected=1)
        self.assertEqual(pinned_state["status"], "verification-stale")
        self.assertEqual(pinned_state["baseline"], first["baseline"])
        verified = self.cli("workflow", "verify", "discount", "--json", command=pinned)
        self.assertEqual(verified["status"], "ready")
        previous = pinned_state["verification"]["inputs"]
        current = verified["verification"]["inputs"]
        self.assertEqual(previous["content"], current["content"])
        self.assertNotEqual(previous["environment"], current["environment"])
        self.assertEqual(previous["baseline"], current["baseline"])
        document = self.cli("doc", "show", "FLOW_SPEC", "--json", command=pinned)
        self.assertNotIn("Replacement acceptance marker.", document["content"])
        original_config = (self.root / ".forgeflow/config.json").read_bytes()
        self.run_command([*replacement, "update", "--json"], expected=1)
        self.assertEqual((self.root / ".forgeflow/config.json").read_bytes(), original_config)
        adopted = self.cli("workflow", "adopt", "discount", "--reason", "acceptance test adopts replacement",
                           "--impact", "reviewed changed spec and repeat affected checks", "--json", command=replacement)
        self.assertNotEqual(adopted["baseline"]["identity"], first["baseline"]["identity"])
        self.assertIsNone(adopted["verification"])
        self.assertEqual(self.cli("workflow", "verify", "discount", "--json", command=replacement)["status"], "ready")
        completed = self.cli("workflow", "finalize", "discount", "--json", command=replacement)
        self.assertEqual(completed["status"], "ready")
        self.assertTrue(completed["finalization_complete"])
        self.assertIsNone(completed["integration"])


if __name__ == "__main__":
    unittest.main()
