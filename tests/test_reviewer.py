#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from forgeflow.renderer import ReportRenderer
from forgeflow.review_scanner import ReviewScanner
from forgeflow.reviewer import ReviewEngine, ReviewResult
from forgeflow.smell_detector import CodeSmell, SmellDetector


class TestSmellDetector(unittest.TestCase):
    def test_clean_code_has_no_critical_smells(self):
        clean_code = "def calculate_total(price: float, tax_rate: float) -> float:\n    return price * (1.0 + tax_rate)\n"
        smells = SmellDetector.analyze_code(clean_code)
        critical = [s for s in smells if s.severity == "CRITICAL"]
        self.assertEqual(len(critical), 0)

    def test_bare_except_detection(self):
        bad_code = "def unsafe_operation():\n    try:\n        do_something()\n    except:\n        pass\n"
        smells = SmellDetector.analyze_code(bad_code)
        critical = [s for s in smells if s.severity == "CRITICAL" and s.smell_type == "Bare Except"]
        self.assertEqual(len(critical), 1)

    def test_base_exception_detection(self):
        bad_code = "def catch_all():\n    try:\n        pass\n    except BaseException:\n        pass\n"
        smells = SmellDetector.analyze_code(bad_code)
        critical = [s for s in smells if s.severity == "CRITICAL" and s.smell_type == "Bare Except"]
        self.assertEqual(len(critical), 1)

    def test_too_many_parameters_detection(self):
        code = "def many_args(a: int, b: int, c: int, d: int, e: int, f: int) -> int:\n    return a + b + c + d + e + f\n"
        smells = SmellDetector.analyze_code(code)
        warnings = [s for s in smells if s.smell_type == "Too Many Parameters"]
        self.assertEqual(len(warnings), 1)

    def test_deep_nesting_detection(self):
        code = "def nested(x: int) -> int:\n    if x > 0:\n        if x > 1:\n            if x > 2:\n                if x > 3:\n                    return x\n    return 0\n"
        smells = SmellDetector.analyze_code(code)
        nesting = [s for s in smells if s.smell_type == "Deep Nesting"]
        self.assertEqual(len(nesting), 1)

    def test_long_function_detection(self):
        lines = ["def long_func() -> None:"]
        for i in range(60):
            lines.append(f"    x_{i} = {i}")
        code = "\n".join(lines)
        smells = SmellDetector.analyze_code(code)
        long_funcs = [s for s in smells if s.smell_type == "Long Function"]
        self.assertEqual(len(long_funcs), 1)

    def test_missing_type_annotations(self):
        code = "def untyped_func(foo, bar):\n    return foo + bar\n"
        smells = SmellDetector.analyze_code(code)
        types = [s for s in smells if s.smell_type == "Missing Type Annotations"]
        self.assertEqual(len(types), 1)

    def test_top_level_side_effect_detection(self):
        bad_code = "import logging\nimport sqlite3\nlogging.basicConfig(level=logging.INFO)\nconn = sqlite3.connect('test.db')\n"
        smells = SmellDetector.analyze_code(bad_code)
        side_effects = [s for s in smells if s.smell_type == "Top-level Side-Effect"]
        self.assertEqual(len(side_effects), 2)
        self.assertEqual(side_effects[0].severity, "CRITICAL")

    def test_unmanaged_resource_detection(self):
        bad_code = "def read_file(path: str) -> str:\n    f = open(path)\n    return f.read()\n"
        smells = SmellDetector.analyze_code(bad_code)
        unmanaged = [s for s in smells if s.smell_type == "Unmanaged Resource"]
        self.assertEqual(len(unmanaged), 1)

    def test_main_block_and_with_context_allowed(self):
        good_code = "def read_file_safe(path: str) -> str:\n    with open(path) as f:\n        return f.read()\n\nif __name__ == '__main__':\n    import sqlite3\n    conn = sqlite3.connect('main.db')\n"
        smells = SmellDetector.analyze_code(good_code)
        critical_or_unmanaged = [s for s in smells if s.smell_type in ("Top-level Side-Effect", "Unmanaged Resource")]
        self.assertEqual(len(critical_or_unmanaged), 0)


class TestReviewScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "sample.py").write_text("print('hello')\n")
        (self.root / "PRD.md").write_text("# PRD\nREQ-F01: Sample\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_all_source_files(self):
        files = ReviewScanner.get_all_source_files(self.root)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "sample.py")

    def test_find_spec_source(self):
        spec = ReviewScanner.find_spec_source(self.root)
        self.assertIsNotNone(spec)
        self.assertEqual(spec.name, "PRD.md")


class TestReviewEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "good.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
        (self.root / "src" / "bad.py").write_text("def bad():\n    try:\n        pass\n    except:\n        pass\n")
        (self.root / "PRD.md").write_text("# PRD\nREQ-F01: Review\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_review_detects_bad_code(self):
        engine = ReviewEngine(repo_root=self.root)
        res = engine.run_review(all_files=True)
        self.assertFalse(res.passed)
        self.assertTrue(any(s.severity == "CRITICAL" for s in res.smells))

    def test_run_review_good_code_only(self):
        engine = ReviewEngine(repo_root=self.root)
        good_file = self.root / "src" / "good.py"
        res = engine.run_review(targets=[good_file], strict=False)
        self.assertTrue(res.passed)
        self.assertIsNotNone(res.report_path)

    def test_render_terminal_and_json(self):
        engine = ReviewEngine(repo_root=self.root)
        res = engine.run_review(all_files=True)
        terminal_out = ReportRenderer.render_terminal_review(res)
        json_out = ReportRenderer.render_json_review(res)
        self.assertIn("Code Review & Architecture Audit Report", terminal_out)
        parsed = json.loads(json_out)
        self.assertEqual(parsed["summary"]["total_files"], 2)

    def test_render_terminal_includes_refactoring_guidance(self):
        engine = ReviewEngine(repo_root=self.root)
        nested_file = self.root / "src" / "nested.py"
        nested_file.write_text("def nested(x):\n    if x > 0:\n        if x > 1:\n            if x > 2:\n                if x > 3:\n                    return x\n    return 0\n")
        res = engine.run_review(targets=[nested_file], strict=False)
        terminal_out = ReportRenderer.render_terminal_review(res)
        self.assertIn("Deep Module & Clean Code 리팩토링 권장 사항", terminal_out)
    def test_run_review_clean_tree_bailout(self):
        engine = ReviewEngine(repo_root=self.root)
        from unittest.mock import patch
        with patch.object(ReviewScanner, "get_diff_files", return_value=[]):
            res = engine.run_review(all_files=False)
            self.assertTrue(res.passed)
            self.assertEqual(res.smells, [])
            self.assertEqual(res.files_scanned, [])

    def test_security_vulnerability_causes_review_failure(self):
        engine = ReviewEngine(repo_root=self.root)
        sec_file = self.root / "src" / "vuln.py"
        sec_file.write_text("import subprocess\nsubprocess.run('echo hi', shell=True)\n", encoding="utf-8")
        res = engine.run_review(targets=[sec_file], strict=False)
        self.assertFalse(res.passed)
        self.assertTrue(any(s.smell_type == "Security Vulnerability" for s in res.smells))

    def test_fail_on_warning_causes_review_failure(self):
        engine = ReviewEngine(repo_root=self.root)
        warn_file = self.root / "src" / "warn.py"
        warn_file.write_text("def silent():\n    try:\n        pass\n    except ValueError:\n        pass\n", encoding="utf-8")
        # normal review without strict or fail_on_warning should pass
        res_normal = engine.run_review(targets=[warn_file], strict=False, fail_on_warning=False)
        self.assertTrue(res_normal.passed)

        # with fail_on_warning
        res_fail = engine.run_review(targets=[warn_file], fail_on_warning=True)
        self.assertEqual(res_fail.passed, False)


class TestBaselineAwareReview(unittest.TestCase):
    def setUp(self):
        import subprocess
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        subprocess.run(["git", "init"], cwd=str(self.root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(self.root), check=True)
        subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=str(self.root), check=True)
        (self.root / "src").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _commit(self, msg: str):
        import subprocess
        subprocess.run(["git", "add", "."], cwd=str(self.root), check=True)
        subprocess.run(["git", "commit", "-m", msg], cwd=str(self.root), check=True)

    def test_invalid_git_baseline_ref_raises_value_error(self):
        engine = ReviewEngine(repo_root=self.root)
        target = self.root / "src" / "test.py"
        target.write_text("x = 1\n", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            engine.run_review(targets=[target], findings_baseline="non-existent-ref-12345")
        self.assertIn("Invalid or non-existent git baseline reference", str(ctx.exception))

    def test_strict_without_baseline_fails_on_any_warning(self):
        target = self.root / "src" / "warn.py"
        target.write_text("def silent():\n    try:\n        pass\n    except ValueError:\n        pass\n", encoding="utf-8")
        self._commit("add warning file")
        engine = ReviewEngine(repo_root=self.root)

        res_strict = engine.run_review(targets=[target], strict=True)
        self.assertFalse(res_strict.passed, "Strict without baseline must fail on any warning")

    def test_baseline_aware_clean_baseline_fails_on_new_warning(self):
        target = self.root / "src" / "calc.py"
        target.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
        self._commit("base clean commit")

        # In candidate, introduce a warning (empty except)
        target.write_text("def add(a: int, b: int) -> int:\n    try:\n        return a + b\n    except ValueError:\n        pass\n", encoding="utf-8")
        engine = ReviewEngine(repo_root=self.root)

        res = engine.run_review(targets=[target], strict=True, findings_baseline="HEAD")
        self.assertFalse(res.passed, "Candidate adding a new warning over clean baseline must fail")
        self.assertIsNotNone(res.baseline_stats)
        self.assertEqual(res.baseline_stats["new_warnings"], 1)

    def test_baseline_aware_unchanged_existing_warning_passes(self):
        target = self.root / "src" / "service.py"
        target.write_text(
            "def existing_warn():\n    try:\n        pass\n    except ValueError:\n        pass\n\n"
            "def clean_func():\n    return 42\n",
            encoding="utf-8"
        )
        self._commit("base commit with existing warning")

        # In candidate, modify ONLY clean_func, leaving existing_warn unchanged
        target.write_text(
            "def existing_warn():\n    try:\n        pass\n    except ValueError:\n        pass\n\n"
            "def clean_func():\n    # modified comment\n    return 100\n",
            encoding="utf-8"
        )
        engine = ReviewEngine(repo_root=self.root)

        res = engine.run_review(targets=[target], strict=True, findings_baseline="HEAD")
        self.assertTrue(res.passed, "Existing warning in untouched function must be exempt and pass")
        self.assertEqual(res.baseline_stats["baseline_warnings"], 1)
        self.assertEqual(res.baseline_stats["new_warnings"], 0)
        self.assertEqual(res.baseline_stats["modified_scope_warnings"], 0)
        self.assertEqual(res.baseline_stats["exempt_warnings"], 1)
        # Verify that warning is still presented in smells
        warnings = [s for s in res.smells if s.severity == "WARNING"]
        self.assertEqual(len(warnings), 1)

    def test_baseline_aware_modified_function_with_non_increasing_warning_passes(self):
        target = self.root / "src" / "service.py"
        target.write_text(
            "def warned_func():\n    try:\n        pass\n    except ValueError:\n        pass\n",
            encoding="utf-8"
        )
        self._commit("base commit")

        # In candidate, modify warned_func with a comment or bugfix, keeping existing warning non-increasing
        target.write_text(
            "def warned_func():\n    # minor fix or comment inside warned function\n    try:\n        pass\n    except ValueError:\n        pass\n",
            encoding="utf-8"
        )
        engine = ReviewEngine(repo_root=self.root)

        res = engine.run_review(targets=[target], strict=True, findings_baseline="HEAD")
        self.assertTrue(res.passed, "Existing warning in modified function must not block Gate 2 if no new warnings are added")
        self.assertEqual(res.baseline_stats["modified_scope_warnings"], 1)
        self.assertEqual(res.baseline_stats["new_warnings"], 0)
        self.assertEqual(res.baseline_stats["exempt_warnings"], 0)

    def test_baseline_aware_modified_function_with_new_warning_fails(self):
        target = self.root / "src" / "service.py"
        target.write_text(
            "def warned_func():\n    try:\n        pass\n    except ValueError:\n        pass\n",
            encoding="utf-8"
        )
        self._commit("base commit")

        # In candidate, modify warned_func AND introduce a NEW warning (e.g. another silent except)
        target.write_text(
            "def warned_func():\n    try:\n        pass\n    except ValueError:\n        pass\n    try:\n        pass\n    except KeyError:\n        pass\n",
            encoding="utf-8"
        )
        engine = ReviewEngine(repo_root=self.root)

        res = engine.run_review(targets=[target], strict=True, findings_baseline="HEAD")
        self.assertFalse(res.passed, "Adding a NEW warning inside modified function must fail strict gate")
        self.assertGreaterEqual(res.baseline_stats["new_warnings"], 1)

    def test_baseline_aware_line_shift_does_not_duplicate_warning(self):
        target = self.root / "src" / "shifted.py"
        target.write_text(
            "def warned_func():\n    try:\n        pass\n    except ValueError:\n        pass\n",
            encoding="utf-8"
        )
        self._commit("base commit")

        # In candidate, prepend 10 lines of comments at the very top (shifting line numbers)
        comments = "\n".join(f"# comment line {i}" for i in range(10))
        target.write_text(
            f"{comments}\n\ndef warned_func():\n    try:\n        pass\n    except ValueError:\n        pass\n",
            encoding="utf-8"
        )
        engine = ReviewEngine(repo_root=self.root)

        # Notice: diff is outside warned_func body lines (lines 1-10 are modified, warned_func is at lines 12+)
        # warned_func scope itself was not touched
        res = engine.run_review(targets=[target], strict=True, findings_baseline="HEAD")
        self.assertTrue(res.passed, "Line shifting outside function must not treat existing warning as new")
        self.assertEqual(res.baseline_stats["new_warnings"], 0)
        self.assertEqual(res.baseline_stats["exempt_warnings"], 1)

    def test_baseline_aware_resolved_warning_reported(self):
        target = self.root / "src" / "fix.py"
        target.write_text("def fixed():\n    try:\n        pass\n    except ValueError:\n        pass\n", encoding="utf-8")
        self._commit("base with warning")

        # In candidate, resolve the warning
        target.write_text("def fixed():\n    pass\n", encoding="utf-8")
        engine = ReviewEngine(repo_root=self.root)

        res = engine.run_review(targets=[target], strict=True, findings_baseline="HEAD")
        self.assertTrue(res.passed)
        self.assertEqual(res.baseline_stats["resolved_warnings"], 1)
        self.assertEqual(res.baseline_stats["baseline_warnings"], 1)
        self.assertEqual(res.baseline_stats["new_warnings"], 0)


if __name__ == "__main__":
    unittest.main()