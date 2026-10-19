#!/usr/bin/env python3
"""
Unit tests for ForgeFlow Document Integrity & Markdown Parser
"""

import tempfile
import unittest
import subprocess
import shutil
import re
from pathlib import Path

from forgeflow.harness import HarnessEngine
from forgeflow.runner import RuntimeTestRunner
from forgeflow.validator import (
    DocumentIntegrityValidator,
    MarkdownSectionParser,
    TierRules,
    SelfGovernanceValidator,
)


class TestMarkdownSectionParser(unittest.TestCase):
    def test_extract_tier(self):
        self.assertEqual(MarkdownSectionParser.extract_tier("Risk Tier 1"), 1)
        self.assertEqual(MarkdownSectionParser.extract_tier("Tier 3 (Critical)"), 3)
        self.assertIsNone(MarkdownSectionParser.extract_tier("No tier info"))

    def test_change_note_tier_one_release_is_not_defaulted_to_tier_two(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        release = root / "docs" / "releases" / "tier-one"
        release.mkdir(parents=True)
        release.joinpath("CHANGE_NOTE.md").write_text(
            "# Change Note\n\n- Tier: 1\n\n## Gate 1\nPASS\n",
            encoding="utf-8",
        )
        result = HarnessEngine(root).check_release(release)
        self.assertEqual(result.tier, 1)
        self.assertEqual(set(result.documents), {"CHANGE_NOTE.md"})

    def test_parse_prd_valid(self):
        content = "# PRD\nREQ-F01: Feature A\nREQ-NF01: Performance\n## 인수 조건\n1. Pass"
        res = MarkdownSectionParser.parse_prd(content)
        self.assertTrue(res["passed"])
        self.assertEqual(res["req_ids"], ["REQ-F01", "REQ-NF01"])
        self.assertTrue(res["has_acceptance"])

    def test_parse_prd_missing_req(self):
        content = "# PRD\nNo ids here\n## 인수 조건\n1. Pass"
        res = MarkdownSectionParser.parse_prd(content)
        self.assertFalse(res["passed"])

    def test_parse_design_valid(self):
        content = "# Design\n## 아키텍처\nOverview\n## 요구사항 추적 매트릭스 (RTM)\n| REQ-F01 | mod |"
        res = MarkdownSectionParser.parse_design(content)
        self.assertTrue(res["passed"])

    def test_parse_qa_signoff_valid(self):
        content = "# QA Sign-Off\n- 최종 판정: APPROVED\n## 테스트 실행 요약\nAll passed"
        res = MarkdownSectionParser.parse_qa_signoff(content)
        self.assertTrue(res["passed"])

    def test_parse_completion_report_valid(self):
        content = "# Completion Report\n## 1. 개요 및 성과\nDone\n## 3. 미완 또는 향후 개선 필요 사항\nNext"
        res = MarkdownSectionParser.parse_completion_report(content)
        self.assertTrue(res["passed"])


class TestLifecycleEvidenceSchema(unittest.TestCase):
    """Negative fixtures for the fixed v0.3.8 evidence grammar."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "checkout", "-qb", "feat/v0.3.8-fixture"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
        (self.root / "seed").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitignore", "seed"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "seed"],
            cwd=self.root,
            check=True,
        )
        self.base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_smoke.py").write_text(
            "import unittest\n\nclass Smoke(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
            encoding="utf-8",
        )
        (self.root / "candidate").write_text("candidate\n", encoding="utf-8")
        subprocess.run(["git", "add", "candidate", "tests/test_smoke.py"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "candidate"],
            cwd=self.root, check=True,
        )
        self.candidate = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        self.release_id = "v0.3.8-fixture"
        self.release = self.root / "docs" / "releases" / self.release_id
        self.release.mkdir(parents=True)
        (self.release / "PRD.md").write_text(
            "# PRD\nTier 3\nREQ-F01: evidence\n## Acceptance Criteria\nPASS\n", encoding="utf-8"
        )
        (self.release / "DESIGN.md").write_text(
            "# DESIGN\n## Architecture\nreader\n## RTM\n| REQ-F01 | reader |\n", encoding="utf-8"
        )
        (self.release / "COMPLETION_REPORT.md").write_text(
            "# Completion Report\n## Summary\ncomplete\n## Future Improvements\nnone\n", encoding="utf-8"
        )
        self.engine = HarnessEngine(self.root)
        self._write_valid_qa()

    def _write_valid_qa(self):
        digests = {
            name: self.engine._artifact_digest(name, (self.release / name).read_text(encoding="utf-8"))
            for name in ("PRD.md", "DESIGN.md", "COMPLETION_REPORT.md")
        }
        qa_digest = "0" * 64
        def evidence(qa_value):
            return "\n".join((
                "## ForgeFlow Evidence v1", "```text", "Schema-Version: 1",
                f"Release-ID: {self.release_id}", "Tier: 3", "Task-Branch: feat/v0.3.8-fixture",
                f"Base-SHA: {self.base}", f"Candidate-SHA: {self.candidate}",
                "Stage: GATE_2", "Gate-1: APPROVED", "Gate-2: APPROVED",
                f"Reviewer: id=security; perspective=Security; verdict=APPROVED; candidate-sha={self.candidate}",
                f"Reviewer: id=reliability; perspective=Reliability; verdict=APPROVED; candidate-sha={self.candidate}",
                f"Reviewer: id=maintainability; perspective=Maintainability; verdict=APPROVED; candidate-sha={self.candidate}",
                f"Artifact: path=PRD.md; sha256={digests['PRD.md']}; status=COMPLETE",
                f"Artifact: path=DESIGN.md; sha256={digests['DESIGN.md']}; status=COMPLETE",
                f"Artifact: path=QA_SIGNOFF.md; sha256={qa_value}; status=COMPLETE",
                f"Artifact: path=COMPLETION_REPORT.md; sha256={digests['COMPLETION_REPORT.md']}; status=COMPLETE",
                f"Verification: id=unit-tests; command=python3 -m unittest; result=PASS; exit-code=0; candidate-sha={self.candidate}",
                "Next-Action: NONE", "```",
            ))
        initial = "# QA Sign-Off\nFinal verdict: APPROVED\nTests: PASS\n\n" + evidence(qa_digest) + "\n"
        qa_digest = self.engine._artifact_digest("QA_SIGNOFF.md", initial)
        (self.release / "QA_SIGNOFF.md").write_text(
            "# QA Sign-Off\nFinal verdict: APPROVED\nTests: PASS\n\n" + evidence(qa_digest) + "\n", encoding="utf-8"
        )

    def _unmet(self):
        return self.engine.check_lifecycle_evidence(self.release_id)["unmet_conditions"]

    def test_legacy_release_without_release_notes_passes_strict_audit(self):
        self._commit_final_evidence()
        result = self.engine.check_lifecycle_evidence(self.release_id, strict=True)
        self.assertTrue(result["ok"], result)
        self.assertFalse((self.release / "RELEASE_NOTES.md").exists())

    def test_release_notes_only_mutation_does_not_stale_evidence(self):
        self._commit_final_evidence()
        before = self.engine.check_lifecycle_evidence(self.release_id, strict=True)
        self.assertTrue(before["ok"], before)
        (self.release / "RELEASE_NOTES.md").write_text("# User notes\n\nChanged only.\n", encoding="utf-8")
        after = self.engine.check_lifecycle_evidence(self.release_id, strict=True)
        self.assertTrue(after["ok"], after)

    def test_evidence_core_artifact_set_remains_exact_four(self):
        self.assertEqual(
            HarnessEngine._CORE_ARTIFACTS,
            ("PRD.md", "DESIGN.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md"),
        )

    def _commit_final_evidence(self):
        subprocess.run(["git", "add", "docs"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "final evidence"],
            cwd=self.root,
            check=True,
        )

    def test_accepts_complete_fixed_schema(self):
        self.assertFalse(self.engine.check_lifecycle_evidence(self.release_id)["ok"])
        self._commit_final_evidence()
        self.assertTrue(self.engine.check_lifecycle_evidence(self.release_id, strict=True)["ok"])

    def test_rejects_symlinked_artifact_and_traversal(self):
        outside = self.root / "outside.md"
        outside.write_text((self.release / "PRD.md").read_text(encoding="utf-8"), encoding="utf-8")
        (self.release / "PRD.md").unlink()
        (self.release / "PRD.md").symlink_to(outside)
        self.assertTrue(any("artifact_unreadable_or_stale" in item for item in self._unmet()))
        self.assertIn("invalid_release_id", self.engine.check_lifecycle_evidence("../v0.3.8-fixture")["unmet_conditions"])

    def test_rejects_duplicate_malformed_and_pending_evidence(self):
        qa = self.release / "QA_SIGNOFF.md"
        qa.write_text(qa.read_text(encoding="utf-8").replace("Gate-2: APPROVED", "Gate-2: PENDING"), encoding="utf-8")
        self.assertTrue(any("gate_verdict" in item for item in self._unmet()))
        self._write_valid_qa()
        qa.write_text(qa.read_text(encoding="utf-8").replace("Tier: 3", "Tier: 3\nTier: 3"), encoding="utf-8")
        self.assertTrue(any("duplicate_tier" in item for item in self._unmet()))

    def test_rejects_incomplete_panel_candidate_and_verification_shape(self):
        qa = self.release / "QA_SIGNOFF.md"
        qa.write_text(qa.read_text(encoding="utf-8").replace("perspective=Maintainability", "perspective=Reliability"), encoding="utf-8")
        self.assertTrue(any("reviewer_identity_or_perspective" in item for item in self._unmet()))
        self._write_valid_qa()
        qa.write_text(qa.read_text(encoding="utf-8").replace("id=security; perspective=Security; verdict=APPROVED; candidate-sha=" + self.candidate, "id=security; perspective=Security; verdict=APPROVED; candidate-sha=" + ("1" * 40)), encoding="utf-8")
        self.assertTrue(any("reviewer_candidate_mismatch" in item for item in self._unmet()))
        self._write_valid_qa()
        qa.write_text(qa.read_text(encoding="utf-8").replace("exit-code=0; candidate-sha=" + self.candidate, "exit-code=1; candidate-sha=" + self.candidate, 1), encoding="utf-8")
        self.assertTrue(any("verification_shape" in item for item in self._unmet()))

    def test_rejects_candidate_that_is_not_a_local_commit(self):
        invalid = "1" * 40
        qa = self.release / "QA_SIGNOFF.md"
        qa.write_text(qa.read_text(encoding="utf-8").replace(self.candidate, invalid), encoding="utf-8")
        self.assertIn("candidate_sha_not_local_commit", self._unmet())

    def test_rejects_candidate_branch_base_binding_and_placeholder(self):
        qa = self.release / "QA_SIGNOFF.md"
        qa.write_text(
            qa.read_text(encoding="utf-8").replace("Task-Branch: feat/v0.3.8-fixture", "Task-Branch: feat/other"),
            encoding="utf-8",
        )
        self.assertIn("candidate_not_bound_to_current_branch_base", self._unmet())
        self._write_valid_qa()
        prd = self.release / "PRD.md"
        prd.write_text(prd.read_text(encoding="utf-8") + "\nDraft\n", encoding="utf-8")
        self.assertTrue(any("artifact_unreadable_or_stale" in item for item in self._unmet()))

    def test_rejects_symlinked_release_parent(self):
        real_docs = self.root / "real-docs"
        (self.root / "docs").rename(real_docs)
        (self.root / "docs").symlink_to(real_docs, target_is_directory=True)
        self.assertIn("release_artifacts_missing", self._unmet())

    def test_rejects_stale_candidate_and_empty_strict_suite(self):
        self._commit_final_evidence()
        (self.root / "after-candidate").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "after-candidate"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "after candidate"],
            cwd=self.root, check=True,
        )
        self.assertIn("candidate_not_bound_to_current_branch_base", self._unmet())
        empty = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, empty, ignore_errors=True)
        (empty / "tests").mkdir()
        result = RuntimeTestRunner.run_tests(empty)
        self.assertTrue(re.search(r"Ran\s+0\s+tests", result["output"]))

    def test_rejects_nonrelease_commit_after_candidate(self):
        self._commit_final_evidence()
        path = self.root / "src" / "forbidden.py"
        path.parent.mkdir()
        path.write_text("value = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/forbidden.py"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "post-candidate code"],
            cwd=self.root,
            check=True,
        )
        self.assertIn("candidate_not_bound_to_current_branch_base", self._unmet())

    def test_rejects_session_state_commit_after_candidate(self):
        self._commit_final_evidence()
        state = self.root / "docs" / "session-state" / "next-actions.md"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text("stale session state\n", encoding="utf-8")
        subprocess.run(["git", "add", "docs/session-state/next-actions.md"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "session state after candidate"],
            cwd=self.root,
            check=True,
        )
        self.assertIn("candidate_not_bound_to_current_branch_base", self._unmet())

    def test_rejects_sibling_candidate_not_ancestral_to_head(self):
        self._commit_final_evidence()
        tree = subprocess.check_output(
            ["git", "rev-parse", f"{self.candidate}^{{tree}}"], cwd=self.root, text=True
        ).strip()
        sibling = subprocess.check_output(
            [
                "git", "-c", "user.name=test", "-c", "user.email=test@example.com",
                "commit-tree", tree, "-p", self.base,
            ],
            cwd=self.root,
            input="sibling candidate\n",
            text=True,
        ).strip()
        self.assertFalse(
            self.engine._has_candidate_binding(
                self.release_id, "feat/v0.3.8-fixture", self.base, sibling
            )
        )

    def test_rejects_equal_base_and_candidate(self):
        qa = self.release / "QA_SIGNOFF.md"
        qa.write_text(
            qa.read_text(encoding="utf-8").replace(f"Base-SHA: {self.base}", f"Base-SHA: {self.candidate}"),
            encoding="utf-8",
        )
        self.assertIn("candidate_not_bound_to_current_branch_base", self._unmet())

    def test_placeholder_matcher_rejects_markers_without_rejecting_policy_prose(self):
        self.assertTrue(HarnessEngine._contains_placeholder("- **Status**: Draft"))
        self.assertTrue(HarnessEngine._contains_placeholder("TODO: complete review"))
        self.assertTrue(HarnessEngine._contains_placeholder("This is a placeholder document."))
        self.assertFalse(HarnessEngine._contains_placeholder("placeholder detection is fail-closed."))


class TestSelfGovernanceValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.temp_dir, ignore_errors=True))
        for name in ("FLOW_SPEC.md", "GATES_AND_LOOPS.md", "CHANGELOG.md"):
            for parent in (self.temp_dir / "docs/spec", self.temp_dir / "src/forgeflow/templates/spec"):
                parent.mkdir(parents=True, exist_ok=True)
                (parent / name).write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "checkout", "-qb", "feat/r1"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "base"], cwd=self.temp_dir, check=True)
        self.base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.temp_dir, text=True).strip()

    def _commit_change(self, coverage=True, extra_rows=""):
        release = self.temp_dir / "docs/releases/r1"
        release.mkdir(parents=True)
        metadata = f"- **Base commit**: `{self.base}`\n- **Task branch**: `feat/r1`\n"
        (release / "PRD.md").write_text(metadata, encoding="utf-8")
        table = "\n".join((
            "| `src/forgeflow/x.py` | code | `docs/spec/FLOW_SPEC.md` | rule |",
            "| `docs/spec/FLOW_SPEC.md` | spec | `docs/spec/FLOW_SPEC.md` | rule |",
            "| `src/forgeflow/templates/spec/FLOW_SPEC.md` | package spec | `docs/spec/FLOW_SPEC.md` | parity |",
        )) + extra_rows if coverage else ""
        (release / "DESIGN.md").write_text(metadata + "## Self-Governance Spec Coverage\n| Changed path | Change classification | Canonical spec path | Coverage rationale |\n|---|---|---|---|\n" + table, encoding="utf-8")
        path = self.temp_dir / "src/forgeflow/x.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x = 1\n", encoding="utf-8")
        for parent in (self.temp_dir / "docs/spec", self.temp_dir / "src/forgeflow/templates/spec"):
            (parent / "FLOW_SPEC.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "change"], cwd=self.temp_dir, check=True)

    def test_self_governance_valid_coverage(self):
        self._commit_change()
        passed, _ = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertTrue(passed)

    def test_self_governance_rejects_missing_coverage(self):
        self._commit_change(coverage=False)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("missing", messages[0])

    def test_self_governance_rejects_duplicate_coverage_row(self):
        self._commit_change(extra_rows="\n| `src/forgeflow/x.py` | duplicate | `docs/spec/FLOW_SPEC.md` | duplicate |")
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("duplicates", messages[0])

    def test_self_governance_rejects_unknown_coverage_row(self):
        self._commit_change(extra_rows="\n| `tests/not_changed.py` | test | `docs/spec/FLOW_SPEC.md` | unknown |")
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("unknown_rows", messages[0])

    def test_self_governance_rejects_unknown_changed_path(self):
        self._commit_change()
        (self.temp_dir / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")
        subprocess.run(["git", "add", "unexpected.txt"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "unknown"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("unknown changed paths", messages[0])

    def test_self_governance_rejects_dirty_worktree(self):
        self._commit_change()
        (self.temp_dir / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("worktree must be clean", messages[0])

    def test_self_governance_rejects_head_as_base(self):
        self._commit_change()
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.temp_dir, text=True).strip()
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", head)
        self.assertFalse(passed)
        self.assertIn("strict ancestor", messages[0])

    def test_self_governance_rejects_wrong_structured_binding(self):
        self._commit_change()
        prd = self.temp_dir / "docs/releases/r1/PRD.md"
        prd.write_text(prd.read_text(encoding="utf-8").replace("feat/r1", "fix/r1"), encoding="utf-8")
        subprocess.run(["git", "add", str(prd.relative_to(self.temp_dir))], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "wrong binding"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("Task branch", messages[0])

    def test_self_governance_rejects_non_allowlisted_branch(self):
        self._commit_change()
        subprocess.run(["git", "branch", "-m", "custom/r1"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("allowlisted", messages[0])

    def test_self_governance_rejects_shallow_repository(self):
        self._commit_change()
        clone_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(clone_dir, ignore_errors=True))
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{self.temp_dir}", str(clone_dir)], check=True)
        self.assertEqual(
            subprocess.check_output(["git", "rev-parse", "--is-shallow-repository"], cwd=clone_dir, text=True).strip(),
            "true",
        )
        passed, messages = SelfGovernanceValidator.validate(clone_dir, "r1", self.base)
        self.assertFalse(passed)
        self.assertIn("shallow", messages[0])

    def _commit_versioned_release(
        self, target="0.1.1", evidence_target="0.1.1", release_id="v0.1.1-version",
        previous="0.1.0", bump="patch", legacy_base=False, legacy_source=None,
    ):
        subprocess.run(["git", "branch", "-m", f"feat/{release_id}"], cwd=self.temp_dir, check=True)
        version_path = self.temp_dir / "src/forgeflow/_version.py"
        version_path.parent.mkdir(parents=True, exist_ok=True)
        if legacy_base:
            (self.temp_dir / "src/forgeflow/__init__.py").write_text(
                legacy_source or f'__version__ = "{previous}"\n', encoding="utf-8"
            )
        else:
            version_path.write_text(f'__version__ = "{previous}"\n', encoding="utf-8")
        (self.temp_dir / "pyproject.toml").write_text(
            '[project]\ndynamic = ["version"]\n\n[tool.setuptools.dynamic]\n'
            'version = {attr = "forgeflow._version.__version__"}\n', encoding="utf-8"
        )
        templates_dir = self.temp_dir / "src/forgeflow/templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        for name in ("PRD.md", "DESIGN.md", "RELEASE_NOTES.md"):
            (templates_dir / name).write_text("template\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "version base"], cwd=self.temp_dir, check=True)
        base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.temp_dir, text=True).strip()
        version_path.write_text(f'__version__ = "{target}"\n', encoding="utf-8")
        release = self.temp_dir / "docs/releases" / release_id
        release.mkdir(parents=True)
        metadata = (
            f"- **Base commit**: `{base}`\n"
            f"- **Task branch**: `feat/{release_id}`\n"
            f"- **Previous ForgeFlow version**: `{previous}`\n"
            f"- **Target ForgeFlow version**: `{evidence_target}`\n"
            f"- **Version bump type**: `{bump}`\n"
            "- **Version change reason**: `test`\n"
        )
        (release / "PRD.md").write_text(metadata, encoding="utf-8")
        table = "\n".join((
            "| `src/forgeflow/_version.py` | code | `docs/spec/FLOW_SPEC.md` | version |",
            "| `docs/spec/FLOW_SPEC.md` | spec | `docs/spec/FLOW_SPEC.md` | rule |",
            "| `src/forgeflow/templates/spec/FLOW_SPEC.md` | package spec | `docs/spec/FLOW_SPEC.md` | parity |",
        ))
        (release / "DESIGN.md").write_text(
            metadata + "## Self-Governance Spec Coverage\n"
            "| Changed path | Change classification | Canonical spec path | Coverage rationale |\n"
            "|---|---|---|---|\n" + table,
            encoding="utf-8",
        )
        for parent in (self.temp_dir / "docs/spec", self.temp_dir / "src/forgeflow/templates/spec"):
            (parent / "FLOW_SPEC.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "version change"], cwd=self.temp_dir, check=True)
        return release_id, base

    def test_self_governance_validates_versioned_release_binding(self):
        release_id, base = self._commit_versioned_release()
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertTrue(passed, messages)

    def test_self_governance_rejects_mismatched_target_version(self):
        release_id, base = self._commit_versioned_release(evidence_target="0.1.2")
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("Target ForgeFlow version", messages[0])

    def test_self_governance_rejects_missing_version_field_and_release_prefix(self):
        release_id, base = self._commit_versioned_release()
        prd = self.temp_dir / "docs/releases" / release_id / "PRD.md"
        prd.write_text(
            prd.read_text(encoding="utf-8").replace("- **Version change reason**: `test`\n", ""),
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(prd.relative_to(self.temp_dir))], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "missing version field"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("Version change reason", messages[0])

    def test_self_governance_rejects_non_bump(self):
        release_id, base = self._commit_versioned_release(target="0.1.0", evidence_target="0.1.0", release_id="v0.1.0-version")
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("Version bump type", messages[0])

    def test_self_governance_rejects_release_prefix(self):
        release_id, base = self._commit_versioned_release(release_id="v0.1.1x-version")
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("release ID", messages[0])

    def test_self_governance_rejects_dynamic_metadata_mismatch_and_symlink_source(self):
        release_id, base = self._commit_versioned_release()
        pyproject = self.temp_dir / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "0.1.1"\n', encoding="utf-8")
        subprocess.run(["git", "add", "pyproject.toml"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "bad metadata"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("pyproject.toml", messages[0])


    def test_self_governance_rejects_symlink_version_source(self):
        release_id, base = self._commit_versioned_release()
        version = self.temp_dir / "src/forgeflow/_version.py"
        outside_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(outside_dir, ignore_errors=True))
        outside = outside_dir / "outside-version.py"
        outside.write_text('__version__ = "9.9.9"\n', encoding="utf-8")
        version.unlink()
        version.symlink_to(outside)
        subprocess.run(["git", "add", "src/forgeflow/_version.py"], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "symlink source"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("regular file", messages[0])

    def test_self_governance_accepts_exact_legacy_migration_fallback(self):
        release_id, base = self._commit_versioned_release(
            target="0.4.4", evidence_target="0.4.4",
            release_id=SelfGovernanceValidator.VERSION_RELEASE_ID,
            previous="0.2.0", bump="minor", legacy_base=True,
        )
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertTrue(passed, messages)

    def test_self_governance_rejects_legacy_fallback_outside_exact_migration(self):
        release_id, base = self._commit_versioned_release(
            target="0.4.4", evidence_target="0.4.4", release_id="v0.4.4-other",
            previous="0.2.0", bump="minor", legacy_base=True,
        )
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("legacy base version fallback", messages[0])

    def test_self_governance_rejects_malformed_legacy_version_source(self):
        release_id, base = self._commit_versioned_release(
            target="0.4.4", evidence_target="0.4.4",
            release_id=SelfGovernanceValidator.VERSION_RELEASE_ID,
            previous="0.2.0", bump="minor", legacy_base=True,
            legacy_source='__version__ = version_from_network()\n',
        )
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, release_id, base)
        self.assertFalse(passed)
        self.assertIn("string literal", messages[0])

    def test_version_literal_parser_rejects_duplicate_and_leading_zero_values(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            SelfGovernanceValidator._parse_version_literal(
                '__version__ = "0.1.0"\n__version__ = "0.1.1"\n', "version.py"
            )
        with self.assertRaisesRegex(ValueError, "without leading zeroes"):
            SelfGovernanceValidator._parse_version_literal('__version__ = "01.1.0"\n', "version.py")

    def _seed_core_path(self, path: str) -> str:
        target = self.temp_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old = True\n", encoding="utf-8")
        subprocess.run(["git", "add", path], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "seed core path"], cwd=self.temp_dir, check=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.temp_dir, text=True).strip()

    def _commit_name_status_change(self, old_path: str, new_path=None):
        base = self._seed_core_path(old_path)
        release = self.temp_dir / "docs/releases/r1"
        release.mkdir(parents=True)
        metadata = f"- **Base commit**: `{base}`\n- **Task branch**: `feat/r1`\n"
        (release / "PRD.md").write_text(metadata, encoding="utf-8")
        changed_paths = [old_path]
        if new_path:
            changed_paths.append(new_path)
        table = "\n".join(
            [f"| `{path}` | code | `docs/spec/FLOW_SPEC.md` | name-status |" for path in changed_paths]
            + [
                "| `docs/spec/FLOW_SPEC.md` | spec | `docs/spec/FLOW_SPEC.md` | rule |",
                "| `src/forgeflow/templates/spec/FLOW_SPEC.md` | package spec | `docs/spec/FLOW_SPEC.md` | parity |",
            ]
        )
        (release / "DESIGN.md").write_text(
            metadata + "## Self-Governance Spec Coverage\n"
            "| Changed path | Change classification | Canonical spec path | Coverage rationale |\n"
            "|---|---|---|---|\n" + table,
            encoding="utf-8",
        )
        if new_path:
            destination = self.temp_dir / new_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "mv", old_path, new_path], cwd=self.temp_dir, check=True)
        else:
            subprocess.run(["git", "rm", "-q", old_path], cwd=self.temp_dir, check=True)
        for parent in (self.temp_dir / "docs/spec", self.temp_dir / "src/forgeflow/templates/spec"):
            (parent / "FLOW_SPEC.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "name status"], cwd=self.temp_dir, check=True)
        return base

    def test_self_governance_requires_both_rename_paths(self):
        base = self._commit_name_status_change("src/forgeflow/old.py", "src/forgeflow/new.py")
        design = self.temp_dir / "docs/releases/r1/DESIGN.md"
        design.write_text(design.read_text(encoding="utf-8").replace("| `src/forgeflow/old.py` | code | `docs/spec/FLOW_SPEC.md` | name-status |\n", ""), encoding="utf-8")
        subprocess.run(["git", "add", str(design.relative_to(self.temp_dir))], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "remove rename old coverage"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", base)
        self.assertFalse(passed)
        self.assertIn("src/forgeflow/old.py", messages[0])

    def test_self_governance_requires_deleted_path_coverage(self):
        base = self._commit_name_status_change("src/forgeflow/deleted.py")
        design = self.temp_dir / "docs/releases/r1/DESIGN.md"
        design.write_text(design.read_text(encoding="utf-8").replace("| `src/forgeflow/deleted.py` | code | `docs/spec/FLOW_SPEC.md` | name-status |\n", ""), encoding="utf-8")
        subprocess.run(["git", "add", str(design.relative_to(self.temp_dir))], cwd=self.temp_dir, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", "remove deletion coverage"], cwd=self.temp_dir, check=True)
        passed, messages = SelfGovernanceValidator.validate(self.temp_dir, "r1", base)
        self.assertFalse(passed)
        self.assertIn("src/forgeflow/deleted.py", messages[0])


if __name__ == "__main__":
    unittest.main()
